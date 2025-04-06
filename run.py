import requests
import sys
import argparse
 
TOKEN = '7777543551:AAHJYYN3VwfC686y1Ir_aYewX1IzUMOlU68'
 
sub=''
 
WEBHOOK_URL = f"{sub}/webhook/"
 
def delete(TOKEN=TOKEN):
    url = f'https://api.telegram.org/bot{TOKEN}/deleteWebhook'
    params = { 'drop_pending_updates': True}
    response = requests.post(url, data=params)
    print(response.json())

def setting(sub, TOKEN=TOKEN):
    delete(TOKEN=TOKEN)
    TOKEN = str(TOKEN)
    WEBHOOK_URL = f"{sub}/telbot/webhook/"
    response = requests.get(f"https://api.telegram.org/bot{TOKEN}/setWebhook?url={WEBHOOK_URL}")
    print(response.json())


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run setting with a sub value.")
    parser.add_argument('--sub', required=True, help="Sub value for the setting function")
    args = parser.parse_args()

    # Call the function with the parsed argument
    setting(sub=args.sub)

    
    
# python run.py --sub 68164854bca01acd9751cb28007ceb4a
# ssh -R 80:127.0.0.1:8000 serveo.net

# sudo kill -9 nginx
# sudo kill $(sudo lsof -t -i :8443)

# # قطع تمام فرآیندهای xrdp کاربر جاری
# pkill -u $(whoami) xrdp
# pkill -u $(whoami) Xorg

# sudo ss -tulnp | grep ':80'

# gunicorn --bind 127.0.0.1:8000 AI.wsgi:application --access-logfile -

# proot-distro login ubuntu

# cloudflared tunnel run intelleum
