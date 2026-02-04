#!/bin/bash
set -e  # با اولین خطا متوقف شود

echo "🔧 رفع مشکلات سیستم..."
# رفع dependencyهای شکسته
sudo apt --fix-broken install -y 2>/dev/null || true
sudo dpkg --configure -a 2>/dev/null || true

# حذف لینک خراب nginx اگر وجود دارد
sudo rm -f /etc/nginx/sites-enabled/default 2>/dev/null || true

echo "🔄 آپدیت سیستم..."
sudo apt-get update
sudo apt-get upgrade -y

echo "📦 نصب بسته‌های ضروری..."
# نصب بدون reconfigure مجدد
sudo DEBIAN_FRONTEND=noninteractive apt-get install -y \
    nginx \
    v2ray \
    python3 \
    git \
    python3.12-venv \
    tmux

echo "⚙️ پیکربندی nginx..."
# ایجاد فایل default اگر وجود ندارد
if [ ! -f /etc/nginx/sites-available/default ]; then
    sudo tee /etc/nginx/sites-available/default > /dev/null << 'NGINX_EOF'
server {
    listen 80 default_server;
    listen [::]:80 default_server;
    
    root /var/www/html;
    index index.html index.htm;
    
    server_name _;
    
    location / {
        try_files $uri $uri/ =404;
    }
}
NGINX_EOF
fi

# فعال کردن سایت
sudo ln -sf /etc/nginx/sites-available/default /etc/nginx/sites-enabled/

# تست و راه‌اندازی nginx
sudo nginx -t
sudo systemctl enable nginx
sudo systemctl restart nginx

echo "🔐 تنظیم پسورد root..."
echo "root:139523" | sudo chpasswd

echo "📥 دریافت کد پروژه..."
mkdir -p ~/intelleum
cd ~/intelleum

if [ ! -d .git ]; then
    git init
    git remote add origin https://github.com/ho139523/telegram-integrated-django-site
else
    git remote set-url origin https://github.com/ho139523/telegram-integrated-django-site
fi

git pull origin master --force

echo "✅ راه‌اندازی کامل شد!"
echo "📁 محتویات دایرکتوری:"
ls -la
