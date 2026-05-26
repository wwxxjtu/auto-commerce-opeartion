"""拼多多搜索工具 - Web应用"""
import asyncio
import random
import json
import os
import re
import requests
from flask import Flask, render_template_string, request, jsonify, send_file
from playwright.async_api import async_playwright

# 导入拼多多登录模块
from pinduoduo_login import PinduoduoLogin

app = Flask(__name__)

class LoginManager:
    """登录管理器，单例模式管理浏览器和登录状态"""
    _instance = None
    _lock = asyncio.Lock()
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        self._initialized = True
        self.playwright = None
        self.browser = None
        self.context = None
        self.page = None
        self.logged_in = False
    
    async def init_browser(self):
        """初始化浏览器"""
        if self.browser is not None:
            return
        
        print("初始化浏览器...")
        self.playwright = await async_playwright().start()
        self.browser = await self.playwright.chromium.launch(
            headless=False,
            args=[
                "--disable-gpu",
                "--disable-web-security",
                "--disable-dev-shm-usage",
                "--no-sandbox",
                "--disable-blink-features=AutomationControlled",
                "--start-maximized",
                "--user-agent=Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1",
                "--disable-extensions",
                "--disable-plugins-discovery",
            ],
            slow_mo=100,
        )
        
        iphone_15 = self.playwright.devices['iPhone 15']
        iphone_15['user_agent'] = "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1"
        
        self.context = await self.browser.new_context(**iphone_15)
        self.page = await self.context.new_page()
        
        await self.page.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined
            });
            Object.defineProperty(navigator, 'plugins', {
                get: () => [1, 2, 3, 4, 5]
            });
            Object.defineProperty(navigator, 'languages', {
                get: () => ['zh-CN', 'zh', 'en']
            });
            window.chrome = { runtime: {} };
            Object.defineProperty(navigator, 'permissions', {
                value: { query: () => Promise.resolve({ state: 'granted' }) },
                configurable: true
            });
        """)
        print("浏览器初始化完成")
    
    async def login(self):
        """执行登录流程，返回是否登录成功"""
        async with self._lock:
            if self.logged_in:
                return True
            
            await self.init_browser()
            
            login = PinduoduoLogin()
            login.page = self.page
            
            print("开始执行登录流程...")
            success = await login.run_login()
            
            if success:
                self.logged_in = True
                print("✅ 登录成功")
            else:
                print("❌ 登录失败")
            
            return success
    
    async def ensure_logged_in(self):
        """确保已登录，如果未登录则执行登录流程"""
        if self.logged_in and self.page is not None:
            from urllib.parse import urlparse
            parsed = urlparse(self.page.url)
            path = parsed.path.lower()
            title = await self.page.title() if self.page else ''

            # 检查URL路径和页面标题来判断是否真的在登录状态
            if ('index' in path or path == '/' or path == '') and 'login' not in path:
                print(f"当前已登录，URL: {self.page.url}")
                return True
            elif title and '拼多多' in title and 'login' not in path:
                print(f"当前已登录（标题验证），URL: {self.page.url}")
                return True
            else:
                print(f"检测到页面状态异常（path={path}, title={title}），需要重新登录")
                self.logged_in = False

        return await self.login()
    
    async def get_page(self):
        """获取当前页面，如果未登录则先登录"""
        if not await self.ensure_logged_in():
            return None
        return self.page
    
    async def close(self):
        """关闭浏览器"""
        if self.page:
            await self.page.close()
            self.page = None
        if self.context:
            await self.context.close()
            self.context = None
        if self.browser:
            await self.browser.close()
            self.browser = None
        if self.playwright:
            await self.playwright.stop()
            self.playwright = None
        self.logged_in = False
        print("浏览器已关闭")

login_manager = LoginManager()

async def random_delay(min_sec=3, max_sec=8):
    """随机延迟，模拟人类操作间隔"""
    delay = random.uniform(min_sec, max_sec)
    print(f"等待 {delay:.2f} 秒...")
    await asyncio.sleep(delay)

async def long_delay(min_sec=10, max_sec=15):
    """长延迟，用于关键操作之间"""
    delay = random.uniform(min_sec, max_sec)
    print(f"等待 {delay:.2f} 秒（长延迟）...")
    await asyncio.sleep(delay)

async def search_shop(shop_name):
    """搜索店铺并获取销量排序页面"""
    page = await login_manager.get_page()
    if page is None:
        return {"error": "登录失败，请手动登录后重试"}
    
    try:
        # 检查当前页面URL，判断是否需要重新登录
        current_url = page.url
        if 'login' in current_url.lower():
            print("检测到未登录状态，尝试重新登录...")
            if not await login_manager.ensure_logged_in():
                return {"error": "登录失败，请手动登录后重试"}
            page = login_manager.page
        
        # 打开拼多多搜索页面
        search_url = f"https://mobile.pinduoduo.com/search_result.html?keyword={shop_name}"
        await page.goto(search_url, timeout=60000)
        await long_delay(10, 15)
        
        # 检查是否被重定向到登录页
        if 'login' in page.url.lower():
            print("页面跳转到登录页，尝试重新登录...")
            if not await login_manager.ensure_logged_in():
                return {"error": "登录失败，请手动登录后重试"}
            page = login_manager.page
            await page.goto(search_url, timeout=60000)
            await long_delay(10, 15)
        
        # 等待页面加载完成
        await page.wait_for_selector('body', timeout=30000)
        await random_delay(3, 5)
        
        # 获取页面内容用于调试
        await page.screenshot(path='static/search_result.png')
        
        # 获取所有文本内容
        all_text = await page.inner_text('body')
        await random_delay(2, 4)
        
        # 尝试找到店铺标签 - 使用多种选择器
        shop_tab = None
        selectors = [
            'text/店铺',
            '.tab-shop',
            '[data-type="shop"]',
            '.category-tabs div',
        ]
        
        for selector in selectors:
            try:
                shop_tab = await page.query_selector(selector)
                if shop_tab:
                    break
            except:
                continue
        
        if shop_tab:
            await shop_tab.click(delay=random.uniform(200, 500))
            await long_delay(10, 15)
        else:
            elements = await page.query_selector_all('div, span, button')
            for elem in elements:
                try:
                    text = await elem.inner_text()
                    if '店铺' in text:
                        await elem.click(delay=random.uniform(200, 500))
                        await long_delay(10, 15)
                        shop_tab = elem
                        break
                except:
                    continue
        
        if not shop_tab:
            return {"error": f"未找到店铺标签，页面文本预览: {all_text[:500]}"}
        
        await random_delay(3, 5)
        
        # 获取店铺列表
        shops = []
        shop_selectors = [
            '.search-shop-item',
            '.shop-item',
            '.goods-item',
            '[class*="shop"]',
            '.item',
        ]
        
        shop_elements = []
        for selector in shop_selectors:
            try:
                elements = await page.query_selector_all(selector)
                if elements:
                    shop_elements = elements
                    break
            except:
                continue
        
        for idx, element in enumerate(shop_elements[:10]):
            try:
                name = ''
                sales = ''
                
                name_selectors = ['.shop-name', '.name', '.title', 'span:first-child', 'div:first-child']
                for sel in name_selectors:
                    try:
                        name_elem = await element.query_selector(sel)
                        if name_elem:
                            name = await name_elem.inner_text()
                            break
                    except:
                        continue
                
                sales_selectors = ['.shop-sales', '.sales', '.num', '[class*="sales"]', 'div:last-child']
                for sel in sales_selectors:
                    try:
                        sales_elem = await element.query_selector(sel)
                        if sales_elem:
                            sales = await sales_elem.inner_text()
                            break
                    except:
                        continue
                
                if name or sales:
                    shops.append({
                        'rank': idx + 1,
                        'name': name.strip() if name else '未知',
                        'sales': sales.strip() if sales else '未知'
                    })
            except Exception as e:
                continue
        
        screenshot_path = f'static/shop_search_{shop_name[:10]}.png'
        await page.screenshot(path=screenshot_path, full_page=True)
        
        return {
            'success': True,
            'shops': shops,
            'screenshot': screenshot_path
        }
    
    except Exception as e:
        try:
            await page.screenshot(path='static/error_shop.png')
        except:
            pass
        return {"error": str(e)}

async def search_product(product_name):
    """搜索商品并获取销量排序页面"""
    page = await login_manager.get_page()
    if page is None:
        return {"error": "登录失败，请手动登录后重试"}
    
    try:
        current_url = page.url
        if 'login' in current_url.lower():
            print("检测到未登录状态，尝试重新登录...")
            if not await login_manager.ensure_logged_in():
                return {"error": "登录失败，请手动登录后重试"}
            page = login_manager.page
        
        search_url = f"https://mobile.pinduoduo.com/search_result.html?keyword={product_name}"
        await page.goto(search_url, timeout=60000)
        await long_delay(10, 15)
        
        if 'login' in page.url.lower():
            print("页面跳转到登录页，尝试重新登录...")
            if not await login_manager.ensure_logged_in():
                return {"error": "登录失败，请手动登录后重试"}
            page = login_manager.page
            await page.goto(search_url, timeout=60000)
            await long_delay(10, 15)
        
        await page.wait_for_selector('body', timeout=30000)
        await random_delay(3, 5)
        
        await page.screenshot(path='static/search_result_p.png')
        
        all_text = await page.inner_text('body')
        await random_delay(2, 4)
        
        sales_sort = None
        selectors = [
            'text/销量',
            '.sort-sales',
            '[data-sort="sales"]',
            '.sort-bar div',
        ]
        
        for selector in selectors:
            try:
                sales_sort = await page.query_selector(selector)
                if sales_sort:
                    break
            except:
                continue
        
        if sales_sort:
            await sales_sort.click(delay=random.uniform(200, 500))
            await long_delay(10, 15)
        else:
            elements = await page.query_selector_all('div, span, button')
            for elem in elements:
                try:
                    text = await elem.inner_text()
                    if '销量' in text:
                        await elem.click(delay=random.uniform(200, 500))
                        await long_delay(10, 15)
                        sales_sort = elem
                        break
                except:
                    continue
        
        if not sales_sort:
            return {"error": f"未找到销量排序按钮，页面文本预览: {all_text[:500]}"}
        
        await random_delay(3, 5)
        
        products = []
        product_selectors = [
            '.search-item',
            '.goods-item',
            '.item',
            '[class*="goods"]',
        ]
        
        product_elements = []
        for selector in product_selectors:
            try:
                elements = await page.query_selector_all(selector)
                if elements:
                    product_elements = elements
                    break
            except:
                continue
        
        for idx, element in enumerate(product_elements[:10]):
            try:
                name = ''
                price = ''
                sales = ''
                
                name_selectors = ['.goods-name', '.name', '.title', '.goods-title']
                for sel in name_selectors:
                    try:
                        name_elem = await element.query_selector(sel)
                        if name_elem:
                            name = await name_elem.inner_text()
                            break
                    except:
                        continue
                
                price_selectors = ['.goods-price', '.price', '.cost', '[class*="price"]']
                for sel in price_selectors:
                    try:
                        price_elem = await element.query_selector(sel)
                        if price_elem:
                            price = await price_elem.inner_text()
                            break
                    except:
                        continue
                
                sales_selectors = ['.goods-sales', '.sales', '.num', '[class*="sales"]']
                for sel in sales_selectors:
                    try:
                        sales_elem = await element.query_selector(sel)
                        if sales_elem:
                            sales = await sales_elem.inner_text()
                            break
                    except:
                        continue
                
                if name or price:
                    products.append({
                        'rank': idx + 1,
                        'name': name.strip() if name else '未知',
                        'price': price.strip() if price else '未知',
                        'sales': sales.strip() if sales else '未知'
                    })
            except Exception as e:
                continue
        
        screenshot_path = f'static/product_search_{product_name[:10]}.png'
        await page.screenshot(path=screenshot_path, full_page=True)
        
        return {
            'success': True,
            'products': products,
            'screenshot': screenshot_path
        }
    
    except Exception as e:
        try:
            await page.screenshot(path='static/error_product.png')
        except:
            pass
        return {"error": str(e)}

# HTML模板
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>拼多多搜索工具</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }
        .container {
            max-width: 1200px;
            margin: 0 auto;
        }
        .header {
            text-align: center;
            color: white;
            margin-bottom: 30px;
        }
        .header h1 {
            font-size: 2.5rem;
            margin-bottom: 10px;
        }
        .header p {
            font-size: 1.1rem;
            opacity: 0.9;
        }
        .tabs {
            display: flex;
            justify-content: center;
            gap: 10px;
            margin-bottom: 20px;
        }
        .tab {
            padding: 12px 30px;
            border: none;
            border-radius: 25px;
            font-size: 1rem;
            cursor: pointer;
            transition: all 0.3s;
            font-weight: 600;
        }
        .tab.active {
            background: white;
            color: #667eea;
            box-shadow: 0 4px 15px rgba(0,0,0,0.2);
        }
        .tab.inactive {
            background: rgba(255,255,255,0.2);
            color: white;
        }
        .tab.inactive:hover {
            background: rgba(255,255,255,0.3);
        }
        .search-box {
            background: white;
            border-radius: 15px;
            padding: 30px;
            box-shadow: 0 10px 40px rgba(0,0,0,0.15);
        }
        .search-form {
            display: flex;
            gap: 15px;
            margin-bottom: 25px;
        }
        .search-input {
            flex: 1;
            padding: 15px 20px;
            border: 2px solid #e0e0e0;
            border-radius: 10px;
            font-size: 1rem;
            transition: border-color 0.3s;
        }
        .search-input:focus {
            outline: none;
            border-color: #667eea;
        }
        .search-btn {
            padding: 15px 40px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border: none;
            border-radius: 10px;
            font-size: 1rem;
            font-weight: 600;
            cursor: pointer;
            transition: transform 0.2s, box-shadow 0.2s;
        }
        .search-btn:hover {
            transform: translateY(-2px);
            box-shadow: 0 5px 20px rgba(102, 126, 234, 0.4);
        }
        .search-btn:disabled {
            opacity: 0.6;
            cursor: not-allowed;
            transform: none;
        }
        .login-status {
            background: #e8f5e9;
            border: 1px solid #a5d6a7;
            border-radius: 10px;
            padding: 12px 15px;
            margin-bottom: 20px;
            color: #2e7d32;
            display: flex;
            align-items: center;
            gap: 10px;
        }
        .login-status.warning {
            background: #fff3e0;
            border-color: #ffcc80;
            color: #e65100;
        }
        .loading {
            text-align: center;
            padding: 40px;
            color: #666;
        }
        .loading img {
            width: 50px;
            animation: spin 1s linear infinite;
        }
        @keyframes spin {
            from { transform: rotate(0deg); }
            to { transform: rotate(360deg); }
        }
        .result {
            margin-top: 25px;
        }
        .result-title {
            font-size: 1.2rem;
            font-weight: 600;
            margin-bottom: 15px;
            color: #333;
        }
        .table-container {
            overflow-x: auto;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }
        table {
            width: 100%;
            border-collapse: collapse;
            background: white;
        }
        th, td {
            padding: 12px 15px;
            text-align: left;
            border-bottom: 1px solid #eee;
        }
        th {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            font-weight: 600;
        }
        tr:hover {
            background: #f8f9fa;
        }
        .screenshot-container {
            margin-top: 25px;
            border-radius: 10px;
            overflow: hidden;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }
        .screenshot-container img {
            width: 100%;
            display: block;
        }
        .error {
            background: #fff5f5;
            border: 1px solid #fed7d7;
            border-radius: 10px;
            padding: 15px;
            color: #c53030;
            margin-top: 20px;
        }
        .footer {
            text-align: center;
            color: white;
            margin-top: 30px;
            opacity: 0.8;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🔍 拼多多搜索工具</h1>
            <p>搜索店铺或商品，获取销量排序结果</p>
        </div>
        
        <div class="tabs">
            <button class="tab active" onclick="switchTab('shop')">🏪 店铺搜索</button>
            <button class="tab inactive" onclick="switchTab('product')">📦 商品搜索</button>
        </div>
        
        <div class="search-box">
            <div id="loginStatus" class="login-status">
                <span>🔒</span>
                <span>检查登录状态...</span>
            </div>
            
            <form class="search-form" onsubmit="handleSearch(event)">
                <input 
                    type="text" 
                    id="searchInput" 
                    class="search-input" 
                    placeholder="请输入搜索关键词..."
                    required
                >
                <button type="submit" id="searchBtn" class="search-btn">
                    搜索
                </button>
            </form>
            
            <div id="loading" class="loading" style="display: none;">
                <img src="data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24'%3E%3Ccircle class='path' cx='12' cy='12' r='10' fill='none' stroke='%23667eea' stroke-width='4' stroke-linecap='round' stroke-dasharray='100' stroke-dashoffset='0' style='animation: dash 1.5s ease-in-out infinite;'%3E%3C/circle%3E%3Cstyle%3E@keyframes dash {to {stroke-dashoffset: -200;}}%3C/style%3E%3C/svg%3E" alt="Loading">
                <p>正在搜索中，请稍候...</p>
            </div>
            
            <div id="result"></div>
        </div>
        
        <div class="footer">
            <p>拼多多搜索工具 © 2024</p>
        </div>
    </div>
    
    <script>
        let currentTab = 'shop';
        
        // 检查登录状态
        async function checkLoginStatus() {
            try {
                const response = await fetch('/login_status');
                const data = await response.json();
                const statusDiv = document.getElementById('loginStatus');
                
                if (data.logged_in) {
                    statusDiv.innerHTML = '<span>✅</span><span>已登录，可以进行搜索</span>';
                    statusDiv.className = 'login-status';
                } else {
                    statusDiv.innerHTML = '<span>⚠️</span><span>未登录，请先进行搜索触发登录流程</span>';
                    statusDiv.className = 'login-status warning';
                }
            } catch (error) {
                console.error('检查登录状态失败:', error);
            }
        }
        
        function switchTab(tab) {
            currentTab = tab;
            document.querySelectorAll('.tab').forEach(t => t.classList.remove('active', 'inactive'));
            document.querySelector('.tab:nth-child(' + (tab === 'shop' ? '1' : '2') + ')').classList.add('active');
            document.querySelector('.tab:nth-child(' + (tab === 'shop' ? '2' : '1') + ')').classList.add('inactive');
            document.getElementById('result').innerHTML = '';
        }
        
        async function handleSearch(event) {
            event.preventDefault();
            const keyword = document.getElementById('searchInput').value.trim();
            const searchBtn = document.getElementById('searchBtn');
            const loading = document.getElementById('loading');
            const result = document.getElementById('result');
            
            if (!keyword) return;
            
            searchBtn.disabled = true;
            loading.style.display = 'block';
            result.innerHTML = '';
            
            try {
                const response = await fetch('/search', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({
                        type: currentTab,
                        keyword: keyword
                    })
                });
                
                const data = await response.json();
                
                if (data.success) {
                    let html = '<div class="result-title">';
                    html += currentTab === 'shop' ? '🏪 店铺搜索结果' : '📦 商品搜索结果';
                    html += ` (共 ${currentTab === 'shop' ? data.shops.length : data.products.length} 条)</div>`;
                    
                    // 表格
                    html += '<div class="table-container"><table><thead><tr>';
                    html += '<th>排名</th>';
                    html += '<th>' + (currentTab === 'shop' ? '店铺名称' : '商品名称') + '</th>';
                    if (currentTab === 'product') {
                        html += '<th>价格</th>';
                    }
                    html += '<th>销量</th></tr></thead><tbody>';
                    
                    if (currentTab === 'shop') {
                        data.shops.forEach(item => {
                            html += `<tr><td>${item.rank}</td><td>${item.name}</td><td>${item.sales}</td></tr>`;
                        });
                    } else {
                        data.products.forEach(item => {
                            html += `<tr><td>${item.rank}</td><td>${item.name}</td><td>${item.price}</td><td>${item.sales}</td></tr>`;
                        });
                    }
                    
                    html += '</tbody></table></div>';
                    
                    // 截图
                    html += '<div class="result-title">📷 页面截图</div>';
                    html += `<div class="screenshot-container"><img src="/screenshot?path=${encodeURIComponent(data.screenshot)}" alt="搜索结果截图"></div>`;
                    
                    result.innerHTML = html;
                } else {
                    result.innerHTML = `<div class="error">❌ 搜索失败: ${data.error}</div>`;
                }
                
                // 更新登录状态
                await checkLoginStatus();
            } catch (error) {
                result.innerHTML = `<div class="error">❌ 请求失败: ${error.message}</div>`;
            } finally {
                searchBtn.disabled = false;
                loading.style.display = 'none';
            }
        }
        
        // 页面加载时检查登录状态
        document.addEventListener('DOMContentLoaded', checkLoginStatus);
    </script>
</body>
</html>
"""

@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)

@app.route('/login_status')
def login_status():
    """检查登录状态"""
    logged_in = os.path.exists('pdd_cookies.json')
    return jsonify({'logged_in': logged_in})

@app.route('/search', methods=['POST'])
def search():
    data = request.get_json()
    search_type = data.get('type')
    keyword = data.get('keyword')
    
    if search_type == 'shop':
        result = asyncio.run(search_shop(keyword))
    elif search_type == 'product':
        result = asyncio.run(search_product(keyword))
    else:
        result = {"error": "无效的搜索类型"}
    
    return jsonify(result)

@app.route('/screenshot')
def screenshot():
    path = request.args.get('path')
    return send_file(path, mimetype='image/png')

if __name__ == '__main__':
    os.makedirs('static', exist_ok=True)
    app.run(host='0.0.0.0', port=5000, debug=True)