import requests
import sys
import argparse
 
TOKEN = '7777543551:AAHJYYN3VwfC686y1Ir_aYewX1IzUMOlU68'
 
sub=''
 
WEBHOOK_URL = f"https://{sub}.serveo.net/webhook/"
 
def delete(TOKEN=TOKEN):
    url = f'https://api.telegram.org/bot{TOKEN}/deleteWebhook'
    params = { 'drop_pending_updates': True}
    response = requests.post(url, data=params)
    print(response.json())

def setting(sub, TOKEN=TOKEN):
    delete(TOKEN=TOKEN)
    TOKEN = str(TOKEN)
    WEBHOOK_URL = f"https://{sub}.serveo.net/webhook/"
    response = requests.get(f"https://api.telegram.org/bot{TOKEN}/setWebhook?url={WEBHOOK_URL}")
    print(response.json())


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run setting with a sub value.")
    parser.add_argument('--sub', required=True, help="Sub value for the setting function")
    args = parser.parse_args()

    # Call the function with the parsed argument
    setting(sub=args.sub)

    
    
# python run.py --sub 6733d262deb60d833b185c6e28142008
# ssh -R 80:127.0.0.1:8000 serveo.net

