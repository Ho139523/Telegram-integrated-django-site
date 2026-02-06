import requests
import sys
import argparse
 
TOKEN = "8019448982:AAEW-sHSuIqd2BaL5qM8rSlVPkP9eoTLRIM"
sub=''
from utils.variables.TOKEN import TOKEN
from AI.settings import current_site
WEBHOOK_URL = f"{current_site}/telbot/webhook/"
 
def delete(TOKEN=TOKEN):
    url = f'https://api.telegram.org/bot{TOKEN}/deleteWebhook'
    params = { 'drop_pending_updates': True}
    response = requests.post(url, data=params)
    print(response.json())

from utils.variables.TOKEN import TOKEN
print(TOKEN)
def setting(sub, TOKEN=TOKEN):
    delete(TOKEN=TOKEN)
    TOKEN = str(TOKEN)
    response = requests.get(f"https://api.telegram.org/bot{TOKEN}/setWebhook?url={WEBHOOK_URL}")
    print(response.json())


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run setting with a sub value.")
    parser.add_argument('--sub', required=False, help="Sub value for the setting function")
    args = parser.parse_args()

    # Call the function with the parsed argument
    setting(sub=args.sub)

    
    
#python run.py --sub 68164854bca01acd9751cb28007ceb4a
#ssh -R 80:127.0.0.1:8000 serveo.net
#
#sudo pkill -9 python
#
#
###########################

# قطع تمام فرآیندهای xrdp کاربر جاری
#pkill -u $(whoami) xrdp
#pkill -u $(whoami) Xorg
#
############################
#
#sudo ss -tulnp | grep ':8000'
#
#gunicorn --bind 127.0.0.1:8000 AI.wsgi:application --access-logfile -
#
#proot-distro login ubuntu
#
#cloudflared tunnel run intelleum
#
#############################
#
#ssh -p 45677 hussein2079@37.148.9.135
#clear
#   cd /home/hussein2079/Desktop/intelleum && source /home/hussein2079/Desktop/intelleum/myenv/bin/activate && proxychains python manage.py runserver
#
#############################
#
#cd /storage/emulated/0/fonts
#pipenv shell
#git pull origin master
#clear
#
#############################
#
#git commit -a -m "update"
#git push origin master
#
#############################
#
#sudo systemctl daemon-reload
#sudo systemctl restart uwsgi
#tail -n 50 /var/log/uwsgi/ai.log
#
#############################
#
#setxkbmap -layout us,ir -option grp:alt_shift_toggle
#
#############################
#
#sudo -n 50 cat /var/log/uwsgi/django.log
#sudo cat /var/log/uwsgi/ai-error.log
#sudo journalctl -u pull.service -f
#
#############################
#
#uvicorn AI.asgi:application --host 0.0.0.0 --port 8000 --reload



# SSL RENEWAL

# عالی حسین ✅
# خب، چون پورت 80/443 بسته است، بهترین روش DNS-01 Challenge با Cloudflare API هست تا SSL روی سرور 8443 مستقیم بگیری و Cloudflare هم روی DNS only باشه.

# قدم‌به‌قدم راه‌اندازی Certbot با DNS-01 و Cloudflare
# 1️⃣ گرفتن API Token از Cloudflare

# وارد حساب Cloudflare شو.

# به My Profile → API Tokens برو.

# روی Create Token کلیک کن.

# از Template: Edit zone DNS استفاده کن.

# دامنه مورد نظر (intelleum.ir) رو انتخاب کن و Permission: Zone → DNS → Edit بده.

# Token ساخته می‌شه، اون رو جایی امن نگه دار.

# مثال اسم فایل Credential در سرور:

# ~/.secrets/cf.ini


# dns_cloudflare_api_token = <API_TOKEN>


# chmod 600 ~/.secrets/cf.ini


# sudo apt update
# sudo apt install python3-certbot-dns-cloudflare -y


# گرفتن گواهی SSL با DNS Challenge

# sudo certbot certonly \
#   --dns-cloudflare \
#   --dns-cloudflare-credentials ~/.secrets/cf.ini \
#   -d intelleum.ir


# sudo nginx -t
# sudo systemctl restart nginx


# تمدید اتوماتیک

# برای تمدید اتوماتیک Certbot با DNS-01 و Cloudflare، کافیه همین cron job رو داشته باشی:

# sudo crontab -e


# و اضافه کن:

# 0 0 * * * certbot renew --quiet --dns-cloudflare --dns-cloudflare-credentials /home/<username>/.secrets/cf.ini


# هر روز نیمه شب چک می‌کنه و اگر نزدیک به انقضا بود، تمدید می‌کنه.


