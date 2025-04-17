import subprocess
import paramiko
import requests
import re
import time
import os

# فعال‌سازی محیط مجازی
myenv_path = "C:/Users/asus/Desktop/petroleum/GUI/myenv/Scripts/activate"
activate_env_command = f"{myenv_path} && "

# توکن تلگرام
TOKEN = 'YOUR_TELEGRAM_TOKEN'

def delete_webhook(token):
    url = f'https://api.telegram.org/bot{token}/deleteWebhook'
    params = {'drop_pending_updates': True}
    response = requests.post(url, data=params)
    print("Deleted webhook:", response.json())

def set_webhook(subdomain, token):
    webhook_url = f"https://{subdomain}.serveo.net/webhook/"
    url = f'https://api.telegram.org/bot{token}/setWebhook?url={webhook_url}'
    response = requests.get(url)
    print("Set webhook response:", response.json())

# تنظیمات اتصال SSH به Serveo
host = "serveo.net"
port = 22
local_host = "127.0.0.1"
local_port = 8000
username = "root"  # برای Serveo معمولاً "root" کافی است.
private_key_path = "C:/Users/asus/Desktop/petroleum/GUI/.ssh/myssh"

# ایجاد SSHClient و تنظیمات کلید خصوصی
client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

try:
    # بارگذاری کلید خصوصی
    key = paramiko.RSAKey.from_private_key_file(private_key_path)

    # اتصال به سرور Serveo
    client.connect(hostname=host, port=port, key_filename=private_key_path)

    # ایجاد فوروارد پورت
    transport = client.get_transport()
    channel = transport.open_channel("direct-tcpip", (local_host, local_port), (host, 80))
    print("Serveo tunnel created successfully.")

    # دریافت زیر دامنه از Serveo
    serveo_output = transport.get_banner().decode()
    match = re.search(r'Forwarding HTTP traffic from https://(.*)\.serveo\.net', serveo_output)
    if not match:
        print("Failed to retrieve Serveo subdomain.")
        client.close()
        exit(1)

    subdomain = match.group(1)
    print("Subdomain created:", subdomain)

    # حذف وبهوک قبلی و تنظیم وبهوک جدید
    delete_webhook(TOKEN)
    set_webhook(subdomain, TOKEN)

    # اجرای سرور جنگو در محیط مجازی
    django_command = f"{activate_env_command} python manage.py runserver {local_host}:{local_port}"
    django_process = subprocess.Popen(django_command, shell=True)
    print("Django server is running at http://127.0.0.1:8000")

    # نگه داشتن برنامه تا Ctrl+C زده شود
    while True:
        time.sleep(1)

except Exception as e:
    print("Error creating Serveo tunnel:", e)

finally:
    client.close()
    if 'django_process' in locals():
        django_process.terminate()
    print("Processes terminated.")
