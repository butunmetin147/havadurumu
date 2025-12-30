import requests
from PIL import Image, ImageDraw, ImageFont
from datetime import datetime, timedelta
import schedule, time
from instagrapi import Client
from githublogin import username, password

# ------------------------
# Türkiye Bölgeleri ve İller
# ------------------------
regions = {
    "Marmara Bölgesi": ["İstanbul","Edirne","Kırklareli","Tekirdağ","Kocaeli","Sakarya","Bursa","Balıkesir","Çanakkale","Yalova"],
    "Ege Bölgesi": ["İzmir","Aydın","Muğla","Manisa","Denizli","Uşak","Kütahya","Afyonkarahisar"],
    "Akdeniz Bölgesi": ["Antalya","Adana","Mersin","Hatay","Isparta","Kahramanmaraş","Osmaniye"],
    "Karadeniz Bölgesi": ["Trabzon","Rize","Samsun","Ordu","Giresun","Zonguldak","Bartın","Sinop"],
    "İç Anadolu Bölgesi": ["Ankara","Konya","Kayseri","Sivas","Yozgat","Kırıkkale","Kırşehir","Aksaray","Niğde","Nevşehir"],
    "Doğu Anadolu Bölgesi": ["Erzurum","Kars","Ağrı","Van","Malatya","Elazığ","Tunceli","Bingöl"],
    "Güneydoğu Anadolu Bölgesi": ["Diyarbakır","Şanlıurfa","Mardin","Batman","Siirt","Şırnak","Gaziantep"]
}

# ------------------------
# OpenWeatherMap API Key
# ------------------------
API_KEY = "51ec80ac4efd3d17205937399de50041"


# Global olarak
gun_adlari = ["Pazartesi", "Salı", "Çarşamba", "Perşembe", "Cuma", "Cumartesi", "Pazar"]



# ------------------------
# Şehre göre yarının hava durumu alma fonksiyonu
# ------------------------
def get_weather(city):
    url = f"http://api.openweathermap.org/data/2.5/forecast?q={city}&units=metric&lang=tr&appid={API_KEY}"
    try:
        r = requests.get(url, timeout=10)
        data = r.json()
        tomorrow = (datetime.now() + timedelta(days=1)).date()
        for item in data["list"]:
            dt = datetime.fromtimestamp(item["dt"]).date()
            if dt == tomorrow:
                desc = item["weather"][0]["description"]
                tmax = item["main"]["temp_max"]
                tmin = item["main"]["temp_min"]
                return desc, tmax, tmin
        return "Bilinmiyor", 0, 0
    except Exception as e:
        print(f"⚠️ {city} için veri alınamadı: {e}")
        return "Bilinmiyor", 0, 0

# ------------------------
# Hava durumu açıklamasına göre emoji belirleme
# ------------------------
def weather_icon(desc):
    desc = desc.lower()
    if "güneş" in desc or "clear" in desc or "açık" in desc: return "☀️"
    if "kapalı" in desc or "cloud" in desc or "bulut" in desc: return "☁️"
    if "parçalı" in desc or "partly" in desc: return "⛅"
    if "yağmur" in desc or "rain" in desc: return "🌧️"
    if "kar" in desc or "snow" in desc: return "❄️"
    if "sis" in desc or "pus" in desc or "fog" in desc: return "🌫️"
    if "fırtına" in desc or "storm" in desc: return "🌪️"
    if "şimşek" in desc or "lightning" in desc: return "🌩️"
    return "❓"

# ------------------------
# Yazıyı siyah kenarlıklı beyaz renkle çizen yardımcı fonksiyon
# ------------------------
def draw_text_with_outline(draw, position, text, font, fill="white", outline="black", outline_width=2):
    """Yazıyı siyah kenar ve beyaz iç renkle çizer"""
    x, y = position
    for dx in range(-outline_width, outline_width+1):
        for dy in range(-outline_width, outline_width+1):
            draw.text((x+dx, y+dy), text, font=font, fill=outline)
    draw.text((x, y), text, font=font, fill=fill)


# ------------------------
# Görsel oluşturma fonksiyonu
# ------------------------
def create_image(region_name):
    img = Image.open("hava.jpg").convert("RGB")  # Arka plan fotoğrafı
    width, height = img.size
    draw = ImageDraw.Draw(img)

    # Fontlar
    font_tr = r"C:\Windows\Fonts\arialbd.ttf"       # Türkçe karakter destekli, kalın
    emoji_font = r"C:\Windows\Fonts\seguiemj.ttf"   # Emoji destekli
    font_title = ImageFont.truetype(font_tr, 70)
    font_sub = ImageFont.truetype(font_tr, 60)
    font_city = ImageFont.truetype(font_tr, 55)
    font_emoji = ImageFont.truetype(emoji_font, 60)

    # Başlık
    title = region_name
    bbox = draw.textbbox((0, 0), title, font=font_title)
    x = (width - (bbox[2]-bbox[0])) / 2
    draw_text_with_outline(draw, (x, 120), title, font=font_title)

    # Tarih alt başlık
    tomorrow_date = (datetime.now() + timedelta(days=1)).strftime("%d.%m.%Y")
    yarin_gun = gun_adlari[(datetime.now() + timedelta(days=1)).weekday()]
    subtitle = f"{yarin_gun} ({tomorrow_date})"
    bbox = draw.textbbox((0, 0), subtitle, font=font_sub)
    x = (width - (bbox[2]-bbox[0])) / 2
    draw_text_with_outline(draw, (x, 220), subtitle, font=font_sub)

    # Şehir listesi
    y = 400
    for city in regions[region_name]:
        desc, tmax, tmin = get_weather(city)
        icon = weather_icon(desc)

        # Metin (şehir + sıcaklık + açıklama)
        text = f"{city}: {int(tmax)}°  {desc}"

        # Yazıyı çiz (siyah kenarlı, beyaz içli)
        bbox = draw.textbbox((0, 0), text, font=font_city)
        x = 120
        draw_text_with_outline(draw, (x, y), text, font=font_city)

        # Emoji (ayrı çiziliyor)
        emoji_bbox = draw.textbbox((0, 0), icon, font=font_emoji)
        emoji_x = width - 180  # Sağ tarafa hizala
        draw.text((emoji_x, y), icon, font=font_emoji, fill="white")
        #alt çizgi
        draw.line(
            [(100, y + bbox[3]-bbox[1]+10), (width - 100, y + bbox[3]-bbox[1]+10)],
            fill=(255,255,255),
            width=2
        )

        y += bbox[3]-bbox[1] + 70  # Boşluk ekle

    # Görseli kaydet
    filename = f"weather_{region_name}_{datetime.now().strftime('%Y%m%d')}.jpg"
    img.save(filename)
    return filename
# ------------------------
# Instagram Bağlantısı (TEK GİRİŞ)
# ------------------------
cl = Client()
cl.load_settings("session.json")

try:
    cl.login(username, password)
except Exception:
    cl.relogin()

def upload_story(image_path, region_name):
    caption = f"{region_name} için yarının hava durumu 🌥️🌧️☀️\nKaynak: OpenWeatherMap"
    cl.photo_upload_to_story(image_path, caption)



# ------------------------
# Otomatik paylaşım
# ------------------------
def job():
    for region in regions:
        print(f"⏳ {region} hazırlanıyor...")
        image_path = create_image(region)
        upload_story(image_path, region)
        print(f"✅ {region} paylaşıldı.")
        time.sleep(3)

# ------------------------
# Zamanlama
# ------------------------
schedule.every().day.at("10:00").do(job)

print("📅 Hava durumu paylaşım botu başlatıldı. Her gün 05:00'de paylaşacak.")

while True:
    schedule.run_pending()
    time.sleep(30)
