# Desktop Island

Desktop Island is a transparent, frameless desktop overlay for Windows. It keeps your wallpaper visible while bringing music controls and practical widgets into one desktop panel.

See the [Privacy Policy](privacy-policy.html) for information about local data and the optional YouTube and Spotify connections.

Windows masaüstü için şeffaf, çerçevesiz bir Dynamic Island katmanı. Açık masaüstü duvar kâğıdını görünür bırakır; üstteki müzik paneli dışındaki fare tıklamaları masaüstüne geçer. Başka uygulamaya geçince katman gizlenir.

## Başlatma

- `dist_verified\DesktopIsland\DesktopIsland.exe` dosyasını aç. Bu Python 3.12 ile oluşturulan en güncel derlemedir; yanında bulunan `_internal` klasörü ve dosyaları aynı klasörde kalmalıdır.
- Kaynak koddan çalıştırmak için Python 3.11+ kurup `run.bat` dosyasına çift tıkla.
- Derleme için `build_app.bat` kullanılır.

## Şu an çalışanlar

- Windows medya oturumundan şarkı, sanatçı, kapak, süre bilgisini alma ve önceki/oynat/duraklat/sonraki kontrolleri.
- YouTube araması ve videoyu masaüstü arka planında oynatma.
- Spotify araması ve sonuçları uygulama içindeki Spotify gömülü oynatıcıda açma.
- Focus sayacı, yerel not, yerel takvim notları ve CPU/RAM kartı.
- İsteğe bağlı yerel video arka planı. Görsel varsayılan olarak sessizdir.

## Müzik arama bağlantıları

Paneli açıp **MUSIC CONNECTIONS** düğmesinden YouTube Data API anahtarı ve Spotify Web API erişim tokenı gir. Değerler yalnızca bu bilgisayardaki `%LOCALAPPDATA%\DesktopIsland\config.json` dosyasına kaydedilir. Spotify erişim tokenlarının süresi dolabilir; API tokenını yenileyip aynı alandan kaydetmen gerekir.

Uygulama şarkı arama isteği yaptığında sorgu ilgili sağlayıcıya HTTPS ile gönderilir. Arama anahtarları olmadan sağlayıcı kataloglarında arama yapılamaz.


## Microsoft Store packaging

The Partner Center product name has been reserved as **Desktop Island**. Its Store identity is defined in `packaging/AppxManifest.xml` and matches the Product identity page in Partner Center:

- Package name: `OrhanDoanKaplan.DesktopIsland`
- Publisher: `CN=1E6CC6C5-0729-46FA-9522-4ACC95C4B57B`
- Publisher display name: `Orhan Doğan Kaplan`

To prepare an x64 Store package, double-click `build_store_msix.bat`. It builds the app with the Python 3.12 environment and uses MakeAppx from the Windows SDK. The output is written to `artifacts/store/DesktopIsland_1.0.0.0_x64.msix`. If MakeAppx is missing, install the Windows 10/11 SDK with Appx Packaging Tools and run the batch file again.

The MSIX is only a submission package. It is not published until uploaded in the Desktop Island Partner Center draft and it passes Store certification. Microsoft signs MSIX packages distributed through the Store.
