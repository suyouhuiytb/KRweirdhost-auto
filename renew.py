import os
import asyncio
from playwright.async_api import async_playwright

USERNAME   = os.environ["WH_USERNAME"]
PASSWORD   = os.environ["WH_PASSWORD"]
TG_TOKEN   = os.environ["TG_BOT_TOKEN"]
TG_CHAT_ID = os.environ["TG_CHAT_ID"]

async def tg_send(text, photo=None):
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
            else:
                await client.post(
                    f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage",
                    data={"chat_id": TG_CHAT_ID, "text": text, "parse_mode": "HTML"}
                )
    except:
        pass

async def main():
    await tg_send("WeirdHost 续期启动")

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(viewport={"width": 1400, "height": 900})
        page = await context.new_page()

        # 伪装成真实用户
        await page.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
            Object.defineProperty(navigator, 'languages', {get: () => ['ko-KR', 'ko', 'en']});
        """)

        try:
            for attempt in range(1, 4):
                await tg_send(f"第 {attempt} 次尝试登录...")
                await page.goto("https://hub.weirdhost.xyz/auth/login", timeout=90000)

                # 等 Cloudflare 过
                await page.wait_for_load_state("networkidle", timeout=90000)

                # 狂点所有“확인 / Confirm / OK”
                for txt in ["확인", "Confirm", "OK", "OK", "확인하기"]:
                    try:
                        while await page.get_by_text(txt).count() > 0:
                            await page.get_by_text(txt).first.click(force=True, timeout=5000)
                            await asyncio.sleep(1)
                    except:
                        pass

                # 填写用户名密码（兼容 username 或 email 字段）
                await page.fill("input[name='username'], input[name='email'], input[type='text']", USERNAME, timeout=15000)
                await page.fill("input[name='password'], input[type='password']", PASSWORD, timeout=10000)

                # 点击登录按钮
                await page.click("button:has-text('로그인'), button[type='submit'], input[type='submit']", timeout=10000)
                await asyncio.sleep(8)

                # 判断是否登录成功
                if "dashboard" in page.url or "server" in page.url:
                    await tg_send("登录成功！正在续期...")
                    await page.goto("https://hub.weirdhost.xyz/server/80982fa5", timeout=60000)

                    # 狂点“시간추가”
                    for _ in range(15):
                        if await page.get_by_text("시간추가").count() > 0:
                            await page.get_by_text("시간추가").click(force=True)
                            await asyncio.sleep(3)
                            break
                        await asyncio.sleep(1)

                    content = await page.content()
                    if "You can't renew your server currently" in content:
                        await tg_send("冷却中\n明天同一时间段只能续一次，明天0点自动成功")
                    elif "시간이 추가되었습니다" in content:
                        await tg_send("续期成功！\n服务器时间已延长")
                    else:
                        await page.screenshot(path="/tmp/last_screenshot.png", full_page=True)
                        await tg_send("未知结果（附截图）", photo="/tmp/last_screenshot.png")
                    return

                else:
                    # 没登录成功，发截图重试
                    await page.screenshot(path=f"/tmp/attempt{attempt}.png", full_page=True)
                    await tg_send(f"第{attempt}次失败（附截图）", photo=f"/tmp/attempt{attempt}.png")

            await tg_send("三次全失败了\n请手动去 https://hub.weirdhost.xyz 登录看看是不是被风控了")

        except Exception as e:
            await page.screenshot(path="/tmp/last_screenshot.png", full_page=True)
            await tg_send(f"脚本异常：{str(e)}\n附最终截图", photo="/tmp/last_screenshot.png")

        finally:
            await context.close()
            await browser.close()

asyncio.run(main())
