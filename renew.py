import os
import asyncio
from playwright.async_api import async_playwright, TimeoutError as PWTimeout

USERNAME   = os.environ["WH_USERNAME"]
PASSWORD   = os.environ["WH_PASSWORD"]
TG_TOKEN   = os.environ["TG_BOT_TOKEN"]
TG_CHAT_ID = os.environ["TG_CHAT_ID"]

async def tg_send(text, photo=None):
    try:
        import httpx
        client = httpx.AsyncClient(timeout=15)
        if photo:
            files = {'photo': open(photo, 'rb')}
            await client.post(f"https://api.telegram.org/bot{TG_TOKEN}/sendPhoto",
                              data={"chat_id": TG_CHAT_ID, "caption": text, "parse_mode": "HTML"},
                              files=files)
        else:
            await client.post(f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage",
                              data={"chat_id": TG_CHAT_ID, "text": text, "parse_mode": "HTML"})
    except:
        pass

async def main():
    await tg_send("WeirdHost 续期开始运行（终极版）")

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            viewport={"width": 1366, "height": 768},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        )
        page = await context.new_page()

        # 绕过检测
        await page.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', {get: () => false});
            Object.defineProperty(navigator, 'languages', {get: () => ['ko-KR','ko','en']});
        """)

        try:
            # 多次重试机制
            for attempt in range(1, 4):
                print(f"第 {attempt} 次尝试...")
                await page.goto("https://hub.weirdhost.xyz/auth/login", wait_until="domcontentloaded", timeout=90000)

                # 等 Cloudflare 过
                try:
                    await page.wait_for_load_state("networkidle", timeout=60000)
                except:
                    pass

                # 狂点所有“확인”“Confirm”“OK”按钮
                for text in ["확인", "Confirm", "OK", "확인하기"]:
                    while await page.locator(f"text={text}").count() > 0:
                        await page.locator(f"text={text}").first.click(force=True, timeout=5000)

                # 尝试填写用户名（真实字段是 username，不是 email！）
                try:
                    await page.fill("input[name='username'], input#username, input[placeholder*='아이디'], input[placeholder*='Username']", USERNAME, timeout=10000)
                    await page.fill("input[name='password'], input#password", PASSWORD, timeout=10000)
                    await page.click("button:has-text('로그인'), button[type='submit'], input[type='submit']", timeout=10000)
                    await asyncio.sleep(5)

                    if "dashboard" in page.url or "server" in page.url:
                        await tg_send("登录成功！正在续期...")
                        break
                        await page.goto("https://hub.weirdhost.xyz/server/80982fa5", wait_until="networkidle", timeout=60000)
                        
                        # 狂点“시간추가”
                        for _ in range(15):
                            if await page.locator("text=시간추가").count() > 0:
                                await page.locator("text=시간추가").first.click(force=True)
                                await asyncio.sleep(3)
                                break
                            await asyncio.sleep(2)

                        content = await page.content()
                        if "You can't renew your server currently" in content:
                            await tg_send("<b>冷却中</b>\n只能一天续一次，明天0点自动成功")
                        elif "시간이 추가되었습니다" in content:
                            await tg_send("<b>续期成功！</b>\n服务器时间已延长")
                        else:
                            screenshot = "/tmp/result.png"
                            await page.screenshot(path=screenshot, full_page=True)
                            await tg_send("未知结果（已截图）", photo=screenshot)
                        return

                except PWTimeout:
                    await page.screenshot(path=f"/tmp/attempt{attempt}.png")
                    await tg_send(f"第 {attempt} 次尝试超时，已截图", photo=f"/tmp/attempt{attempt}.png")
                    await page.reload()
                    await asyncio.sleep(10)
                    continue

            await tg_send("<b>三次都失败了</b>\n可能账号被暂时封或者网站改版了，请手动登录看看")

        except Exception as e:
            await tg_send(f"<b>脚本崩溃</b>\n{str(e)}")
        finally:
            await context.close()
            await browser.close()

asyncio.run(main())
