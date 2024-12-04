import os
import subprocess
import requests
import time
import re


# توکن ربات تلگرام
TOKEN = '7777543551:AAHJYYN3VwfC686y1Ir_aYewX1IzUMOlU68'

# تابع حذف وب‌هوک فعلی
def delete_webhook(token):
    url = f'https://api.telegram.org/bot{token}/deleteWebhook'
    params = {'drop_pending_updates': True}
    response = requests.post(url, data=params)
    print("Deleted webhook:", response.json())

# تابع تنظیم وب‌هوک جدید
def set_webhook(subdomain_url, token):
    webhook_url = f"{subdomain_url}/telbot/webhook/"
    url = f'https://api.telegram.org/bot{token}/setWebhook?url={webhook_url}'
    response = requests.get(url)
    print("Set webhook response:", response.json())

# تابع دریافت رمز عبور از LocalTunnel
def retrieve_tunnel_password():
    try:
        result = subprocess.run(
            ["curl", "-s", "https://loca.lt/mytunnelpassword"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        if result.returncode == 0:
            password = result.stdout.strip()
            print("Tunnel password retrieved using curl:", password)
            return password
        else:
            print("Failed to retrieve tunnel password using curl:", result.stderr)
            return None
    except Exception as e:
        print(f"Error retrieving tunnel password: {e}")
        return None

# اجرای سرور Django
django_command = ["python", "manage.py", "runserver", "127.0.0.1:8000"]
django_process = subprocess.Popen(django_command)
print("Django server is running at http://127.0.0.1:8000")
time.sleep(15)

# دریافت رمز عبور و اتصال به LocalTunnel
password = retrieve_tunnel_password()
if password:
    print("Tunnel password retrieved successfully.")

    localtunnel_command = f"echo {password} | lt --port 8000 --subdomain intelleum"
    localtunnel_process = subprocess.Popen(localtunnel_command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

    subdomain_url = None
    for _ in range(60):
        output = localtunnel_process.stdout.readline()
        if output:
            print("Localtunnel output:", output.strip())
            match = re.search(r'https?://\S+\.loca\.lt', output)
            if match:
                subdomain_url = match.group(0)
                break
        time.sleep(5)

    if subdomain_url:
        print("Localtunnel URL:", subdomain_url)
        delete_webhook(TOKEN)
        set_webhook(subdomain_url, TOKEN)
    else:
        print("Failed to retrieve Localtunnel URL.")
        localtunnel_process.terminate()
        django_process.terminate()
else:
    print("Tunnel password not available; unable to start tunnel.")

# ذخیره پیام آخرین کامیت
def get_last_commit_message():
    try:
        result = subprocess.run(
            ["git", "log", "-1", "--pretty=%s"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        if result.returncode == 0:
            return result.stdout.strip()
        else:
            print("Error retrieving last commit message:", result.stderr)
            return None
    except Exception as e:
        print(f"Error occurred retrieving last commit message: {e}")
        return None

# پوش کردن تغییرات به گیت‌هاب
def push_to_github(commit_message="Auto commit after stopping the script"):
    try:
        subprocess.run(["git", "add", "."], check=True)
        subprocess.run(["git", "commit", "-m", commit_message], check=True)
        subprocess.run(["git", "push", "origin", "master"], check=True)
        print("Changes pushed to GitHub successfully.")
    except subprocess.CalledProcessError as e:
        print("Error pushing changes to GitHub:", e)

# مدیریت فرآیندها
try:
    django_process.wait()
    localtunnel_process.wait()
except KeyboardInterrupt:
    django_process.terminate()
    localtunnel_process.terminate()
    print("Processes terminated.")

    # ارسال تغییرات به گیت‌هاب پس از توقف اسکریپت
    print("Last commit message:", get_last_commit_message())
    push_to_github(commit_message=input("Please enter your commit message: "))