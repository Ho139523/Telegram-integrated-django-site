#!/bin/bash
set -e  # با اولین خطا متوقف شود

echo "\n\n🔧 SYSTEM FIX\n\n"
# رفع dependencyهای شکسته
sudo apt --fix-broken install -y 2>/dev/null || true
sudo dpkg --configure -a 2>/dev/null || true

# حذف لینک خراب nginx اگر وجود دارد
sudo rm -f /etc/nginx/sites-enabled/default 2>/dev/null || true

echo "\n\n🔄 SYSTEM UPDTAE \n\n"
sudo apt-get update
sudo apt-get upgrade -y

echo "\n\n📦 PACKAGE INSTALLATION\n\n"
# نصب بدون reconfigure مجدد
sudo DEBIAN_FRONTEND=noninteractive apt-get install -y \
    nginx \
    v2ray \
    python3 \
    git \
    python3.12-venv \
    tmux

echo "\n\n NGINX SETUP \n\n"
# ایجاد فایل default اگر وجود ندارد
if [ ! -f /etc/nginx/sites-available/default ]; then
    sudo tee /etc/nginx/sites-available/default > /dev/null << 'NGINX_EOF'
# Redirect HTTP to HTTPS
server {
    listen 80;
    listen [::]:80;
    server_name intellium.ir www.intellium.ir;

    return 301 https://$host$request_uri;
}

# Django on HTTPS
server {
    listen 443 ssl http2;
    listen [::]:443 ssl http2;
    server_name intellium.ir www.intellium.ir;

    ssl_certificate /etc/letsencrypt/live/intellium.ir/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/intellium.ir/privkey.pem;

    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_prefer_server_ciphers off;

    add_header Strict-Transport-Security "max-age=63072000; includeSubDomains; preload" always;

    client_max_body_size 20M;


    # ---- Static Files ----
    location /static/ {
        alias /var/www/intelleum/staticfiles/;
        expires 30d;
        access_log off;
    }

    location /media/ {
        alias /var/www/intelleum/media/;
        expires 30d;
        access_log off;
    }


    # ---- Django ----
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
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

echo "\n\n🔐 UPDATE PASSWORD\n\n"
echo "root:139523" | sudo chpasswd

echo "\n\n📥 RECIEVING PROJECT\n\n"
mkdir -p ~/intelleum
cd ~/intelleum

if [ ! -d .git ]; then
    git init
    git remote add origin https://github.com/ho139523/telegram-integrated-django-site
else
    git remote set-url origin https://github.com/ho139523/telegram-integrated-django-site
fi

git pull origin master --force

echo "\n\n✅ SERVER SETUP ACCOMPLISHED\n\n"
echo "\n\n📁 DIRECTORY CONTENT\n\n"
ls -la


echo -e "\n\n FIREWALL SETUP\n\n"
echo "y" | sudo ufw enable
sudo ufw allow 443
sudo ufw status
sudo ufw status numbered
