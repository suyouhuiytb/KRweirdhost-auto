import os
import requests
from bs4 import BeautifulSoup
import urllib.parse

# ========== 配置 ==========
USERNAME   = os.getenv("WH_USERNAME")
PASSWORD   = os.getenv("WH_PASSWORD")
TG_TOKEN   = os.getenv("TG_BOT_TOKEN")
TG_CHAT_ID = os.getenv("TG_CHAT_ID")

if not all([USERNAME, PASSWORD, TG_TOKEN, TG_CHAT_ID]):
    print("错误：缺少必要环境变量")
    exit(1)

login_url  = "https://hub.weirdhost.xyz/auth/login"
server_url = "https://hub.weirdhost.xyz/server/80982fa5"

session = requests.Session()
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
}

def tg_send(text):
    """发送Telegram消息（自动转义）"""
    url = f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage"
    payload = {
        "chat_id": TG_CHAT_ID,
        "text": text,
        "parse_mode": "HTML",
        "disable_web_page_preview": True
    }
    try:
        requests.post(url, data=payload, timeout=10)
    except:
        pass  # 防止TG失败导致整个任务挂

tg_send("WeirdHost 自动续期开始运行")

# Step 1: 登录（已处理确认/条款复选框）
login_page = session.get(login_url, headers=headers)
soup = BeautifulSoup(login_page.text, "html.parser")

csrf_token = soup.find("input", {"name": "_token"})["value"] if soup.find("input", {"name": "_token"}) else ""

login_data = {
    "_token": csrf_token,
    "email": USERNAME,
    "password": PASSWORD,
}

# 自动勾选可能的确认复选框
for cb in soup.find_all("input", {"type": "checkbox"}):
    name = cb.get("name")
    if name and any(k in name.lower() for k in ["term","agree","confirm","check"]):
        login_data[name] = "on"

resp = session.post(login_url, data=login_data, headers=headers, allow_redirects=True)

if "dashboard" not in resp.url and "server" not in resp.url:
    msg = "登录失败！账号密码可能错误或触发验证码"
    tg_send(f"<b>续期失败</b>\n{msg}")
    print(msg)
    exit(1)

tg_send("登录成功，正在尝试续期...")

# Step 2: 访问服务器页面
server_page = session.get(server_url, headers=headers)
soup = BeautifulSoup(server_page.text, "html.parser")

# Step 3: 提交续期
renew_form = soup.find("form", action=lambda x: x and "renew" in x)
if not renew_form:
    tg_send("<b>续期失败</b>\n未找到续期表单，服务器可能已过期或页面改版")
    exit(1)

renew_url = "https://hub.weirdhost.xyz" + renew_form["action"]
renew_data = {"_token": soup.find("input", {"name": "_token"})["value"]}

renew_resp = session.post(renew_url, data=renew_data, headers=headers)

resp_text = renew_resp.text

if "You can't renew your server currently" in resp_text:
    tg_send("<b>冷却中</b>\nYou can't renew your server currently,\nbecause you can only once at one time period.\n\n明天同一时间再试就会成功")
elif "시간이 추가되었습니다" in resp_text or "successfully" in resp_text.lower():
    tg_send("<b>续期成功！</b>\n服务器时间已成功延长")
else:
    tg_send(f"<b>未知结果，请手动检查</b>\n响应片段：\n<code>{resp_text[:600]}</code>")

print("任务完成，通知已发送")
