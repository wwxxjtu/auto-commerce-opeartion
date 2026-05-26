"""调试拼多多搜索页面结构"""
import asyncio
from playwright.async_api import async_playwright

async def debug_search_page():
    """调试搜索页面"""
    playwright = await async_playwright().start()
    browser = await playwright.chromium.launch(
        headless=True,
        args=[
            "--disable-gpu",
            "--disable-web-security",
            "--disable-dev-shm-usage",
            "--no-sandbox",
            "--disable-blink-features=AutomationControlled",
            "--user-agent=Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1"
        ],
    )
    
    context = await browser.new_context(viewport={'width': 414, 'height': 896})
    page = await context.new_page()
    
    try:
        # 打开拼多多搜索页面
        search_url = "https://mobile.pinduoduo.com/search_result.html?keyword=手机"
        await page.goto(search_url, timeout=60000)
        await asyncio.sleep(3)
        
        # 获取页面HTML
        html = await page.content()
        
        # 保存HTML到文件
        with open('search_page.html', 'w', encoding='utf-8') as f:
            f.write(html)
        
        # 获取所有文本内容用于分析
        all_text = await page.inner_text('body')
        
        # 打印页面中的关键文本
        print("=== 页面文本内容（前2000字符）===")
        print(all_text[:2000])
        
        # 获取所有按钮和链接文本
        print("\n=== 页面中的按钮和链接 ===")
        buttons = await page.query_selector_all('button, a')
        for btn in buttons[:20]:
            try:
                text = await btn.inner_text()
                if text.strip():
                    print(f"  - {text.strip()}")
            except:
                continue
        
        # 获取所有div的class属性
        print("\n=== 页面中div的class属性 ===")
        divs = await page.query_selector_all('div')
        classes = set()
        for div in divs[:50]:
            try:
                cls = await div.get_attribute('class')
                if cls:
                    classes.add(cls)
            except:
                continue
        
        for cls in sorted(classes)[:30]:
            print(f"  - {cls}")
        
        await page.screenshot(path='search_debug.png')
        print("\n✅ 页面调试完成，已保存: search_page.html, search_debug.png")
        
    except Exception as e:
        print(f"❌ 调试失败: {e}")
    finally:
        await page.close()
        await context.close()
        await browser.close()
        await playwright.stop()

if __name__ == "__main__":
    asyncio.run(debug_search_page())