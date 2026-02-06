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






#!/bin/bash

echo -e "\n\n📦 PACKAGE INSTALLATION\n\n"
# نصب بدون reconfigure مجدد
sudo DEBIAN_FRONTEND=noninteractive apt-get install -y \
    nginx \
    v2ray \
    python3 \
    git \
    python3.12-venv \
    tmux

sudo apt install -y build-essential python3-dev python3-venv libssl-dev libffi-dev certbot python3-certbot-nginx

DOMAIN="intellium.ir"
EMAIL="answereeee4@gmail.com"

echo -e "\n\n🔐 SSL VALIDATION\n\n"

# تابع ایجاد مسیرهای لازم
create_required_paths() {
    echo "Creating required directories..."
    
    # ایجاد مسیر letsencrypt اگر وجود ندارد
    sudo mkdir -p /etc/letsencrypt/live/
    sudo mkdir -p /etc/letsencrypt/archive/
    sudo mkdir -p /etc/letsencrypt/renewal/
    
    # ایجاد مسیرهای وب
    sudo mkdir -p /var/www/html/.well-known/acme-challenge/
    sudo chown -R www-data:www-data /var/www/html/
    sudo chmod -R 755 /var/www/html/
    
    # ایجاد مسیرهای پروژه
    sudo mkdir -p /var/www/intelleum/staticfiles/
    sudo mkdir -p /var/www/intelleum/media/
    sudo chown -R $USER:$USER /var/www/intelleum/
    
    echo "✓ Required directories created"
}

# تابع بررسی وجود گواهی
check_cert_exists() {
    # ابتدا مطمئن شویم مسیر وجود دارد
    if [ ! -d "/etc/letsencrypt/live/" ]; then
        return 1  # مسیر وجود ندارد، پس گواهی هم ندارد
    fi
    
    if [ -f "/etc/letsencrypt/live/$DOMAIN/fullchain.pem" ] && \
       [ -f "/etc/letsencrypt/live/$DOMAIN/privkey.pem" ]; then
        return 0  # گواهی وجود دارد
    else
        return 1  # گواهی وجود ندارد
    fi
}

# تابع بررسی اعتبار گواهی
check_cert_validity() {
    if check_cert_exists; then
        # بررسی تاریخ انقضا
        local cert_file="/etc/letsencrypt/live/$DOMAIN/fullchain.pem"
        
        if [ ! -f "$cert_file" ]; then
            return 1  # فایل وجود ندارد
        fi
        
        # خواندن تاریخ انقضا
        local expiry_date=$(sudo openssl x509 -in "$cert_file" -enddate -noout 2>/dev/null | cut -d= -f2)
        
        if [ -z "$expiry_date" ]; then
            echo "⚠️ Could not read certificate expiry date"
            return 2  # نتوانستیم تاریخ را بخوانیم، احتمالا نیاز به تمدید
        fi
        
        # تبدیل تاریخ انقضا به timestamp
        local expiry_epoch=$(date -d "$expiry_date" +%s 2>/dev/null)
        local now_epoch=$(date +%s)
        
        if [ -z "$expiry_epoch" ]; then
            echo "⚠️ Could not parse expiry date: $expiry_date"
            return 2
        fi
        
        # محاسبه روزهای باقی‌مانده
        local seconds_remaining=$((expiry_epoch - now_epoch))
        local days_remaining=$((seconds_remaining / 86400))
        
        echo "Certificate expires in $days_remaining days"
        
        # اگر گواهی کمتر از 30 روز دیگر منقضی می‌شود
        if [ $days_remaining -gt 30 ]; then
            return 0  # معتبر (بیش از 30 روز اعتبار دارد)
        else
            return 2  # منقضی شده یا کمتر از 30 روز اعتبار دارد
        fi
    else
        return 1  # گواهی وجود ندارد
    fi
}

# تابع دریافت گواهی جدید
create_certificate() {
    echo -e "\n📝 Creating new SSL certificate for $DOMAIN...\n"
    
    # ایجاد مسیرهای لازم
    create_required_paths
    
    # توقف nginx اگر در حال اجراست
    echo "Stopping Nginx for certificate setup..."
    sudo systemctl stop nginx 2>/dev/null || true
    
    # روش 1: استفاده از standalone (روش مطمئن‌تر)
    echo "Method 1: Using standalone mode..."
    if sudo certbot certonly --standalone \
        --non-interactive \
        --agree-tos \
        --email "$EMAIL" \
        -d "$DOMAIN" \
        -d "www.$DOMAIN" \
        --preferred-challenges http \
        --http-01-port 80; then
        
        echo -e "\n✅ SSL certificate created successfully using standalone method\n"
        return 0
    fi
    
    # روش 2: اگر روش اول شکست خورد، از nginx استفاده کن
    echo -e "\nMethod 1 failed, trying Method 2: Using Nginx mode..."
    
    # راه‌اندازی nginx با کانفیگ ساده
    sudo tee /etc/nginx/sites-available/certbot-setup > /dev/null <<EOF
server {
    listen 80;
    server_name $DOMAIN www.$DOMAIN;
    
    location /.well-known/acme-challenge/ {
        root /var/www/html;
    }
    
    location / {
        return 301 https://\$server_name\$request_uri;
    }
}
EOF

    sudo ln -sf /etc/nginx/sites-available/certbot-setup /etc/nginx/sites-enabled/
    sudo rm -f /etc/nginx/sites-enabled/default 2>/dev/null
    
    # راه‌اندازی nginx
    sudo nginx -t 2>/dev/null || true
    sudo systemctl start nginx
    
    # صبر کردن برای راه‌اندازی nginx
    sleep 3
    
    if sudo certbot certonly --nginx \
        --non-interactive \
        --agree-tos \
        --email "$EMAIL" \
        -d "$DOMAIN" \
        -d "www.$DOMAIN" \
        --preferred-challenges http; then
        
        echo -e "\n✅ SSL certificate created successfully using Nginx method\n"
        
        # حذف فایل موقت
        sudo rm -f /etc/nginx/sites-available/certbot-setup /etc/nginx/sites-enabled/certbot-setup 2>/dev/null
        return 0
    else
        echo -e "\n❌ Both methods failed to create SSL certificate"
        return 1
    fi
}

# تابع تمدید گواهی
renew_certificate() {
    echo -e "\n🔄 Renewing SSL certificate...\n"
    
    # اول سعی کن با renew عادی
    if sudo certbot renew --non-interactive; then
        echo -e "\n✅ SSL certificate renewed successfully\n"
        return 0
    fi
    
    # اگر renew عادی کار نکرد، force renew کن
    echo "Standard renewal failed, trying force renewal..."
    
    if sudo certbot renew --non-interactive --force-renewal; then
        echo -e "\n✅ SSL certificate force-renewed successfully\n"
        return 0
    fi
    
    # اگر هنوز کار نکرد، دستی تمدید کن
    echo "Force renewal failed, trying manual renewal..."
    
    if sudo certbot certonly --standalone \
        --non-interactive \
        --agree-tos \
        --email "$EMAIL" \
        -d "$DOMAIN" \
        -d "www.$DOMAIN" \
        --keep-until-expiring; then
        
        echo -e "\n✅ SSL certificate manually renewed\n"
        return 0
    else
        echo -e "\n⚠️ Could not renew certificate\n"
        return 1
    fi
}

# ========== اجرای منطق اصلی ==========

# ایجاد مسیرهای لازم در ابتدا
create_required_paths

# بررسی وضعیت گواهی
check_cert_validity
case $? in
    0)
        # حالت ۱: گواهی معتبر است
        echo -e "\n✅ SSL certificate is valid and up to date\n"
        
        # نمایش اطلاعات گواهی
        echo -e "📋 Certificate information:\n"
        if command -v certbot >/dev/null 2>&1; then
            sudo certbot certificates --domain "$DOMAIN" 2>/dev/null || \
            echo "Certificate details not available via certbot command"
        else
            echo "Certbot command not found, but certificate exists at:"
            echo "  /etc/letsencrypt/live/$DOMAIN/"
        fi
        
        # نمایش تاریخ انقضا
        if [ -f "/etc/letsencrypt/live/$DOMAIN/fullchain.pem" ]; then
            echo -e "\n📅 Expiry date:"
            sudo openssl x509 -in "/etc/letsencrypt/live/$DOMAIN/fullchain.pem" -enddate -noout | cut -d= -f2
        fi
        ;;
    
    1)
        # حالت ۲: گواهی وجود ندارد
        echo -e "\n⚠️ SSL certificate not found. Creating new one...\n"
        
        if create_certificate; then
            echo -e "\n✅ SSL setup completed successfully\n"
            
            # بررسی نهایی
            if check_cert_exists; then
                echo "✓ Certificate verified: /etc/letsencrypt/live/$DOMAIN/"
            else
                echo "⚠️ Certificate creation reported success but files not found!"
            fi
        else
            echo -e "\n❌ SSL setup failed\n"
            echo "Possible reasons:"
            echo "  1. Domain $DOMAIN does not point to this server's IP"
            echo "  2. Port 80 is blocked (check firewall: sudo ufw status)"
            echo "  3. DNS propagation is not complete"
            echo ""
            echo "To debug:"
            echo "  sudo certbot certonly --standalone -d $DOMAIN --dry-run"
            exit 1
        fi
        ;;
    
    2)
        # حالت ۳: گواهی منقضی شده یا نزدیک به انقضا
        echo -e "\n⚠️ SSL certificate is expired or expiring soon. Renewing...\n"
        
        if renew_certificate; then
            echo -e "\n✅ SSL renewal completed\n"
        else
            echo -e "\n🔄 Renewal failed, trying to create new certificate instead...\n"
            if create_certificate; then
                echo -e "\n✅ New SSL certificate created\n"
            else
                echo -e "\n❌ Failed to renew/create SSL certificate\n"
                echo "You may need to check DNS and firewall settings."
                exit 1
            fi
        fi
        ;;
esac

# تنظیم تمدید خودکار (Cron Job) اگر وجود ندارد
echo -e "\n⏰ Setting up auto-renewal...\n"
if [ ! -f /etc/cron.d/certbot-renew ] || ! grep -q "certbot renew" /etc/cron.d/certbot-renew 2>/dev/null; then
    echo "0 3 * * * root /usr/bin/certbot renew --quiet --post-hook 'systemctl reload nginx' 2>/dev/null" | sudo tee /etc/cron.d/certbot-renew >/dev/null
    echo "✓ Auto-renew cron job added (daily at 3 AM)"
else
    echo "✓ Auto-renew cron job already exists"
fi

echo -e "\n\n🌐 NGINX SETUP \n\n"

# تابع تنظیم Nginx
setup_nginx() {
    echo "Creating Nginx configuration for $DOMAIN..."
    
    # مطمئن شویم گواهی وجود دارد
    if ! check_cert_exists; then
        echo "❌ Cannot setup Nginx: SSL certificate not found!"
        return 1
    fi
    
    # ایجاد کانفیگ nginx
    sudo tee /etc/nginx/sites-available/$DOMAIN > /dev/null << NGINX_EOF
# Redirect HTTP to HTTPS
server {
    listen 80;
    listen [::]:80;
    server_name $DOMAIN www.$DOMAIN;

    # برای Certbot challenges
    location /.well-known/acme-challenge/ {
        root /var/www/html;
        allow all;
    }

    return 301 https://\$host\$request_uri;
}

# Django on HTTPS
server {
    listen 443 ssl http2;
    listen [::]:443 ssl http2;
    server_name $DOMAIN www.$DOMAIN;

    ssl_certificate /etc/letsencrypt/live/$DOMAIN/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/$DOMAIN/privkey.pem;

    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256:ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-GCM-SHA384;
    ssl_prefer_server_ciphers off;

    ssl_session_cache shared:SSL:10m;
    ssl_session_timeout 10m;

    add_header Strict-Transport-Security "max-age=63072000; includeSubDomains; preload" always;
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;

    client_max_body_size 20M;

    # ---- Static Files ----
    location /static/ {
        alias /var/www/intelleum/staticfiles/;
        expires 30d;
        access_log off;
        try_files \$uri \$uri/ =404;
    }

    location /media/ {
        alias /var/www/intelleum/media/;
        expires 30d;
        access_log off;
        try_files \$uri \$uri/ =404;
    }

    # ---- Django ----
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_set_header X-Forwarded-Host \$server_name;
        
        proxy_buffer_size 128k;
        proxy_buffers 4 256k;
        proxy_busy_buffers_size 256k;
        
        proxy_connect_timeout 300s;
        proxy_send_timeout 300s;
        proxy_read_timeout 300s;
    }

    # Health check
    location /health {
        access_log off;
        return 200 "healthy\n";
        add_header Content-Type text/plain;
    }
}
NGINX_EOF

    # فعال کردن سایت
    sudo ln -sf /etc/nginx/sites-available/$DOMAIN /etc/nginx/sites-enabled/
    
    # حذف سایت پیش‌فرض اگر وجود دارد
    sudo rm -f /etc/nginx/sites-enabled/default 2>/dev/null
    
    echo "✓ Nginx configuration created"
}

# بررسی وجود کانفیگ nginx
if [ -f "/etc/nginx/sites-available/$DOMAIN" ]; then
    echo "✓ Nginx config already exists for $DOMAIN"
    
    # بررسی محتوای فایل (ممکن است نیاز به بروزرسانی مسیر گواهی باشد)
    if ! grep -q "ssl_certificate /etc/letsencrypt/live/$DOMAIN/fullchain.pem" /etc/nginx/sites-available/$DOMAIN; then
        echo "⚠️ Updating SSL certificate paths in nginx config..."
        setup_nginx
    fi
else
    echo "Creating nginx config for $DOMAIN..."
    setup_nginx
fi

# تست و راه‌اندازی Nginx
echo -e "\n🔧 Testing nginx configuration..."
if sudo nginx -t 2>&1; then
    echo -e "✅ Nginx configuration test passed\n"
    
    # فعال‌سازی و راه‌اندازی
    sudo systemctl enable nginx 2>/dev/null
    sudo systemctl restart nginx
    
    sleep 3
    
    if systemctl is-active --quiet nginx; then
        echo -e "✅ NGINX IS ACTIVE AND RUNNING\n"
        
        # بررسی وضعیت
        echo -e "📊 Nginx status:"
        sudo systemctl status nginx --no-pager | grep -A 2 "Active:" || true
    else
        echo -e "\n❌ NGINX FAILED TO START\n"
        sudo systemctl status nginx --no-pager | tail -20
        exit 1
    fi
else
    echo -e "\n❌ Nginx configuration test failed\n"
    sudo nginx -t 2>&1 | tail -10
    exit 1
fi

# نمایش اطلاعات نهایی
echo -e "\n\n🎉 SETUP COMPLETED SUCCESSFULLY!\n"
echo -e "=========================================="
echo -e "📋 SUMMARY"
echo -e "=========================================="
echo -e "• Domain:           $DOMAIN"
echo -e "• SSL Certificate:  $(check_cert_exists && echo '✓ INSTALLED' || echo '✗ NOT INSTALLED')"
echo -e "• Nginx Status:     $(systemctl is-active --quiet nginx && echo '✓ RUNNING' || echo '✗ STOPPED')"
echo -e "• Auto-renew:       $(grep -q "certbot renew" /etc/cron.d/certbot-renew 2>/dev/null && echo '✓ CONFIGURED' || echo '✗ NOT CONFIGURED')"

if check_cert_exists; then
    echo -e "• Cert Location:    /etc/letsencrypt/live/$DOMAIN/"
    if [ -f "/etc/letsencrypt/live/$DOMAIN/fullchain.pem" ]; then
        expiry=$(sudo openssl x509 -in "/etc/letsencrypt/live/$DOMAIN/fullchain.pem" -enddate -noout 2>/dev/null | cut -d= -f2)
        echo -e "• Expiry Date:      $expiry"
    fi
fi

echo -e "=========================================="
echo -e "\n🔗 Your site should be accessible at:"
echo -e "   🌐 https://$DOMAIN"
echo -e "   🔗 https://www.$DOMAIN"
echo -e "\n⚠️  If you cannot access the site, check:"
echo -e "   1. DNS propagation (nslookup $DOMAIN)"
echo -e "   2. Firewall settings (sudo ufw status)"
echo -e "   3. Nginx error logs (sudo tail -f /var/log/nginx/error.log)"
echo -e "\n"







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
sudo ufw allow 80
sudo ufw status
sudo ufw status numbered



echo -e "\n\n🔄 MAKE MIGRATIONS\n\n"
python manage.py makemigrations
python manage.py migrate

echo -e "\n\n📁 RUNNING DJANGO\n\n"
python manage.py runserver


