#!/bin/bash

ANSWER1="$1"
ANSWER2="$2"

set -e  

echo -e "\n\n🔧 SYSTEM FIX\n\n"

sudo apt --fix-broken install -y 2>/dev/null || true
sudo dpkg --configure -a 2>/dev/null || true


sudo rm -f /etc/nginx/sites-enabled/default 2>/dev/null || true



echo -e "\n\n🔄 SYSTEM UPDTAE \n\n"





if [ -z "$ANSWER1" ]; then
    read -p "Do you want to UPDATE AND UPGRADE system? (yes/no): " ANSWER1
fi

ANSWER=$(echo "$ANSWER1" | tr '[:upper:]' '[:lower:]')

if [ "$ANSWER1" = "yes" ]; then
    echo "\n\nSYSTEM UPDATE AND UPGRADE...\n\n"
    
    sudo apt-get update
    sudo apt-get upgrade -y

elif [ "$ANSWER1" = "no" ]; then
    echo "\n\nSKIPPING SYSTEM UPDDATE AND UPGRADE\n\n"

else
    echo "\n\n⚠️ Invalid input: $ANSWER1"
    echo "Please use 'yes' or 'no'"

    exit 1
fi







echo -e "\n\n📦 PACKAGE INSTALLATION\n\n"
# نصب بدون reconfigure مجدد
sudo DEBIAN_FRONTEND=noninteractive apt-get install -y \
    nginx \
    v2ray \
    python3 \
    git \
    python3.12-venv \
    tmux

sudo apt install -y build-essential python3-dev python3-venv libssl-dev libffi-dev

echo -e "\n\n NGINX SETUP \n\n"
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

sudo ln -sf /etc/nginx/sites-available/default /etc/nginx/sites-enabled/

sudo nginx -t
sudo systemctl enable nginx
sudo systemctl restart nginx


if systemctl is-active --quiet nginx; then
    echo "\n\n✅ NGINX IS ACTIVE\n\n"
else
    echo "\n\n❌ NGINX IS NOT ACTIVE\n\n"
fi



echo -e "\n\n🔐 UPDATE PASSWORD\n\n"
echo "root:139523" | sudo chpasswd



echo -e "\n\n📥 RECIEVING PROJECT\n\n"
mkdir -p ~/intelleum
cd ~/intelleum

if [ ! -d .git ]; then
    git init
    git remote add origin https://$GIT_TOKEN@github.com/ho139523/telegram-integrated-django-site
else
    git remote set-url origin https://$GIT_TOKEN@github.com/ho139523/telegram-integrated-django-site
fi

git pull origin master --force


echo -e "\n\n SYS ENV VAR DEFINITION\n\n"
append_if_not_exists() {
    local line="$1"
    local file="$2"
    grep -qxF "$line" "$file" || echo "$line" >> "$file"
}

append_if_not_exists 'alias runserver="cd ~/intelleum ; source ~/intelleum/myenv/bin/activate ; python manage.py runserver"' ~/.bashrc
append_if_not_exists 'alias prj="cd ~/intelleum ; source ~/intelleum/myenv/bin/activate"' ~/.bashrc

source ~/.bashrc

echo -e "\n\n VENV CREATION\n\n"

if [ -d "myenv" ]; then
    echo "✅ Virtual environment already exists. Skipping..."
else
    echo "✅ Virtual environment created."
    python3 -m venv myenv
fi

cd ~/intelleum
source ~/intelleum/myenv/bin/activate


echo -e "\n\n VENV PACKAGE INSTALLATION\n\n"



if [ -z "$ANSWER2" ]; then
        read -p "Do you want to install pip packages? (yes/no): " ANSWER2
fi

if [ "$ANSWER2" = "yes" ]; then
	pip install --upgrade pip
	pip install -r requirements.txt

elif [ "$ANSWER2" = "no" ]; then
	echo -e "\n\n VENV PACKAGES INSTALLATION SKIPPED !\n\n"

else

    echo "\n\n⚠️ Invalid input: $ANSWER2"
    echo "Please use 'yes' or 'no'"
    exit 1
fi


echo -e "\n\n✅ SERVER SETUP ACCOMPLISHED\n\n"
echo -e "\n\n📁 DIRECTORY CONTENT\n\n"
ls -la


echo -e "\n\n FIREWALL SETUP\n\n"
echo "y" | sudo ufw enable
sudo ufw allow 22
sudo ufw allow 443
sudo ufw status
sudo ufw status numbered



echo -e "\n\n📁 RUNNING DJANGO\n\n"
python manage.py runserver


