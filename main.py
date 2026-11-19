"""Desktop Island native Windows overlay (Qt WebEngine + transparent desktop surface)."""
from __future__ import annotations
import ctypes
import ctypes.wintypes
import json
import os
import sys
import threading
import urllib.parse
import urllib.request
from pathlib import Path

if getattr(sys, "frozen", False):
    # Keep the frozen Qt runtime ahead of any Qt DLLs installed by other desktop apps.
    _frozen_root = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parent))
    _qt_dll_dirs = [_frozen_root / "PySide6", _frozen_root / "shiboken6"]
    for _dll_dir in _qt_dll_dirs:
        if _dll_dir.is_dir():
            os.add_dll_directory(str(_dll_dir))
            os.environ["PATH"] = str(_dll_dir) + os.pathsep + os.environ.get("PATH", "")

import psutil
from PySide6.QtCore import QObject, QPoint, QRunnable, QThreadPool, QTimer, Qt, Signal, Slot, QUrl
from PySide6.QtGui import QColor
from PySide6.QtWidgets import QApplication, QFileDialog, QVBoxLayout, QWidget
from PySide6.QtWebChannel import QWebChannel
from PySide6.QtWebEngineWidgets import QWebEngineView

from backend.media_smtc import WindowsMediaMonitor

BASE = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parent))
APP_DATA = Path(os.environ.get("LOCALAPPDATA", str(Path.home()))) / "DesktopIsland"
APP_DATA.mkdir(parents=True, exist_ok=True)
CONFIG_PATH = APP_DATA / "config.json"

class SearchWorker(QRunnable):
    def __init__(self, query: str, provider: str, config: dict, request_id: str, bridge):
        super().__init__(); self.query=query; self.provider=provider; self.config=config; self.request_id=request_id; self.bridge=bridge
    def run(self):
        result=self.bridge.search_music_impl(self.query,self.provider,self.config)
        self.bridge.searchFinished.emit(self.request_id,json.dumps(result,ensure_ascii=False))

class Bridge(QObject):
    searchFinished = Signal(str, str)
    def __init__(self, owner, media):
        super().__init__(owner); self.owner=owner; self.media=media; self.pool=QThreadPool.globalInstance()
        try: self.config=json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
        except Exception: self.config={"video_path":"","youtube_api_key":"","spotify_access_token":""}

    @Slot(result=str)
    def get_state(self):
        return json.dumps({"media":self.media.get_state(),"video_path":self.config.get("video_path",""),
            "connected":{"youtube":bool(self.config.get("youtube_api_key")),"spotify":bool(self.config.get("spotify_access_token"))}})
    @Slot(result=bool)
    def play_pause(self): return self.media.play_pause()
    @Slot(result=bool)
    def next_track(self): return self.media.next_track()
    @Slot(result=bool)
    def previous_track(self): return self.media.previous_track()
    @Slot(str, result=bool)
    def set_hit_regions(self, raw):
        try:
            rectangles=json.loads(raw)
            self.owner.hit_rects=[tuple(int(v) for v in r[:4]) for r in rectangles if len(r)>=4]
            return True
        except Exception: return False
    @Slot(result=str)
    def get_system_stats(self):
        m=psutil.virtual_memory()
        return json.dumps({"cpu_percent":psutil.cpu_percent(),"memory_percent":m.percent,
            "memory_used_gb":round(m.used/(1024**3),1),"memory_total_gb":round(m.total/(1024**3),1)})
    @Slot(str,str,result=str)
    def save_music_connections(self,youtube_key,spotify_token):
        self.config["youtube_api_key"]=(youtube_key or "").strip(); self.config["spotify_access_token"]=(spotify_token or "").strip()
        CONFIG_PATH.write_text(json.dumps(self.config,ensure_ascii=False,indent=2),encoding="utf-8")
        return json.dumps({"youtube":bool(self.config["youtube_api_key"]),"spotify":bool(self.config["spotify_access_token"])})
    @Slot(str,str,str)
    def search_music(self,query,provider,request_id):
        self.pool.start(SearchWorker(query,provider,dict(self.config),request_id,self))
    def search_music_impl(self,query,provider,config):
        query=(query or "").strip(); provider=(provider or "youtube").lower()
        if not query:return {"ok":False,"message":"Bir şarkı adı yaz."}
        if provider=="youtube":
            key=config.get("youtube_api_key","")
            if not key:return {"ok":False,"message":"YouTube araması için MUSIC CONNECTIONS bölümüne YouTube Data API anahtarını ekle."}
            params=urllib.parse.urlencode({"part":"snippet","type":"video","videoCategoryId":"10","maxResults":8,"q":query,"key":key})
            url="https://www.googleapis.com/youtube/v3/search?"+params
            try:
                with urllib.request.urlopen(url,timeout=12) as response: data=json.loads(response.read().decode("utf-8"))
                items=[{"id":x["id"]["videoId"],"title":x["snippet"]["title"],"artist":x["snippet"]["channelTitle"],"thumbnail":x["snippet"]["thumbnails"].get("medium",{}).get("url","")} for x in data.get("items",[]) if x.get("id",{}).get("videoId")]
                return {"ok":True,"provider":"youtube","items":items}
            except Exception as exc:return {"ok":False,"message":f"YouTube araması başarısız: {exc}"}
        if provider=="spotify":
            token=config.get("spotify_access_token","")
            if not token:return {"ok":False,"message":"Spotify araması için MUSIC CONNECTIONS bölümüne Spotify erişim tokenını ekle."}
            params=urllib.parse.urlencode({"q":query,"type":"track","limit":8})
            req=urllib.request.Request("https://api.spotify.com/v1/search?"+params,headers={"Authorization":"Bearer "+token})
            try:
                with urllib.request.urlopen(req,timeout=12) as response:data=json.loads(response.read().decode("utf-8"))
                items=[{"id":x["id"],"title":x["name"],"artist":", ".join(a["name"] for a in x["artists"]),"thumbnail":(x.get("album",{}).get("images") or [{"url":""}])[0]["url"]} for x in data.get("tracks",{}).get("items",[])]
                return {"ok":True,"provider":"spotify","items":items}
            except Exception as exc:return {"ok":False,"message":f"Spotify araması başarısız: {exc}"}
        return {"ok":False,"message":"Spotify veya YouTube seç."}
    @Slot(result=str)
    def choose_video(self):
        path,_=QFileDialog.getOpenFileName(self.owner,"Choose desktop video","","Video files (*.mp4 *.webm *.m4v *.mov);;All files (*.*)")
        if not path:return json.dumps({"ok":False,"cancelled":True})
        self.config["video_path"]=path;CONFIG_PATH.write_text(json.dumps(self.config,ensure_ascii=False,indent=2),encoding="utf-8")
        return json.dumps({"ok":True,"url":Path(path).as_uri(),"name":Path(path).name})
    @Slot(result=bool)
    def quit_app(self): self.owner.close();return True

class DesktopOverlay(QWidget):
    def __init__(self, media):
        super().__init__()
        self.setWindowTitle("Desktop Island")
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint|Qt.WindowType.WindowStaysOnTopHint|Qt.WindowType.Tool)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground,True)
        self.setAttribute(Qt.WidgetAttribute.WA_NoSystemBackground,True)
        self.hit_rects=[];self._passthrough=None
        geometry=QApplication.primaryScreen().virtualGeometry()
        self.setGeometry(geometry)
        layout=QVBoxLayout(self);layout.setContentsMargins(0,0,0,0);layout.setSpacing(0)
        self.view=QWebEngineView(self);self.view.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground,True)
        self.view.page().setBackgroundColor(QColor(0,0,0,0));layout.addWidget(self.view)
        channel=QWebChannel(self.view.page());self.bridge=Bridge(self,media);channel.registerObject("api",self.bridge);self.view.page().setWebChannel(channel)
        self.view.load(QUrl.fromLocalFile(str(BASE/"frontend"/"index.html")))
        self.foreground_timer=QTimer(self);self.foreground_timer.timeout.connect(self.sync_desktop_visibility);self.foreground_timer.start(300)
        self.hit_test_timer=QTimer(self);self.hit_test_timer.timeout.connect(self.sync_mouse_passthrough);self.hit_test_timer.start(20)
    def sync_mouse_passthrough(self):
        if sys.platform!="win32" or not self.isVisible():return
        point=ctypes.wintypes.POINT()
        if not ctypes.windll.user32.GetCursorPos(ctypes.byref(point)):return
        pos=self.mapFromGlobal(QPoint(point.x,point.y));x=pos.x();y=pos.y()
        interactive=any(left<=x<=right and top<=y<=bottom for left,top,right,bottom in self.hit_rects)
        if self._passthrough==interactive:return
        self._passthrough=interactive
        user32=ctypes.windll.user32;get_long=getattr(user32,"GetWindowLongPtrW",user32.GetWindowLongW);set_long=getattr(user32,"SetWindowLongPtrW",user32.SetWindowLongW)
        hwnd=int(self.winId());style=get_long(hwnd,-20)|0x00080000 # WS_EX_LAYERED
        if interactive:style &= ~0x00000020 # WS_EX_TRANSPARENT off over our controls
        else:style |= 0x00000020 # WS_EX_TRANSPARENT passes clicks through to desktop
        set_long(hwnd,-20,style)
        user32.SetWindowPos(hwnd,0,0,0,0,0,0x0001|0x0002|0x0004|0x0010|0x0020)
    def sync_desktop_visibility(self):
        if sys.platform!="win32":return
        user32=ctypes.windll.user32;foreground=user32.GetForegroundWindow();my=int(self.winId())
        buf=ctypes.create_unicode_buffer(128);user32.GetClassNameW(foreground,buf,len(buf));cls=buf.value
        owner=user32.GetWindow(foreground,4) # GW_OWNER
        foreground_is_app=int(foreground)==my or int(owner or 0)==my
        desktop=cls in {"Progman","WorkerW"}
        show=desktop or foreground_is_app
        if show and not self.isVisible():self.show();self.raise_()
        elif not show and self.isVisible():self.hide()

def main():
    if sys.platform=="win32":
        try:ctypes.windll.user32.SetProcessDpiAwarenessContext(ctypes.c_void_p(-4))
        except Exception:pass
    QApplication.setAttribute(Qt.ApplicationAttribute.AA_ShareOpenGLContexts)
    app=QApplication(sys.argv);app.setQuitOnLastWindowClosed(True)
    media=WindowsMediaMonitor();media.start()
    overlay=DesktopOverlay(media);overlay.show()
    try:status=app.exec()
    finally:media.stop()
    raise SystemExit(status)

if __name__=="__main__":
    if "--check-runtime" in sys.argv:
        raise SystemExit(0)
    main()
