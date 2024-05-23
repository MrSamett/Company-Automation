import sys  # Sistem modülünü içe aktar
import pymysql.cursors  # MySQL veritabanı bağlantısı için modülü içe aktar
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QPushButton, QLabel, QLineEdit, QTextEdit, QInputDialog  # PyQt5 bileşenlerini içe aktar
from PyQt5.QtCore import Qt  # PyQt5'in temel bileşenlerini içe aktar
from datetime import datetime  # datetime modülünü içe aktar
from pyzbar.pyzbar import decode  # QR kodu çözümleme için modülü içe aktar
import cv2  # OpenCV modülünü içe aktar
import random  # Rastgele sayılar üretmek için modülü içe aktar
import string  # Dize işlemleri için modülü içe aktar

# Koyu temayı tanımlayan CSS
dark_style = """
    * {
        background-color: #282828;  
        color: #ffffff; 
        font-family: Arial, sans-serif; 
    }
    
    QLabel {
        font-size: 18px; 
    }
    
    QPushButton {
        background-color: #484848; 
        border: 2px solid #ffffff; 
        border-radius: 8px; 
        padding: 8px 16px; 
        font-size: 16px;
    }
    
    QLineEdit {
        background-color: #333333;
        border: 2px solid #ffffff; 
        border-radius: 8px;  
        padding: 8px;  
        color: #ffffff; 
        font-size: 16px; 
    }
    
    QTextEdit {
        background-color: #333333;  
        border: 2px solid #ffffff;  
        border-radius: 8px; 
        padding: 8px;  
        color: #ffffff; 
        font-size: 16px;
    }
"""
# Ana Pencere 
class GirisCikisTakip(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        # Pencere ayarları
        self.setWindowTitle('SCY Denetliyicisi')
        self.setGeometry(100, 100, 600, 400)
        self.setStyleSheet(dark_style)  

        self.layout = QVBoxLayout() # Dikey düzen

        # Hoş geldiniz mesajı
        self.label = QLabel("<h1><b>Hoş Geldiniz!</b></h1>")
        self.label.setAlignment(Qt.AlignCenter) 
        self.layout.addWidget(self.label)

        # Giriş kodu için etiket ve giriş alanı
        self.label_giris_kodu = QLabel("Lütfen giriş yapmak için giriş kodunuzu girin")
        self.label_giris_kodu.setAlignment(Qt.AlignCenter) 
        self.layout.addWidget(self.label_giris_kodu)
        self.entry_code_input = QLineEdit()
        self.layout.addWidget(self.entry_code_input)

        # Giriş ve çıkış butonları
        self.btn_giris = QPushButton("Giriş Yap")
        self.btn_giris.clicked.connect(self.giris_yap)
        self.layout.addWidget(self.btn_giris)
        self.btn_cikis = QPushButton("Çıkış")
        self.btn_cikis.clicked.connect(self.close)
        self.layout.addWidget(self.btn_cikis)

        # QR kodu tarama butonu
        self.btn_qr_tara = QPushButton("QR Kodu Tara")
        self.btn_qr_tara.clicked.connect(self.qr_kod_tara)
        self.layout.addWidget(self.btn_qr_tara)

        self.setLayout(self.layout)

    def qr_kod_tara(self):
        cap = cv2.VideoCapture(0)  # Kamerayı aç

        while True:
            ret, frame = cap.read()  # Kameradan bir kare al
            if not ret:
                continue

            decoded_objects = decode(frame)  # Karedeki QR kodlarını tara

            for obj in decoded_objects:
                gecis_kodu = obj.data.decode('utf-8')  # QR kodunun içeriğini al
                self.giris_yap_qr(gecis_kodu)  # Giriş yap metodunu burada çağır
                # Kamera işlemini sonlandır
                cap.release()
                cv2.destroyAllWindows()
                return

            cv2.imshow('QR Kodu Tarayıcı', frame)  # Kameradan alınan kareyi göster
            if cv2.waitKey(1) & 0xFF == ord('q'):  # Q tuşuna basılınca döngüden çık
                break

        cap.release()
        cv2.destroyAllWindows()

        self.entry_code_input.clear()
        self.entry_code_input.setPlaceholderText("QR kodu tanınamadı! Manuel olarak girin.")

    def giris_yap_qr(self, gecis_kodu):
        try:
            self.giris_yap(is_qr=True, gecis_kodu=gecis_kodu)
        except Exception as e:
            print("Hata:", e)

    def giris_yap(self, is_qr=False, gecis_kodu=None):
        gecis_kodu = gecis_kodu if is_qr else self.entry_code_input.text()
        try:
            # Veritabanına bağlanma
            db = pymysql.connect(host='127.0.0.1', user='root', password='1003452', db='bitirme', charset='utf8mb4', cursorclass=pymysql.cursors.DictCursor)
            baglanti = db.cursor()
            # Yönetici tablosundan giriş kodunu kontrol etme
            baglanti.execute("SELECT * FROM yoneticiler WHERE giris_kodu = %s", (gecis_kodu,))
            yonetici = baglanti.fetchone()
            if yonetici:
                # Yönetici ise yönetici menüsünü aç
                self.admin_menu(yonetici)
            else:
                # Değilse çalışan tablosundan kontrol et
                baglanti.execute("SELECT * FROM calisanlar WHERE giris_kodu = %s", (gecis_kodu,))
                calisan = baglanti.fetchone()
                if calisan:
                    # Eğer çalışan varsa, çalışan menüsünü aç
                    self.calisan_menu(calisan)
                else:
                    # Yoksa hata mesajı ver
                    print("Giriş kodu yanlış!")
        except Exception as e:
            print("Hata:", e)

    # Çalışan menüsünü açan metod
    def calisan_menu(self, calisan):
        self.sub_window = CalisanMenuPenceresi(calisan)
        self.sub_window.show()
        self.close()


    # Yönetici menüsünü açan metod
    def admin_menu(self, yonetici):
        self.sub_window = YoneticiMenuPenceresi(yonetici)
        self.sub_window.show()
        self.close()

# Çalışan Menüsü 
class CalisanMenuPenceresi(QWidget):
    def __init__(self, calisan):
        super().__init__()
        self.calisan = calisan
        self.initUI()

    def initUI(self):
        # Pencere ayarları
        self.setWindowTitle('Çalışan Menüsü')
        self.setGeometry(300, 300, 400, 200)
        self.setStyleSheet(dark_style) 

        self.layout = QVBoxLayout() # Dikey düzen

        # Kullanıcı adına özel hoş geldiniz mesajı
        self.label = QLabel(f"{self.calisan['ad']} {self.calisan['soyad']} Hoş Geldin!")
        self.layout.addWidget(self.label)

        # Giriş ve çıkış butonları
        self.btn_giris = QPushButton("Giriş Yap")
        self.btn_giris.clicked.connect(self.giris_yap)
        self.layout.addWidget(self.btn_giris)
        self.btn_cikis = QPushButton("Çıkış Yap")
        self.btn_cikis.clicked.connect(self.cikis_yap)
        self.layout.addWidget(self.btn_cikis)

        # Ana menü butonu
        self.btn_ana_menu = QPushButton("Ana Menüye Dön")
        self.btn_ana_menu.clicked.connect(self.ana_menu)
        self.layout.addWidget(self.btn_ana_menu)

        self.setLayout(self.layout)

     # Giriş işlemini gerçekleştiren metod
    def giris_yap(self):
        try:
            db = pymysql.connect(host='127.0.0.1', user='root', password='1003452', db='bitirme', charset='utf8mb4', cursorclass=pymysql.cursors.DictCursor)
            baglanti = db.cursor()
            baglanti.execute("UPDATE calisanlar SET giris_saati = %s WHERE id = %s", (datetime.now(), self.calisan['id']))
            db.commit()
            print("Giriş başarıyla kaydedildi.")
        except Exception as e:
            print("Hata:", e)
            db.rollback()
       
    # Çıkış işlemini gerçekleştiren metod
    def cikis_yap(self):
        try:
            db = pymysql.connect(host='127.0.0.1', user='root', password='1003452', db='bitirme', charset='utf8mb4', cursorclass=pymysql.cursors.DictCursor)
            baglanti = db.cursor()
            baglanti.execute("UPDATE calisanlar SET cikis_saati = %s WHERE id = %s", (datetime.now(), self.calisan['id']))
            db.commit()
            print("Çıkış başarıyla kaydedildi.")
        except Exception as e:
            print("Hata:", e)
            db.rollback()

    # Ana menüye dönme metod
    def ana_menu(self):
        self.sub_window = GirisCikisTakip()
        self.sub_window.show()
        self.close()

# Yönetici Menüsü 
class YoneticiMenuPenceresi(QWidget):
    def __init__(self, yonetici):
        super().__init__()
        self.yonetici = yonetici
        self.initUI()

    def initUI(self):
        # Pencere ayarları
        self.setWindowTitle('Yönetici Menüsü')
        self.setGeometry(600, 600, 700, 500)
        self.setStyleSheet(dark_style) 

        self.layout = QVBoxLayout() # Dikey düzen

        self.label = QLabel(f"{self.yonetici['ad']} {self.yonetici['soyad']} Hoş Geldin!")
        self.layout.addWidget(self.label)

        # Terminal için metin alanı
        self.terminal = QTextEdit()
        self.terminal.setReadOnly(True) 
        self.layout.addWidget(self.terminal)
        

        # Çalışanları listeleme butonu
        self.btn_calisanlari_listele = QPushButton("Çalışanları Listele")
        self.btn_calisanlari_listele.clicked.connect(self.calisanlari_listele)
        self.layout.addWidget(self.btn_calisanlari_listele)

        # Giriş çıkış saatlerini listeleme butonu
        self.btn_gecis_cikis_saatleri = QPushButton("Giriş Çıkış Saatlerini Listele")
        self.btn_gecis_cikis_saatleri.clicked.connect(self.gecis_cikis_saatleri_goster)
        self.layout.addWidget(self.btn_gecis_cikis_saatleri)

        # Yeni çalışan ekleme butonu
        self.btn_yeni_calisan_ekle = QPushButton("Yeni Çalışan Ekle")
        self.btn_yeni_calisan_ekle.clicked.connect(self.yeni_calisan_ekle_ac)
        self.layout.addWidget(self.btn_yeni_calisan_ekle)

        # Çalışan silme butonu
        self.btn_calisan_sil = QPushButton("Çalışan Sil")
        self.btn_calisan_sil.clicked.connect(self.calisan_sil)
        self.layout.addWidget(self.btn_calisan_sil)

        # Ana menü butonu
        self.btn_ana_menu = QPushButton("Ana Menüye Dön")
        self.btn_ana_menu.clicked.connect(self.ana_menu)
        self.layout.addWidget(self.btn_ana_menu)

        self.setLayout(self.layout)

    def yeni_calisan_ekle_ac(self):
        self.sub_window = YeniCalisanEklePenceresi()
        self.sub_window.show()

    def calisan_sil(self):
        calisan_id, ok = QInputDialog.getInt(self, "Çalışan Sil", "Silinecek çalışanın ID'sini girin:")
        if ok:
            try:
                db = pymysql.connect(host='127.0.0.1', user='root', password='1003452', db='bitirme', charset='utf8mb4', cursorclass=pymysql.cursors.DictCursor)
                baglanti = db.cursor()
                baglanti.execute("DELETE FROM calisanlar WHERE id = %s", (calisan_id,))
                db.commit()
                print("Çalışan başarıyla silindi.")
            except Exception as e:
                print("Hata:", e)
                db.rollback()

    def calisanlari_listele(self):
        self.terminal.clear() 
        try:
            db = pymysql.connect(host='127.0.0.1', user='root', password='1003452', db='bitirme', charset='utf8mb4', cursorclass=pymysql.cursors.DictCursor)
            baglanti = db.cursor()
            baglanti.execute("SELECT * FROM calisanlar")
            calisanlar = baglanti.fetchall()
            for calisan in calisanlar:
                self.terminal.append(f"{calisan['id']} - {calisan['ad']} {calisan['soyad']}")
        except Exception as e:
            print("Hata:", e)

    def gecis_cikis_saatleri_goster(self):
        self.terminal.clear() 
        try:
            db = pymysql.connect(host='127.0.0.1', user='root', password='1003452', db='bitirme', charset='utf8mb4', cursorclass=pymysql.cursors.DictCursor)
            baglanti = db.cursor()
            baglanti.execute("SELECT * FROM calisanlar")
            calisanlar = baglanti.fetchall()
            for calisan in calisanlar:
                self.terminal.append(f"{calisan['id']} - {calisan['ad']} {calisan['soyad']} -> Giriş: {calisan['giris_saati']}, Çıkış: {calisan['cikis_saati']}")
        except Exception as e:
            print("Hata:", e)

    def ana_menu(self):
        self.sub_window = GirisCikisTakip()
        self.sub_window.show()
        self.close()

# Yeni Çalışan Ekleme Penceresi
class YeniCalisanEklePenceresi(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        # Pencere ayarları
        self.setWindowTitle('Yeni Çalışan Ekle')
        self.setGeometry(300, 300, 300, 200)
        self.setStyleSheet(dark_style) 

        self.layout = QVBoxLayout() # Dikey düzen

        # İsim etiketi ve giriş alanı
        self.label_ad = QLabel("Ad:")
        self.layout.addWidget(self.label_ad)
        self.entry_ad = QLineEdit()
        self.layout.addWidget(self.entry_ad)

        # Soyisim etiketi ve giriş alanı
        self.label_soyad = QLabel("Soyad:")
        self.layout.addWidget(self.label_soyad)
        self.entry_soyad = QLineEdit()
        self.layout.addWidget(self.entry_soyad)

        # Doğum tarihi etiketi ve giriş alanı
        self.label_dogum_tarihi = QLabel("Doğum Tarihi (YYYY-MM-DD):")
        self.layout.addWidget(self.label_dogum_tarihi)
        self.entry_dogum_tarihi = QLineEdit()
        self.layout.addWidget(self.entry_dogum_tarihi)

        # Çalışanı ekleme butonu
        self.btn_ekle = QPushButton("Ekle")
        self.btn_ekle.clicked.connect(self.ekle)
        self.layout.addWidget(self.btn_ekle)

        self.setLayout(self.layout)

    # Çalışan ekleme işlemini gerçekleştiren metod
    def ekle(self):
        ad = self.entry_ad.text()
        soyad = self.entry_soyad.text()
        dogum_tarihi = self.entry_dogum_tarihi.text()
        gecis_kodu = gecis_kodu_olustur(ad, soyad)
        try:
            # Veritabanına bağlanma
            db = pymysql.connect(host='127.0.0.1', user='root', password='1003452', db='bitirme', charset='utf8mb4', cursorclass=pymysql.cursors.DictCursor)
            baglanti = db.cursor()
            # Yeni çalışanı ekleme
            baglanti.execute("INSERT INTO calisanlar (ad, soyad, dogum_tarihi, giris_kodu, giris_saati, cikis_saati) VALUES (%s, %s, %s, %s, NULL, NULL)",
                             (ad, soyad, dogum_tarihi, gecis_kodu))
            db.commit()
            print("Yeni çalışan başarıyla eklendi.")
            print("Oluşturulan giriş kodu:", gecis_kodu)
        except Exception as e:
            print("Hata:", e)
            db.rollback()
        self.close()

# Geçiş kodu oluşturan fonksiyon
def gecis_kodu_olustur(ad, soyad):
    return ad[:2].upper() + soyad[:2].upper() + str(datetime.now().microsecond)[-2:]

# Ana uygulamayı başlat
if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = GirisCikisTakip()
    ex.show()
    sys.exit(app.exec_())
