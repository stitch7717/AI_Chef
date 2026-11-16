"""用本机 Edge 截取各页面（一次性脚本，不入库）。"""
import asyncio, pathlib
from playwright.async_api import async_playwright

OUT = pathlib.Path(r"D:/lc-course-pro/docs/screenshots"); OUT.mkdir(parents=True, exist_ok=True)
BASE = "http://127.0.0.1:8080"

async def login(page):
    await page.goto(BASE + "/login", wait_until="networkidle")
    await page.wait_for_timeout(500)
    ins = page.locator("input")
    await ins.nth(0).fill("admin")
    await ins.nth(1).fill("Admin@2026")
    await page.locator(".submit-btn").first.click()
    await page.wait_for_url("**/chat", timeout=20000)
    await page.wait_for_timeout(2500)

async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch(channel="msedge", headless=True)
        ctx = await b.new_context(viewport={"width": 1440, "height": 900}, device_scale_factor=2)
        pg = await ctx.new_page()

        await pg.goto(BASE + "/login", wait_until="networkidle"); await pg.wait_for_timeout(800)
        await pg.screenshot(path=str(OUT / "01-login.png")); print("01 ok")

        await login(pg)
        await pg.screenshot(path=str(OUT / "02-chat.png")); print("02 ok")

        await pg.goto(BASE + "/pantry", wait_until="networkidle"); await pg.wait_for_timeout(1800)
        await pg.screenshot(path=str(OUT / "03-pantry.png")); print("03 ok")

        await pg.goto(BASE + "/recipes", wait_until="networkidle"); await pg.wait_for_timeout(3000)
        await pg.screenshot(path=str(OUT / "04-recipes.png")); print("04 ok")

        # 添加食材弹窗 + 联想
        await pg.goto(BASE + "/pantry", wait_until="networkidle"); await pg.wait_for_timeout(1200)
        await pg.locator("button", has_text="添加食材").first.click(); await pg.wait_for_timeout(700)
        await pg.locator(".el-dialog input").first.fill("鸡"); await pg.wait_for_timeout(1500)
        await pg.screenshot(path=str(OUT / "05-add-ingredient.png")); print("05 ok")

        # 移动端
        m = await b.new_context(viewport={"width": 390, "height": 844}, device_scale_factor=3, is_mobile=True)
        mp = await m.new_page()
        await login(mp)
        await mp.screenshot(path=str(OUT / "06-mobile-chat.png")); print("06 ok")
        await mp.goto(BASE + "/recipes", wait_until="networkidle"); await mp.wait_for_timeout(2500)
        await mp.screenshot(path=str(OUT / "07-mobile-recipes.png")); print("07 ok")
        await mp.goto(BASE + "/pantry", wait_until="networkidle"); await mp.wait_for_timeout(1500)
        await mp.screenshot(path=str(OUT / "08-mobile-pantry.png")); print("08 ok")

        await b.close()

asyncio.run(main())
