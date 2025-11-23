import os
import asyncio
from playwright.async_api import async_playwright

USERNAME = os.environ["WH_USERNAME"]
PASSWORD = os.environ["WH_PASSWORD"]
TG_TOKEN = os.environ["TG_BOT_TOKEN"]
TG_CHAT_ID = os.environ["TG_CHAT_ID"]

async def tg_send(text):
    try:
        import httpx
        await httpx.AsyncClient(timeout=15).post(
            f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage",
            data={"chat_id": TG_CHAT_ID, "text": text, "parse_mode": "HTML"}
        )
    except: pass

async def main():
    await tg_send("WeirdHost 续期启动（韩国 vless 节点）")

    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=True,
            proxy={"server": "socks5://127.0.0.1:10809"}  # 强制走你的韩国节点
        )
        page = await browser.new_page()

        try:
            await page.goto("https://hub.weirdhost.xyz/auth/login", timeout=60000)
            await page.wait_for_load_state("networkidle", timeout=60000)

            # 勾选条款（直接点页面上唯一的 checkbox）
            await page.check("input[type=checkbox]", force=True)

            await page.fill("input[name='username'], input[name='email']", USERNAME)
            await page.fill("input[name='password']", PASSWORD)
            await page.click("button:has-text('로그인')")
            await asyncio.sleep(6)

            await page.goto("https://hub.weirdhost.xyz/server/80982fa5")
            await page.click("text=시간추가")
            await asyncio.sleep(3)

            content = await page.content()
            if "You can't renew" in content:
                await tg_send("冷却中\n明天自动续")
            else:
                await tg_send("续期成功！服务器时间已延长")

        except Exception as e:
            await page.screenshot(path="/tmp/err.png", full_page=True)
            await tg_send(f"出错：{e}")
        finally:
            await browser.close()

asyncio.run(main())
