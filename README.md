# Flask, MySQL ve Socket.IO Kullanarak Chat Uygulaması
Bu örnek, Flask web framework'ü, MySQL veritabanı ve Socket.IO kütüphanesi kullanılarak basit bir sohbet uygulaması oluşturmayı gösterir. 
Uygulama, kullanıcıların sohbet odasına katılabileceği ve birbirleriyle mesajlaşabileceği temel bir arayüz sunar.


## Gereksinimler

* Python 3.x
* Flask
* Flask-SocketIO
* MySQL veritabanı


## Kurulum

### Manuel Kurulum

1. Clone the repo
   ```sh
    git clone https://github.com/MKLKCDG/ChatApp
   ```
2. Build docker image
   ```sh
    docker build  .
   ```
3. Run container
   ```sh
    docker run 
   ```
4. Go to http://localhost:5000


## Ek Notlar

* Bu örnek sadece öğrenme amaçlıdır ve güvenlik açısından eksiklikler içerebilir. Gerçek bir uygulama geliştirirken güvenlik önlemlerini unutmayın.
* Flask uygulamalarınızı üretim ortamında çalıştırmadan önce güvenlik önlemlerini almak önemlidir.
* MySQL parola ve kullanıcı adınızı güvenli bir şekilde saklayın ve paylaşırken dikkatli olun.