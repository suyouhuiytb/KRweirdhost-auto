import os
import asyncio
from playwright.async_api import async_playwright

USERNAME   = os.environ["WH_USERNAME"]
PASSWORD   = os.environ["WH_PASSWORD"]
TG_TOKEN   = os.environ["TG_BOT_TOKEN"]
TG_CHAT_ID = os.environ["TG_CHAT_ID"]

async def tg_send(text="", photo=None):
    try:
        import httpx
        async with httpx.AsyncClient(timeout=20) as client:
            if photo and os.path.exists(photo):
                with open(photo, "rb") as f:
                    await client.post(f"https://api.telegram.org/bot{TG_TOKEN}/sendPhoto",
                                      data={"chat_id": TG_CHAT_ID, "caption": text, "parse_mode": "HTML"},
                                      files={"photo": f})
            elif text:
                await client.post(f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage",
                                  data={"chat_id": TG_CHAT_ID, "text": text, "parse_mode": "HTML"})
    except: pass

async def main():
    await tg_send("WeirdHost 续期开始运行（条款升级版）")

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await (await browser.new_context(viewport={"width":1400,"height":900})).new_page()

        await page.add_init_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined});")

        try:
            await page.goto("https://hub.weirdhost.xyz/auth/login", timeout=90000)
            await page.wait_for_load_state("networkidle", timeout=90000)

            # 升级：模糊匹配所有含“동의”（同意）的 checkbox / label，强制点击
            terms_selectors = [
                "input[type=checkbox]",  # 直接点页面上所有 checkbox（登录页只有一个）
                "label:has-text('동의')",  # 含“동의”的标签
                "text=동의합니다",  # 通用同意文本
                "#terms, #agree, input[name='terms'], input[name='agree']",  # 常见 ID/name
            ]
            for selector in terms_selectors:
                try:
                    if await page.locator(selector).count() > 0:
                        await page.check(selector, force=True, timeout=5000)
                        print(f"已勾选条款：{selector}")
                        break
                except: pass

            # 填写账号密码
            await page.fill("input[name='username'], input[name='email'], input[type='text']", USERNAME, timeout=15000)
            await page.fill("input[name='password'], input[type='password']", PASSWORD, timeout=10000)

            # 点击登录
            await page.click("button:has-text('로그인'), button[type='submit']", timeout=10000)
            await asyncio.sleep(6)

            if "dashboard" not in page.url and "server" not in page.url:
                await page.screenshot(path="/tmp/login_failed.png", full_page=True)
                await tg_send("登录还是失败（附最新截图）", photo="/tmp/login_failed.png")
                return

            await tg_send("✅ 登录成功！正在续期")
            await page.goto("https://hub.weirdhost.xyz/server/80982fa5", timeout=60000)

            # 等待并点击时间추가
            await page.wait_for_selector("text=시간추가", state="visible", timeout=30000)
            await page.click("text=시간추가", force=True)

            await asyncio.sleep(3)
            content = await page.content()

            if "You can't renew your server currently" in content:
                await tg_send("⏳ 冷却中\n一天只能续一次，明天0点自动成功！")
            elif "시간이 추가되었습니다" in content or "renewed" in content.lower():
                await tg_send("🎉 续期成功！\n服务器时间已延长 🎮")
            else:
                await page.screenshot(path="/tmp/result.png", full_page=True)
                await tg_send("❓ 未知结果（附截图）", photo="/tmp/result.png")

        except Exception as e:
            await page.screenshot(path="/tmp/error.png", full_page=True)
            await tg_send(f"脚本异常：{str(e)}\n附截图", photo="/tmp/error.png")
        finally:
            await page.context.close()
            await browser.close()

asyncio.run(main())
