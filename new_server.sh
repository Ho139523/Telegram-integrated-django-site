echo "🔄 آپدیت سیستم..."
apt-get update
apt-get upgrade -y


echo "📦 نصب بسته‌های ضروری..."
sudo apt install -y nginx v2ray python3 git python3.12-venv
echo -e "139523\n139523" | passwd root ; sudo apt install tmux -y ; sudo apt install v2ray -y ; sudo apt install nginx -y ; mkdir intelleum ; cd ~/intelleum ; git init ; git remote add origin https://github.com/ho139523/telegram-integrated-django-site ; git remote -v ; git pull origin master ; ls -a
