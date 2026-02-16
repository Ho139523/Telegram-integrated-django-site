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
    echo -e "\n\nSYSTEM UPDATE AND UPGRADE...\n\n"
    
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


sudo DEBIAN_FRONTEND=noninteractive apt-get install -y \
    nginx \
    v2ray \
    python3 \
    git \
    python3.12-venv \
    tmux

sudo apt install -y build-essential python3-dev python3-venv libssl-dev libffi-dev certbot python3-certbot-nginx

sudo apt install -y python3-pip redis-server net-tools




# بررسی نصب بودن vim با dpkg
if dpkg -l | grep -q "^ii  vim "; then
    echo "✓ vim از قبل نصب شده است."
else
    echo "✗ vim نصب نیست. در حال نصب..."
    sudo apt update
    sudo apt install -y vim
    if [ $? -eq 0 ]; then
        echo "✓ vim با موفقیت نصب شد."
    else
        echo "✗ خطا در نصب vim!"
        exit 1
    fi
fi



# Change tmux config settings

cat > ~/.tmux.conf <<EOF
# غیرفعال کردن کلید پیش‌فرض (Ctrl+b)
# استفاده از حالت vi در tmux (برای ناوبری با صفحه کلید)
set -g status-keys vi
set -g mode-keys vi

# تنظیم کلیدهای مشابه Vim برای کپی پیست
bind -T copy-mode-vi 'v' send -X begin-selection
bind -T copy-mode-vi 'V' send -X select-line
bind -T copy-mode-vi 'y' send -X copy-selection-and-cancel
bind -T copy-mode-vi 'Y' send -X copy-line
bind -T copy-mode-vi 'C-v' send -X rectangle-toggle
set -g mouse on
unbind C-b

# تنظیم کلید prefix جدید به Alt + j (که در tmux با M-j نمایش داده می‌شود)
set -g prefix M-j

# ارسال کلید به برنامه‌های داخل tmux در صورت نیاز
bind M-j send-prefix
EOF


#tmux kill-server


# Change vim config settings

cat > ~/.vimrc << EOF
" فعال‌سازی نوار وضعیت (statusline)
set laststatus=2
" مخفی کردن حالت ویرایش از خط فرمان
set noshowmode

" تنظیم رنگ نوار وضعیت به سبز
highlight StatusLine ctermfg=green ctermbg=black

" پاک کردن مقدار قبلی statusline و ساخت یک statusline جدید
set statusline=
" نمایش حالت Vim (NORMAL، INSERT و ...) با رنگ متفاوت
set statusline+=%#DiffChange#
set statusline+=\ %{toupper(mode())}\
set statusline+=%#StatusLine#
" نمایش نام فایل با مسیر نسبی
set statusline+=\ %f
" نمایش علامت فقط‌خواندنی (Read-only) در صورت وجود
set statusline+=\ %r
" نمایش علامت تغییر (Modified) در صورت وجود
set statusline+=\ %m
" جداکننده - آیتم‌های بعدی به سمت راست می‌روند
set statusline+=\ %=
" نمایش شماره خط و ستون
set statusline+=\ Ln:\ %l,\ Col:\ %c
" نمایش درصد پیشرفت
set statusline+=\ (%p%%)
EOF


mkdir -p ~/intelleum
cd ~/intelleum

echo -e "\n\n VENV CREATION\n\n"

if [ -d "myenv" ]; then
    echo "✅ Virtual environment already exists. Skipping..."
else
    echo "✅ Virtual environment created."
    python3 -m venv myenv
fi

cd ~/intelleum
source ~/intelleum/myenv/bin/activate



pip install redis







DOMAIN="intellium.ir"
WWW_DOMAIN="www.intellium.ir"
WEBROOT="/var/www/certbot"
NGINX_CONF="/etc/nginx/sites-available/$DOMAIN"

echo "=========================================="
echo "Starting Nginx + Certbot setup for $DOMAIN"
echo "=========================================="

# 3. Create webroot for Certbot
echo "[3/8] Creating webroot directory for Certbot..."
mkdir -p $WEBROOT
chown -R www-data:www-data $WEBROOT

# 4. Create base Nginx config for HTTP (Certbot challenge)
echo "[4/8] Creating base Nginx configuration for Certbot..."

cat > $NGINX_CONF <<EOF
server {
    listen 80;
    listen [::]:80;

    server_name $DOMAIN $WWW_DOMAIN;

    # Certbot HTTP-01 challenge
    location /.well-known/acme-challenge/ {
        root $WEBROOT;
        allow all;
        default_type "text/plain";
    }

    # Test response
    location / {
        return 200 "Certbot ready\n";
        add_header Content-Type text/plain;
    }
}
EOF


sudo ufw allow 80
rm -rf /etc/nginx/sites-available/default

# 5. Enable Nginx site
echo "[5/8] Enabling Nginx site..."
ln -sf $NGINX_CONF /etc/nginx/sites-enabled/$DOMAIN

echo "Testing Nginx configuration..."
nginx -t
systemctl reload nginx

# 7. Obtain SSL certificate
echo "[7/8] Requesting SSL certificate from Let's Encrypt..."
certbot certonly \
  --webroot \
  -w $WEBROOT \
  -d $DOMAIN \
  -d $WWW_DOMAIN

# 8. Configure HTTPS
echo "[8/8] Updating Nginx configuration for HTTPS..."

echo "Reloading Nginx with HTTPS configuration..."
nginx -t
systemctl reload nginx

echo "=========================================="
echo "SSL setup completed successfully!"
echo "Domain: https://$DOMAIN"
echo "=========================================="









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


sudo mkdir -p /var/www/intelleum/staticfiles/
sudo mkdir -p /var/www/intelleum/media/

sudo chown -R www-data:www-data /var/www/intelleum/
sudo chmod -R 755 /var/www/intelleum/











# ============================================
# FTP Server Installation and Configuration Script
# for new server with root user access
# ============================================

# Colors for better output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to display messages
print_status() {
    echo -e "${GREEN}[+]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[!]${NC} $1"
}

print_error() {
    echo -e "${RED}[!]${NC} $1"
}

# ============================================
# Section 1: Server Information Gathering
# ============================================

print_status "Gathering server information..."

# Get public IP address of the server
PUBLIC_IP=$(curl -s http://ifconfig.me 2>/dev/null || curl -s http://ipinfo.io/ip 2>/dev/null || hostname -I | awk '{print $1}')
if [ -z "$PUBLIC_IP" ]; then
    print_warning "Cannot detect public IP. Please enter manually:"
    read -p "Server public IP: " PUBLIC_IP
else
    print_status "Detected public IP: $PUBLIC_IP"
    read -p "Is this IP correct? (y/n): " CONFIRM_IP
    if [[ $CONFIRM_IP != "y" && $CONFIRM_IP != "Y" ]]; then
        read -p "Please enter the server public IP: " PUBLIC_IP
    fi
fi

# Get Passive port number
read -p "Enter Passive Mode port (default: 2121): " PASV_PORT
PASV_PORT=${PASV_PORT:-2121}

# Get FTP password for root user
read -s -p "FTP password for root user (leave empty to keep current SSH password): " FTP_PASSWORD
echo ""

# ============================================
# Section 2: Prerequisites Installation
# ============================================

print_status "Updating system packages..."
apt-get update > /dev/null 2>&1
apt-get upgrade -y > /dev/null 2>&1

print_status "Installing vsftpd and required tools..."
apt-get install -y vsftpd lftp ftp ufw > /dev/null 2>&1

# ============================================
# Section 3: vsftpd Configuration
# ============================================

print_status "Configuring vsftpd..."

# Backup original configuration file
cp /etc/vsftpd.conf /etc/vsftpd.conf.backup

# Create new configuration file
cat > /etc/vsftpd.conf << EOF
# ============================================
# vsftpd configuration for new server
# Generated by installation script
# ============================================

# Basic settings
listen=YES
listen_port=21
listen_ipv6=NO

# Authentication
anonymous_enable=NO
local_enable=YES
write_enable=YES
local_umask=022

# Logging
dirmessage_enable=YES
use_localtime=YES
xferlog_enable=YES
xferlog_file=/var/log/vsftpd.log
xferlog_std_format=YES
log_ftp_protocol=YES

# Disable port 20 to avoid NAT issues
connect_from_port_20=NO

# Security Chroot settings
chroot_local_user=YES
allow_writeable_chroot=YES

# Passive Mode settings
pasv_enable=YES
pasv_min_port=$PASV_PORT
pasv_max_port=$PASV_PORT
pasv_address=$PUBLIC_IP
pasv_promiscuous=YES

# Active Mode settings
port_enable=YES

# Connection limits
max_clients=10
max_per_ip=3
local_root=/

# Allow root access
userlist_enable=YES
userlist_file=/etc/vsftpd.userlist
userlist_deny=NO

# SSL settings (disabled)
ssl_enable=NO

# Prevent 530 login errors
seccomp_sandbox=NO
EOF

# Create user access list
echo "root" > /etc/vsftpd.userlist
chmod 600 /etc/vsftpd.userlist

print_status "Configuring root access..."

# 1. Remove root from ftpusers (blacklist file)
if [ -f /etc/ftpusers ]; then
    cp /etc/ftpusers /etc/ftpusers.backup
    grep -v "^root$" /etc/ftpusers > /tmp/ftpusers.tmp
    mv /tmp/ftpusers.tmp /etc/ftpusers
    print_status "Root removed from /etc/ftpusers"
fi

# 2. Remove root from ftpusers if exists with different format
sed -i '/^#root$/d' /etc/ftpusers 2>/dev/null || true

# ============================================
# Section 4: Root User Access Configuration
# ============================================

print_status "Configuring root user access..."

# Add root to allowed FTP users list
if ! grep -q "^root" /etc/ftpusers 2>/dev/null; then
    cp /etc/ftpusers /etc/ftpusers.backup
    grep -v "^root$" /etc/ftpusers > /etc/ftpusers.tmp
    mv /etc/ftpusers.tmp /etc/ftpusers
fi

# Change password if new password provided
if [ -n "$FTP_PASSWORD" ]; then
    echo "root:$FTP_PASSWORD" | chpasswd
    print_status "Root password changed."
fi

# Set appropriate shell for FTP access
if ! grep -q "^root.*/bin/bash" /etc/passwd; then
    usermod -s /bin/bash root
fi

# ============================================
# Section 5: Firewall Configuration
# ============================================

print_status "Configuring firewall..."

# Enable UFW if not already enabled
ufw --force enable > /dev/null 2>&1

# Open required ports
ufw allow ssh > /dev/null 2>&1
ufw allow 21/tcp > /dev/null 2>&1
ufw allow $PASV_PORT/tcp > /dev/null 2>&1

print_status "Firewall status:"
ufw status numbered | head -20

# ============================================
# Section 6: Service Startup (Corrected Section)
# ============================================

print_status "Starting vsftpd service..."

# 🔴 Correction 1: Completely stop vsftpd before starting
print_status "Stopping vsftpd (if running)..."
systemctl stop vsftpd 2>/dev/null || true
pkill -9 vsftpd 2>/dev/null || true

# 🔴 Correction 2: Wait to ensure complete shutdown
sleep 3

# 🔴 Correction 3: Verify no vsftpd processes are running
if pgrep vsftpd > /dev/null; then
    print_warning "vsftpd is still running. Force killing..."
    pkill -9 vsftpd
    sleep 2
fi

# 🔴 Correction 4: Reload systemd
systemctl daemon-reload

# 🔴 Correction 5: Start service with delay and error checking
print_status "Starting vsftpd..."
if systemctl start vsftpd; then
    sleep 2  # Wait for service to start
else
    print_error "Error starting service. Retrying..."
    systemctl stop vsftpd 2>/dev/null || true
    pkill -9 vsftpd 2>/dev/null || true
    sleep 2
    systemctl start vsftpd
    sleep 2
fi

systemctl enable vsftpd > /dev/null 2>&1

# 🔴 Correction 6: Check status with longer pause
print_status "Checking service status..."
sleep 3

if systemctl is-active --quiet vsftpd; then
    print_status "vsftpd service started successfully."

    # Quick test
    print_status "Running quick test..."
    sleep 2

    # Check port
    if netstat -tln | grep -q ":21 "; then
        print_status "Port 21 is listening."
    else
        print_warning "Port 21 is not listening."
    fi

else
    print_error "Error starting vsftpd service"
    print_error "Checking logs..."
    journalctl -u vsftpd -n 15 --no-pager

    # Attempt manual debug
    print_status "Attempting manual startup..."
    vsftpd -olisten=YES /etc/vsftpd.conf &
    sleep 3
    if [ $? -eq 0 ]; then
        print_status "vsftpd started manually successfully."
    else
        print_error "Manual startup also failed."
        exit 1
    fi
fi

# ============================================
# Section 7: Installation Testing
# ============================================

print_status "Running initial tests..."

# Test 1: Check listening ports
echo "--- Listening Ports ---"
netstat -tlnp | grep -E ":21|:$PASV_PORT" 2>/dev/null || echo "   Ports not found"

# Test 2: Check service status
echo ""
echo "--- Service Status ---"
systemctl status vsftpd --no-pager -l | head -15

# Test 3: Local connection test
echo ""
echo "--- Local Connection Test ---"
timeout 3 bash -c "echo -e 'user root\nquit' | ftp localhost 21" 2>/dev/null | \
    grep -E "220|230|Login successful" || \
    echo "   Local connection test failed"

# ============================================
# Section 8: Final Information Display
# ============================================

echo ""
echo -e "${GREEN}✅ Installation and configuration completed!${NC}"
echo ""
echo "============================== FTP Server Information =============================="
echo "Server Address: ftp://$PUBLIC_IP"
echo "Control Port: 21"
echo "Passive Port: $PASV_PORT"
echo "Username: root"
echo "Password: $(if [ -n "$FTP_PASSWORD" ]; then echo "New SSH password"; else echo "Current SSH password"; fi)"
echo "================================================================================"
echo ""
echo ""
echo "To test from client:"
echo "lftp -e 'set ftp:passive-mode on; ls' ftp://root@$PUBLIC_IP"
echo ""
echo -e "${YELLOW}⚠️ Security Note:${NC}"
echo "Root access via FTP is not recommended for security."
echo "For production environments, use a regular user with sudo privileges."

echo ""
echo ""
echo ""
echo ""
echo ""















### ===============================
### VARIABLES (edit if needed)
### ===============================
DOMAIN="intellium.ir"
XRAY_PORT=10000
NGINX_PORT=10001
WS_PATH="/vless"
UUID="d1772a6e-41f4-424d-931a-aaab7f8b3f64"
XRAY_INSTALLED=false
XRAY_CONFIGURED=false
NGINX_CONFIGURED=false
SERVICE_CONFIGURED=false

### ===============================
echo "[1/10] Checking prerequisites..."
### ===============================
# Check if packages are installed
for pkg in curl unzip nginx ufw; do
    if ! dpkg -l | grep -q "^ii.*$pkg "; then
        echo "Installing $pkg..."
        apt install -y "$pkg"
    else
        echo "$pkg is already installed."
    fi
done

### ===============================
echo "[2/10] Checking Xray installation..."
### ===============================
if [ -f "/usr/local/bin/xray" ]; then
    echo "Xray is already installed."
    XRAY_INSTALLED=true
else
    echo "Installing Xray core..."
    curl -L https://github.com/XTLS/Xray-install/raw/main/install-release.sh | bash
    XRAY_INSTALLED=true
fi

### ===============================
echo "[3/10] Checking Xray configuration..."
### ===============================
XRAY_CONFIG_FILE="/usr/local/etc/xray/config.json"
EXPECTED_CONFIG=$(cat <<EOF
{
  "log": {
    "loglevel": "warning"
  },
  "inbounds": [
    {
      "port": ${XRAY_PORT},
      "listen": "0.0.0.0",
      "protocol": "vless",
      "settings": {
        "clients": [
          {
            "id": "${UUID}",
            "flow": ""
          }
        ],
        "decryption": "none"
      },
      "streamSettings": {
        "network": "ws",
        "security": "none",
        "wsSettings": {
          "path": "${WS_PATH}"
        }
      }
    }
  ],
  "outbounds": [
    {
      "protocol": "freedom",
      "settings": {}
    }
  ]
}
EOF
)

# Create directory if doesn't exist
mkdir -p /usr/local/etc/xray

# Check if config exists and is correct
if [ -f "$XRAY_CONFIG_FILE" ]; then
    CURRENT_CONFIG=$(cat "$XRAY_CONFIG_FILE")
    if [ "$CURRENT_CONFIG" = "$EXPECTED_CONFIG" ]; then
        echo "Xray configuration is already up to date."
        XRAY_CONFIGURED=true
    else
        echo "Updating Xray configuration..."
        echo "$EXPECTED_CONFIG" > "$XRAY_CONFIG_FILE"
        XRAY_CONFIGURED=true
    fi
else
    echo "Creating Xray configuration..."
    echo "$EXPECTED_CONFIG" > "$XRAY_CONFIG_FILE"
    XRAY_CONFIGURED=true
fi

### ===============================
echo "[4/10] Checking Xray service..."
### ===============================
SERVICE_FILE="/etc/systemd/system/xray.service"
SERVICE_CONTENT=$(cat <<EOF
[Unit]
Description=Xray Service
Documentation=https://github.com/xtls
After=network.target nss-lookup.target

[Service]
User=root
CapabilityBoundingSet=CAP_NET_ADMIN CAP_NET_BIND_SERVICE
AmbientCapabilities=CAP_NET_ADMIN CAP_NET_BIND_SERVICE
NoNewPrivileges=true
ExecStart=/usr/local/bin/xray run -config /usr/local/etc/xray/config.json
Restart=on-failure
RestartPreventExitStatus=23
LimitNPROC=10000
LimitNOFILE=1000000
RuntimeDirectory=xray
RuntimeDirectoryMode=0755

[Install]
WantedBy=multi-user.target
EOF
)

if [ -f "$SERVICE_FILE" ]; then
    CURRENT_SERVICE=$(cat "$SERVICE_FILE")
    if [ "$CURRENT_SERVICE" = "$SERVICE_CONTENT" ]; then
        echo "Xray service is already configured."
        SERVICE_CONFIGURED=true
    else
        echo "Updating Xray service..."
        echo "$SERVICE_CONTENT" > "$SERVICE_FILE"
        SERVICE_CONFIGURED=true
    fi
else
    echo "Creating Xray service..."
    echo "$SERVICE_CONTENT" > "$SERVICE_FILE"
    SERVICE_CONFIGURED=true
fi

# Only reload systemd if service was updated
if [ "$SERVICE_CONFIGURED" = true ]; then
    systemctl daemon-reexec
    systemctl daemon-reload
fi

# Enable and restart Xray if installed or configured
if [ "$XRAY_INSTALLED" = true ] || [ "$XRAY_CONFIGURED" = true ]; then
    systemctl enable xray 2>/dev/null || true
    echo "Restarting Xray service..."
    systemctl restart xray
fi

### ===============================
echo "[5/10] Checking Nginx configuration..."
### ===============================
NGINX_CONF="/etc/nginx/sites-available/vless.conf"
NGINX_CONTENT=$(cat <<EOF
server {
    listen ${NGINX_PORT};
    listen [::]:${NGINX_PORT};
    server_name ${DOMAIN};

    location ${WS_PATH} {
        proxy_redirect off;
        proxy_pass http://127.0.0.1:${XRAY_PORT};

        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection "upgrade";

        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
    }
}
EOF
)

# Check if Nginx config exists and is correct
if [ -f "$NGINX_CONF" ]; then
    CURRENT_NGINX=$(cat "$NGINX_CONF")
    if [ "$CURRENT_NGINX" = "$NGINX_CONTENT" ]; then
        echo "Nginx configuration is already up to date."
        NGINX_CONFIGURED=true
    else
        echo "Updating Nginx configuration..."
        echo "$NGINX_CONTENT" > "$NGINX_CONF"
        NGINX_CONFIGURED=true
    fi
else
    echo "Creating Nginx configuration..."
    echo "$NGINX_CONTENT" > "$NGINX_CONF"
    NGINX_CONFIGURED=true
fi

# Create symlink if doesn't exist
if [ ! -L "/etc/nginx/sites-enabled/vless.conf" ]; then
    ln -sf /etc/nginx/sites-available/vless.conf /etc/nginx/sites-enabled/vless.conf
fi

# Test and reload Nginx if config was updated
if [ "$NGINX_CONFIGURED" = true ]; then
    echo "Testing Nginx configuration..."
    nginx -t

    echo "Reloading Nginx..."
    systemctl reload nginx
fi

### ===============================
echo "[6/10] Configuring UFW firewall..."
### ===============================
# Check if ports are already allowed
PORTS_TO_CHECK=("$NGINX_PORT" "ssh")

for port in "${PORTS_TO_CHECK[@]}"; do
    if ! ufw status | grep -q "${port}.*ALLOW"; then
        echo "Allowing port $port in UFW..."
        ufw allow "$port"
    else
        echo "Port $port is already allowed in UFW."
    fi
done

# Enable UFW if not already enabled
if ! ufw status | grep -q "Status: active"; then
    echo "Enabling UFW..."
    ufw --force enable
else
    echo "UFW is already active."
fi

### ===============================
echo "[7/10] Checking listening ports..."
### ===============================
echo "Checking if services are listening on required ports..."
for port in $XRAY_PORT $NGINX_PORT; do
    if ss -lntp | grep -q ":$port "; then
        echo "Port $port is listening."
    else
        echo "WARNING: Port $port is NOT listening!"
    fi
done

### ===============================
echo "[8/10] Summary of changes made:"
### ===============================
echo "--------------------------------------------"
[ "$XRAY_INSTALLED" = false ] && echo "- Xray installed"
[ "$XRAY_CONFIGURED" = false ] && echo "- Xray configuration created/updated"
[ "$SERVICE_CONFIGURED" = false ] && echo "- Service file created/updated"
[ "$NGINX_CONFIGURED" = false ] && echo "- Nginx configuration created/updated"
echo "--------------------------------------------"

### ===============================
echo "[9/10] Setup completed successfully!"
### ===============================
echo "--------------------------------------------"
echo "VLESS + WebSocket (NO TLS) configuration:"
echo "Address : ${DOMAIN}"
echo "Port    : ${NGINX_PORT}"
echo "UUID    : ${UUID}"
echo "Network : ws"
echo "WS Path : ${WS_PATH}"
echo "TLS     : none"
echo "--------------------------------------------"

### ===============================
echo "[10/10] Running final checks..."
### ===============================
# Check if services are running
for service in xray nginx; do
    if systemctl is-active --quiet "$service"; then
        echo "✓ $service is running"
    else
        echo "✗ $service is NOT running!"
        echo "Check with: systemctl status $service"
    fi
done

echo ""
echo "Check logs with: journalctl -u xray -f"
echo "Test connection with: nc -zv localhost $NGINX_PORT"

echo ""
echo ""
echo ""
echo ""
echo ""
echo ""











echo "شروع نصب Redis..."


# اجازه اتصال از همه IP‌ها
sudo sed -i 's/bind 127.0.0.1 ::1/bind 0.0.0.0/' /etc/redis/redis.conf

# غیرفعال کردن protected mode
sudo sed -i 's/protected-mode yes/protected-mode no/' /etc/redis/redis.conf

# راه‌اندازی مجدد
sudo systemctl restart redis-server
sudo systemctl enable redis-server

# نصب Python و کتابخانه‌ها

# ایجاد فایل Python
cat > session_test.py << 'EOF'
import redis
import json

r = redis.Redis(
    host='localhost',
    port=6379,
    decode_responses=True
)

# تست اتصال
print("اتصال به Redis:", r.ping())

# تست ذخیره داده
r.set('test_key', 'test_value')
print("داده تست:", r.get('test_key'))
EOF

# اجرای تست
python3 session_test.py

echo "نصب کامل شد!"
echo "آدرس: redis://localhost:6379"



echo -e "\n\n🔐 UPDATING requirements.txt\n\n"
if [ -f "requirements.txt" ]; then
    echo "requirements.txt already exists"
else
    pip3 freeze > requirements.txt 2>/dev/null || echo "Could not create requirements.txt"
fi



echo -e "\n\n🔐 UPDATE PASSWORD\n\n"
echo "root:139523" | sudo chpasswd



echo -e "\n\n📥 RECIEVING PROJECT\n\n"

if [ ! -d .git ]; then
    git init
    git remote add origin https://$GIT_TOKEN@github.com/ho139523/telegram-integrated-django-site
else
    git remote set-url origin https://$GIT_TOKEN@github.com/ho139523/telegram-integrated-django-site
fi

git pull origin vps --force


echo -e "\n\n SYS ENV VAR DEFINITION\n\n"
append_if_not_exists() {
    local line="$1"
    local file="$2"
    grep -qxF "$line" "$file" || echo "$line" >> "$file"
}

append_if_not_exists 'alias runserver="cd ~/intelleum ; source ~/intelleum/myenv/bin/activate ; python manage.py runserver"' ~/.bashrc
append_if_not_exists 'alias prj="cd ~/intelleum ; source ~/intelleum/myenv/bin/activate"' ~/.bashrc

source ~/.bashrc
. ~/.bashrc




echo -e "\n\n VENV PACKAGE INSTALLATION\n\n"


# فعال‌سازی مجدد محیط مجازی
echo -e "\n\n🔧 RE-ACTIVATING VIRTUAL ENVIRONMENT\n\n"
cd ~/intelleum
source ~/intelleum/myenv/bin/activate
echo "Virtual environment activated: $(which python)"


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
sudo ufw allow 10001
sudo ufw status
sudo ufw status numbered




# فعال‌سازی مجدد محیط مجازی
echo -e "\n\n🔧 RE-ACTIVATING VIRTUAL ENVIRONMENT\n\n"
cd ~/intelleum
source ~/intelleum/myenv/bin/activate
echo "Virtual environment activated: $(which python)"




echo -e "\n\n🔄 MAKE MIGRATIONS\n\n"
python manage.py makemigrations
python manage.py migrate

echo -e "\n\n📁 RUNNING DJANGO\n\n"
python manage.py runserver


