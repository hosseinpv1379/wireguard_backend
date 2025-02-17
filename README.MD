# WireGuard Management API

این پروژه یک API برای مدیریت WireGuard VPN است که امکان ایجاد، حذف و مدیریت peer ها را فراهم می‌کند.

## پیش‌نیازها

- Python 3.8+
- WireGuard
- pip

## نصب

### 1. نصب WireGuard
```bash
# برای اوبونتو/دبیان
sudo apt update
sudo apt install wireguard

# برای سنت‌او‌اس
sudo yum install wireguard-tools
```

### 2. کلون پروژه
```bash
git clone https://github.com/hosseinpv1379/wireguard_backend.git
cd wireguard_backend
```

### 3. ایجاد و فعال‌سازی محیط مجازی
```bash
# ایجاد محیط مجازی
python3 -m venv venv

# فعال‌سازی محیط مجازی
# در لینوکس/مک
source venv/bin/activate
# در ویندوز
.\venv\Scripts\activate

# به‌روزرسانی pip
pip install --upgrade pip
```

### 4. نصب وابستگی‌ها
```bash
pip install -r requirements.txt
```

### 5. ایجاد فایل requirements.txt
```bash
# محتوای فایل requirements.txt
flask==2.0.1
python-dotenv==0.19.0
dataclasses==0.6
```

### 6. ایجاد فایل .env
```bash
# ایجاد و ویرایش فایل .env
cp .env.example .env
nano .env
```

محتوای فایل .env:
```
WG_SERVER_PUBLIC_KEY=your_server_public_key
WG_SERVER_ENDPOINT=your_server_ip
WG_INTERFACE=wg0
WG_CONFIG_PATH=/etc/wireguard/wg0.conf
```

## راه‌اندازی

### 1. تنظیم دسترسی‌های لازم
```bash
# ایجاد دایرکتوری برای ذخیره IP ها
sudo mkdir -p /var/lib/wireguard-api
sudo chown -R $USER:$USER /var/lib/wireguard-api

# تنظیم دسترسی به فایل کانفیگ وایرگارد
sudo chmod 600 /etc/wireguard/wg0.conf
```

### 2. اجرای برنامه

#### در محیط توسعه:
```bash
# فعال‌سازی محیط مجازی اگر فعال نیست
source venv/bin/activate

# اجرای برنامه
python run.py
```

#### در محیط تولید با Gunicorn:
```bash
# نصب gunicorn در محیط مجازی
pip install gunicorn

# اجرا با gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 "run:create_app()"
```

## استفاده از API

### ساخت Peer جدید
```bash
curl -X POST http://localhost:5000/api/peer
```

### دریافت اطلاعات یک Peer
```bash
curl http://localhost:5000/api/peer/<public_key>
```

### دریافت لیست تمام Peer ها
```bash
curl http://localhost:5000/api/peers
```

### حذف یک Peer
```bash
curl -X DELETE http://localhost:5000/api/peer/<public_key>
```

## ساختار پروژه
```
project/
├── config/               # تنظیمات پروژه
│   ├── __init__.py
│   └── config.py
├── app/                 # کد اصلی برنامه
│   ├── models/         # مدل‌های داده
│   ├── services/       # سرویس‌های اصلی
│   ├── utils/          # توابع کمکی
│   └── api/            # API endpoints
├── venv/               # محیط مجازی
├── requirements.txt    # وابستگی‌ها
├── .env               # متغیرهای محیطی
├── .env.example       # نمونه فایل env
└── run.py             # فایل اجرایی اصلی
```

## نکات امنیتی

1. حتماً دسترسی فایل کانفیگ وایرگارد را روی 600 تنظیم کنید
2. از محیط مجازی استفاده کنید
3. API را پشت یک reverse proxy مانند Nginx قرار دهید
4. از HTTPS استفاده کنید
5. سیستم احراز هویت اضافه کنید

## عیب‌یابی رایج

### خطای دسترسی به فایل کانفیگ
```bash
sudo chown -R $USER:$USER /etc/wireguard
sudo chmod 600 /etc/wireguard/wg0.conf
```

### خطای اجرای gunicorn
اطمینان حاصل کنید که در محیط مجازی هستید:
```bash
source venv/bin/activate
```

### مشکل در تخصیص IP
بررسی فایل ذخیره IP ها:
```bash
cat /var/lib/wireguard-api/ip_assignments.json
```

## مشارکت در پروژه

1. پروژه را fork کنید
2. یک branch جدید ایجاد کنید
3. تغییرات خود را commit کنید
4. یک pull request ایجاد کنید

## لایسنس

این پروژه تحت لایسنس MIT منتشر شده است.
