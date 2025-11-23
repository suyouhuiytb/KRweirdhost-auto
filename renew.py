import os, asyncio, sys
from playwright.async_api import async_playwright

U = os.environ["WH_USERNAME"]
P = os.environ["WH_PASSWORD"]
TG = os.environ["TG_BOT_TOKEN"]
CID = os.environ["TG_CHAT_ID"]

async def tg(text):
    try:
        import httpx
        await httpx.AsyncClient().post(f"https://api.telegram.org/bot{TG}/sendMessage",
            data={"chat_id": CID, "text": text, "parse_mode": "HTML"}, timeout=10)
    except: pass

async def main():
    await tg("WeirdHost 续期启动（韩国节点强制代理版）")
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=True,
            args=[
                "--proxy-server=http://127.0.0.1:10808",   # 强制走韩国代理
                "--no-sandbox",
                "--disable-gpu",
                "--lang=ko-KR"
            ]
        )
        page = await browser.new_page()
        try:
            await page.goto("https://hub.weirdhost.xyz/auth/login", timeout=60000)
            await page.wait_for_load_state("networkidle", timeout=60000)

            await page.check("input[type=checkbox]", force=True)
            await page.fill("input[name='username'], input[name='email']", U)
            await page.fill("input[name='password']", P)
            await page.click("button:has-text('로그인')")
            await asyncio.sleep(6)

            await page.goto("https://hub.weirdhost.xyz/server/80982fa5")
            await page.click("text=시간추가")
            await asyncio.sleep(4)

            if "You can't renew" in await page.content():
                await tg("冷却中\n明天0点自动成功")
            else:
                await tg("续期成功！\n服务器时间已延长 24h")
        except Exception as e:
            await page.screenshot(path="/tmp/err.png", full_page=True)
            await tg(f"出错：{e}\n已截图")
        finally:
            await browser.close()
    await tg("任务结束")

asyncio.run(main())
