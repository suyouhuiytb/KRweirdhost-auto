import os
import asyncio
from playwright.async_api import async_playwright

USERNAME   = os.environ["WH_USERNAME"]
PASSWORD   = os.environ["WH_PASSWORD"]
TG_TOKEN   = os.environ["TG_BOT_TOKEN"]
TG_CHAT_ID = os.environ["TG_CHAT_ID"]

async def tg_send(text):
    url = f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage"
    try:
        import httpx
        await httpx.AsyncClient().post(url, data={
            "chat_id": TG_CHAT_ID,
            "text": text,
            "parse_mode": "HTML"
        }, timeout=10)
    except:
        pass

async def main():
    await tg_send("WeirdHost 续期开始（Playwright版）")

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        await page.set_viewport_size({"width": 1280, "height": 720})

        # 关键：伪装指纹，绕过 Cloudflare
        await page.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', {get: () => false});
            Object.defineProperty(navigator, 'languages', {get: () => ['ko-KR', 'ko', 'en-US', 'en']});
            Object.defineProperty(navigator, 'plugins', {get: () => [1, 2, 3]});
        """)

        try:
            await page.goto("https://hub.weirdhost.xyz/auth/login", wait_until="networkidle", timeout=30000)

            # 1. 如果有 Cloudflare 验证码，等它过（最多等30秒）
            await page.wait_for_load_state("networkidle")
            if "Just a moment" in await page.content() or "Checking your browser" in await page.content():
                print("检测到 Cloudflare，正在自动过...")
                await page.wait_for_url("**/dashboard**", timeout=60000)  # 最长等60秒

            # 2. 登录前必须点的“확인”弹窗或按钮（多次点击保险）
            for _ in range(3):
                if await page.locator("text=확인").count() > 0:
                    await page.locator("text=확인").first.click(timeout=5000)
                if await page.locator("text=Confirm").count() > 0:
                    await page.locator("text=Confirm").first.click(timeout=5000)

            # 3. 填写账号密码并登录
            await page.fill("input[name='email']", USERNAME)
            await page.fill("input[name='password']", PASSWORD)
            await page.click("button:has-text('Login'), button[type='submit']")
            await page.wait_for_load_state("networkidle")

            # 4. 判断是否真的登录成功
            if "dashboard" not in page.url and "server" not in page.url:
                await tg_send(f"<b>登录失败</b>\n可能是密码错或账号被封")
                await browser.close()
                return

            await tg_send("登录成功，正在续期...")

            # 5. 进入服务器页面并点击“시간추가”
            await page.goto("https://hub.weirdhost.xyz/server/80982fa5", wait_until="networkidle")

            # 多次尝试点击“시간추가”（可能要等一下才出现）
            for i in range(10):
                if await page.locator("text=시간추가").count() > 0:
                    await page.click("text=시간추가")
                    break
                await asyncio.sleep(2)
            else:
                await tg_send("<b>未找到“시간추가”按钮</b>\n服务器可能已彻底过期")
                await browser.close()
                return

            # 6. 判断结果
            await asyncio.sleep(3)
            content = await page.content()

            if "You can't renew your server currently" in content:
                await tg_send("<b>冷却中</b>\n只能一天续一次，明天0点再来就会成功")
            elif "시간이 추가되었습니다" in content or "successfully" in content.lower():
                await tg_send("<b>续期成功！</b>\n服务器时间已延长")
            else:
                await tg_send(f"<b>未知结果</b>\n请手动检查一下吧\n\n{content[:500]}")

        except Exception as e:
            await tg_send(f"<b>脚本异常</b>\n{str(e)}")
            raise
        finally:
            await browser.close()

asyncio.run(main())
