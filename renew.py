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
                    await client.post(
                        f"https://api.telegram.org/bot{TG_TOKEN}/sendPhoto",
                        data={"chat_id": TG_CHAT_ID, "caption": text, "parse_mode": "HTML"},
                        files={"photo": f}
                    )
            elif text:
                await client.post(
                    f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage",
                    data={"chat_id": TG_CHAT_ID, "text": text, "parse_mode": "HTML"}
                )
    except:
        pass

async def main():
    await tg_send("WeirdHost 续期开始运行")

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(viewport={"width": 1400, "height": 900})
        page = await context.new_page()

        await page.add_init_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined});")

        try:
            await page.goto("https://hub.weirdhost.xyz/auth/login", timeout=90000)
            await page.wait_for_load_state("networkidle", timeout=90_000)

            # 狂点所有确认按钮
            for txt in ["확인", "Confirm", "OK", "확인하기"]:
                try:
                    while await page.get_by_text(txt).count() > 0:
                        await page.get_by_text(txt).first.click(force=True, timeout=5000)
                        await asyncio.sleep(1)
                except: pass

            # 填写账号密码（兼容 username 和 email 两种情况）
            await page.fill("input[name='username'], input[name='email'], input[type='text']", USERNAME)
            await page.fill("input[name='password'], input[type='password']", PASSWORD)
            await page.click("button:has-text('로그인'), button[type='submit']")
            await asyncio.sleep(8)

            if "dashboard" in page.url or "server" in page.url:
                await tg_send("登录成功！正在续期")
                await page.goto("https://hub.weirdhost.xyz/server/80982fa5", timeout=60000)

                for _ in range(15):
                    if await page.get_by_text("시간추가").count() > 0:
                        await page.get_by_text("시간추가").click(force=True)
                        await asyncio.sleep(3)
                        break
                    await asyncio.sleep(1)

                content = await page.content()
                if "You can't renew" in content:
                    await tg_send("冷却中\n明天0点会自动成功")
                elif "시간이 추가되었습니다" in content:
                    await tg_send("续期成功！")
                else:
                    await page.screenshot(path="/tmp/result.png", full_page=True)
                    await tg_send("未知结果，已附截图", photo="/tmp/result.png")
            else:
                await page.screenshot(path="/tmp/fail.png", full_page=True)
                await tg_send("登录失败，已附截图", photo="/tmp/fail.png")

        except Exception as e:
            await page.screenshot(path="/tmp/error.png", full_page=True)
            await tg_send(f"脚本出错：{str(e)}\n已附截图", photo="/tmp/error.png")
        finally:
            await context.close()
            await browser.close()

asyncio.run(main())
