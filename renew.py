import os
import asyncio
import sys
from playwright.async_api import async_playwright

print("脚本启动，环境变量检查：")
print(f"用户名: {os.environ.get('WH_USERNAME', '未设置')[:3]}***")
print(f"TG Token: {os.environ.get('TG_BOT_TOKEN', '未设置')[:10]}***")

USERNAME = os.environ["WH_USERNAME"]
PASSWORD = os.environ["WH_PASSWORD"]
TG_TOKEN = os.environ["TG_BOT_TOKEN"]
TG_CHAT_ID = os.environ["TG_CHAT_ID"]

async def tg_send(text, photo=None):
    try:
        import httpx
        print(f"发送 TG: {text[:50]}...")
        async with httpx.AsyncClient(timeout=15) as client:
            if photo and os.path.exists(photo):
                with open(photo, "rb") as f:
                    await client.post(f"https://api.telegram.org/bot{TG_TOKEN}/sendPhoto",
                                      data={"chat_id": TG_CHAT_ID, "caption": text, "parse_mode": "HTML"},
                                      files={"photo": f})
            else:
                await client.post(f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage",
                                  data={"chat_id": TG_CHAT_ID, "text": text, "parse_mode": "HTML"})
        print("TG 发送成功")
    except Exception as e:
        print(f"TG 发送失败: {e}")

async def main():
    await tg_send("🔄 WeirdHost 续期启动（调试版）")

    async with async_playwright() as p:
        print("启动浏览器...")
        browser = await p.chromium.launch(headless=True, proxy={"server": "socks5://127.0.0.1:10809"})
        page = await browser.new_page()
        print("浏览器启动成功")

        try:
            print("访问登录页...")
            await page.goto("https://hub.weirdhost.xyz/auth/login", timeout=60000)
            await page.wait_for_load_state("networkidle", timeout=60000)
            print(f"登录页标题: {await page.title()}")

            # 勾选条款
            print("尝试勾选条款...")
            await page.check("input[type=checkbox]", force=True)
            print("条款勾选完成")

            # 填写表单
            print("填写用户名...")
            await page.fill("input[name='username'], input[name='email']", USERNAME)
            print("填写密码...")
            await page.fill("input[name='password']", PASSWORD)
            print("点击登录...")
            await page.click("button:has-text('로그인')")
            await asyncio.sleep(6)
            print(f"登录后 URL: {page.url}")

            if "dashboard" in page.url or "server" in page.url:
                await tg_send("✅ 登录成功！正在续期...")
                print("访问服务器页...")
                await page.goto("https://hub.weirdhost.xyz/server/80982fa5")
                print("点击时间추가...")
                await page.click("text=시간추가")
                await asyncio.sleep(3)

                content = await page.content()
                print(f"续期响应片段: {content[:200]}")
                if "You can't renew" in content:
                    await tg_send("⏳ 冷却中，明天自动成功")
                else:
                    await tg_send("🎉 续期成功！服务器时间已延长")
            else:
                screenshot = "/tmp/fail.png"
                await page.screenshot(path=screenshot, full_page=True)
                await tg_send("❌ 登录失败（附截图）", photo=screenshot)
                print("登录失败，截图保存")

        except Exception as e:
            print(f"脚本异常: {e}")
            screenshot = "/tmp/error.png"
            await page.screenshot(path=screenshot, full_page=True)
            await tg_send(f"💥 脚本出错：{str(e)}（附截图）", photo=screenshot)
        finally:
            await browser.close()
            print("浏览器关闭")

    await tg_send("任务结束（检查 GitHub 日志）")

if __name__ == "__main__":
    asyncio.run(main())
