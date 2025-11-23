import os
import requests
from bs4 import BeautifulSoup
import time

# ========= 你只需要在 GitHub Secrets 里填这两个 =========
USERNAME = os.getenv("WH_USERNAME")
PASSWORD = os.getenv("WH_PASSWORD")

if not USERNAME or not PASSWORD:
    print("错误：请在 GitHub Secrets 中设置 WH_USERNAME 和 WH_PASSWORD")
    exit(1)

login_url = "https://hub.weirdhost.xyz/auth/login"
server_url = "https://hub.weirdhost.xyz/server/80982fa5"
session = requests.Session()

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/130 Safari/537.36"
}

# Step 1: 登录 - 新增：处理确认按钮/复选框
print("正在登录 WeirdHost...")
login_page = session.get(login_url, headers=headers)
soup = BeautifulSoup(login_page.text, "html.parser")

# 提取 CSRF token
token = soup.find("input", {"name": "_token"})
csrf_token = token["value"] if token else ""

# 基础登录数据
login_data = {
    "_token": csrf_token,
    "email": USERNAME,        # WeirdHost 用 email 登录
    "password": PASSWORD,
}

# 新增：自动检测并处理确认元素（复选框或隐藏字段）
# 查找条款同意复选框（常见name: 'terms', 'agree', 'confirm' 或韩文）
checkbox = soup.find("input", {"type": "checkbox", "name": lambda n: n and ("terms" in n or "agree" in n or "confirm" in n or "확인" in n)})
if checkbox:
    login_data[checkbox["name"]] = "on"  # 勾选 = 发送 'on'
    print(f"已自动勾选确认复选框：{checkbox['name']}")

# 如果有单独的“确定”按钮表单，先“点击”它（POST到其action）
confirm_form = soup.find("form", string=lambda t: t and ("확인" in t or "确定" in t or "confirm" in t))
if confirm_form:
    confirm_url = confirm_form.get("action", login_url)
    confirm_data = {inp["name"]: inp.get("value", "") for inp in confirm_form.find_all("input")}
    # 提交确认（如果有token，也加）
    if csrf_token:
        confirm_data["_token"] = csrf_token
    session.post(confirm_url, data=confirm_data, headers=headers)
    print("已点击登录前确认按钮")
    # 重新获取登录页（以防重载）
    login_page = session.get(login_url, headers=headers)
    soup = BeautifulSoup(login_page.text, "html.parser")

resp = session.post(login_url, data=login_data, headers=headers)

if "dashboard" not in resp.url and resp.status_code != 200:
    print("登录失败！可能是账号密码错误、验证码，或确认步骤未处理")
    print("调试提示：手动登录浏览器，检查F12 Network标签，看登录POST数据。")
    print(resp.text[:500])
    exit(1)

print("登录成功！（已处理确认步骤）")

# Step 2: 访问服务器页面
print("正在访问服务器页面...")
server_page = session.get(server_url, headers=headers)
soup = BeautifulSoup(server_page.text, "html.parser")

# Step 3: 找“시간추가”按钮对应的表单
renew_form = soup.find("form", {"action": lambda x: x and "renew" in x})
if not renew_form:
    print("未找到续期表单，页面可能已变更或服务器已过期")
    print(server_page.text[:1000])
    exit(1)

renew_url = "https://hub.weirdhost.xyz" + renew_form["action"]

# 构造续期数据
renew_data = {
    "_token": soup.find("input", {"name": "_token"})["value"]
}

print("正在提交续期请求...")
renew_resp = session.post(renew_url, data=renew_data, headers=headers)

if "You can't renew your server currently" in renew_resp.text:
    print("冷却中：You can't renew your server currently, because you can only once at one time period.")
    print("明天同一时间会再试一次，冷却结束就会自动续期成功")
elif "successfully" in renew_resp.text.lower() or "시간이 추가되었습니다" in renew_resp.text:
    print("续期成功！服务器时间已延长")
else:
    print("未知响应，请手动检查：")
    print(renew_resp.text[:800])

print("任务结束")
