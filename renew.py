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
    await tg_send("WeirdHost 续期开始（反谷歌墙版）")

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            viewport={"width": 1400, "height": 900},
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15"
        )
        page = await context.new_page()

        # 加强反检测
        await page.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
            Object.defineProperty(navigator, 'plugins', {get: () => [1,2,3,4,5]});
            Object.defineProperty(navigator, 'languages', {get: () => ['ko-KR', 'ko', 'en-US', 'en']});
            window.chrome = {runtime: {}};
        """)

        try:
            await page.goto("https://hub.weirdhost.xyz/auth/login", timeout=120000)  # 延长加载

            # 关键：等 Cloudflare 挑战过（检测 "Just a moment..." 或 "Checking your browser"）
            cf_start = asyncio.get_event_loop().time()
            while asyncio.get_event_loop().time() - cf_start < 120:  # 最多等 2 分钟
                content = await page.content()
                if "Just a moment" in content or "Checking your browser" in content or "cf-browser-verification" in content:
                    await tg_send("🔄 检测到 Cloudflare 挑战，正在自动等待通过...")
                    await page.wait_for_load_state("networkidle", timeout=10000)
                    await asyncio.sleep(10)  # 每 10 秒检查一次
                else:
                    break
            await page.wait_for_load_state("networkidle", timeout=30000)

            # 勾选条款（模糊 + 多重保险）
            terms_selectors = [
                "input[type=checkbox]:not([disabled])",  # 所有可用 checkbox
                "label:has-text('동의') label:has-text('약관')",  # 含同意/条款的 label
                "#terms, #agree, [name*='terms'], [name*='agree']",  # 常见 name/id
            ]
            for selector in terms_selectors:
                try:
                    if await page.locator(selector).count() > 0:
                        await page.check(selector, force=True, timeout=10000)
                        await asyncio.sleep(1)
                        break
                except: pass

            # 填写账号密码
            await page.fill("input[name='username'], input[name='email'], input[type='text']:visible", USERNAME, timeout=15000)
            await page.fill("input[name='password'], input[type='password']:visible", PASSWORD, timeout=10000)

            # 点击登录
            await page.click("button:has-text('로그인'), button[type='submit']:not([disabled])", timeout=10000)
            await asyncio.sleep(8)

            # 检查登录
            if "dashboard" in page.url or "server" in page.url:
                await tg_send("✅ 登录成功！正在续期服务器...")
                await page.goto("https://hub.weirdhost.xyz/server/80982fa5", timeout=60000)
                await page.wait_for_load_state("networkidle", timeout=30000)

                # 点击时间추가
                await page.wait_for_selector("text=시간추가", timeout=30000)
                await page.click("text=시간추가", force=True)
                await asyncio.sleep(4)

                content = await page.content()
                if "You can't renew your server currently" in content:
                    await tg_send("⏳ 冷却中\n一天只能续一次，明天 00:00 自动成功！")
                elif any(msg in content for msg in ["시간이 추가되었습니다", "successfully renewed", "extended"]):
                    await tg_send("🎉 续期成功！\n服务器时间已延长 24 小时 🎮")
                else:
                    await page.screenshot(path="/tmp/result.png", full_page=True)
                    await tg_send("❓ 续期结果未知（附截图检查）", photo="/tmp/result.png")
            else:
                await page.screenshot(path="/tmp/login_failed.png", full_page=True)
                await tg_send("❌ 登录失败（附截图）\n可能密码错或账号风控", photo="/tmp/login_failed.png")

        except Exception as e:
            await page.screenshot(path="/tmp/error.png", full_page=True)
            await tg_send(f"💥 脚本异常：{str(e)[:200]}\n附截图", photo="/tmp/error.png")
        finally:
            await context.close()
            await browser.close()

asyncio.run(main())
