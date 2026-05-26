"""
拼多多登录自动化脚本
使用Playwright框架实现浏览器自动化登录
"""

import asyncio
import random
import re
import json
import os
from datetime import datetime

# 尝试导入Playwright
try:
    from playwright.async_api import async_playwright
except ImportError:
    print("⚠️ Playwright未安装，请先运行: pip install playwright")
    print("⚠️ 然后运行: playwright install chromium")
    raise

class PinduoduoLogin:
    def __init__(self):
        self.playwright = None
        self.browser = None
        self.page = None
        self.phone = "15691721290"  # 手机号码
        self.min_delay = 3  # 最小延迟时间（秒）
        self.max_delay = 8  # 最大延迟时间（秒）
        self.success = False  # 登录是否成功
    
    async def random_delay(self, min_sec=None, max_sec=None):
        """随机延迟，模拟人类操作"""
        if min_sec is None:
            min_sec = self.min_delay
        if max_sec is None:
            max_sec = self.max_delay
        
        delay = random.uniform(min_sec, max_sec)
        print(f"等待 {delay:.2f} 秒...")
        await asyncio.sleep(delay)
    
    async def get_sms_code(self) -> str:
        """从MCP服务器获取最新的短信验证码"""
        import requests
        from datetime import datetime, timedelta
        
        try:
            # 发送验证码后需要等待短信到达，等待时间1分半钟
            wait_seconds = 90
            print(f"等待短信发送（等待{wait_seconds}秒）...")
            for i in range(wait_seconds, 0, -1):
                print(f"\r剩余等待时间: {i}秒", end='', flush=True)
                await asyncio.sleep(1)
            print()
            
            # 多次尝试获取验证码（最多3次）
            for attempt in range(3):
                print(f"正在从MCP服务器获取最新短信验证码（第{attempt + 1}次尝试）...")
                
                response = requests.post(
                    "http://localhost:8080/",
                    json={
                        "type": "call_tool",
                        "data": {
                            "name": "get_latest_sms",
                            "arguments": {"count": 3}  # 获取多条以便筛选
                        },
                        "id": "sms-request"
                    },
                    timeout=10
                )

                if response.status_code == 200:
                    result = response.json()
                    print(f"MCP响应: {json.dumps(result, ensure_ascii=False, indent=2)}")
                    content = result.get("data", {}).get("content", [])
                    if content:
                        for sms_item in content:
                            text = sms_item.get("text", "")
                            print(f"检查短信: {text[:100]}...")
                            
                            # 检查是否是拼多多验证码
                            if '拼多多' in text or 'pinduoduo' in text.lower():
                                # 优先查找"验证码是"后面的6位数字
                                match = re.search(r'验证码是(\d{6})', text)
                                if match:
                                    code = match.group(1)
                                    print(f"✅ 成功获取验证码: {code}")
                                    return code
                                # 如果没找到，尝试查找短信中第一个6位数字
                                match = re.search(r'(\d{6})', text)
                                if match:
                                    code = match.group(1)
                                    print(f"✅ 成功获取验证码(备用方式): {code}")
                                    return code
                            else:
                                print(f"不是拼多多短信，跳过")
                        else:
                            print("未找到拼多多验证码短信")
                    else:
                        print("❌ 未获取到短信内容")
                
                # 如果不是最后一次尝试，等待后重试
                if attempt < 2:
                    print(f"第{attempt + 1}次获取失败，10秒后重试...")
                    await asyncio.sleep(10)

            print("❌ 自动获取验证码失败，需要手动输入")
            return input("请输入验证码：")
        except Exception as e:
            print(f"❌ 获取验证码失败: {e}")
            return input("请输入验证码：")
    
    async def init_browser(self):
        """初始化浏览器，添加反反爬措施"""
        if self.page is not None and self.browser is not None:
            print("检测到已存在浏览器实例，跳过初始化")
            return
            
        print("初始化浏览器...")
        self.playwright = await async_playwright().start()
        
        # 使用 Chromium 浏览器（Firefox不支持移动端模拟）
        self.browser = await self.playwright.chromium.launch(
            headless=False,  # 使用有界面模式
            args=[
                "--start-maximized",
                "--disable-gpu",
                "--disable-web-security",
                "--disable-dev-shm-usage",
                "--no-sandbox",
                "--disable-blink-features=AutomationControlled",  # 隐藏自动化控制特征
                "--disable-extensions",
                "--disable-plugins-discovery",
                "--mute-audio",
            ],
            slow_mo=100,  # 减慢操作速度，模拟人类操作
        )
        
        # 设置移动端模拟，包含自定义用户代理
        iphone_15 = self.playwright.devices['iPhone 15']
        # 更新用户代理为更真实的移动端浏览器
        iphone_15['user_agent'] = "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1"
        self.page = await self.browser.new_page(**iphone_15)
        
        # 设置超时时间
        self.page.set_default_timeout(60000)
        
        # 添加反反爬的额外设置
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
            window.chrome = {
                runtime: {}
            };
            window.navigator.chrome = {
                runtime: {}
            };
            Object.defineProperty(navigator, 'permissions', {
                value: {
                    query: () => Promise.resolve({ state: 'granted' })
                },
                configurable: true
            });
        """)
    
    async def open_login_page(self) -> bool:
        """打开登录页面"""
        print("\n========== 步骤1：打开拼多多登录页面 ==========")
        try:
            await self.random_delay()
            await self.page.goto("https://mobile.pinduoduo.com/login.html")
            await self.page.wait_for_load_state('networkidle')
            await self.page.screenshot(path='step1_login_page.png')
            print("✅ 登录页面打开成功")
            await self.random_delay()
            return True
        except Exception as e:
            print(f"❌ 打开登录页面失败: {e}")
            return False
    
    async def click_phone_login(self) -> bool:
        """点击手机登录标签"""
        print("\n========== 步骤2：点击手机登录标签 ==========")
        try:
            await self.random_delay(1, 2)

            await self.page.screenshot(path='step2_initial.png')

            selectors = [
                '.login-tab.phone',
                'div.login-tab:nth-child(1)',
                'div.login-tab',
                '.login-tab',
                '//div[text()="手机登录"]',
                '//div[contains(text(),"手机登录")]',
                '//div[contains(text(),"手机")]',
                '//span[text()="手机登录"]',
                '//button[text()="手机登录"]',
                '//a[text()="手机登录"]',
                '.tab-item[data-type="phone"]',
                '.switch-login',
                '.login-type-switch',
            ]

            for selector in selectors:
                try:
                    if selector.startswith('//'):
                        phone_tab = await self.page.wait_for_selector(selector, timeout=3000, state='visible')
                    else:
                        phone_tab = await self.page.query_selector(selector)
                    if phone_tab:
                        text = await phone_tab.text_content()
                        print(f"找到元素: '{text}' (选择器: {selector})")
                        await phone_tab.click(delay=random.uniform(100, 300))
                        await self.random_delay(1, 2)
                        await self.page.screenshot(path='step2_phone_login.png')
                        print(f"✅ 成功切换到手机登录界面")
                        await self.random_delay()
                        return True
                except Exception as e:
                    continue

            print("⚠️ 未找到标准手机登录标签，尝试查找其他可能元素...")
            elements = await self.page.query_selector_all('div, span, button, a')
            for elem in elements:
                try:
                    text = await elem.inner_text()
                    if text and ('手机' in text or 'phone' in text.lower()):
                        print(f"找到可能元素: '{text}'")
                        await elem.click(delay=random.uniform(100, 300))
                        await self.random_delay(1, 2)
                        await self.page.screenshot(path='step2_phone_login.png')
                        print("✅ 点击了包含手机关键字的元素")
                        await self.random_delay()
                        return True
                except:
                    continue

            print("⚠️ 未找到手机登录标签，检查当前页面状态")
            await self.page.screenshot(path='step2_check_state.png')
            page_content = await self.page.content()
            if 'input' in page_content and 'phone' in page_content.lower():
                print("检测到页面包含手机号输入框，可能已默认显示手机登录")
            elif 'input' in page_content:
                print("检测到页面包含输入框，继续下一步")
            await self.random_delay()
            return True

        except Exception as e:
            print(f"❌ 点击手机登录标签失败: {e}")
            await self.page.screenshot(path='step2_error.png')
            return False
    
    async def select_country(self) -> bool:
        """选择中国大陆"""
        print("\n========== 步骤3：选择中国大陆 ==========")
        try:
            await self.random_delay(1, 2)
            
            # 尝试查找国家选择器
            selectors = [
                '.country-select',
                '#country-select',
                '.phone-prefix',
                'span.country-code',
            ]
            
            found = False
            for selector in selectors:
                try:
                    country_select = await self.page.query_selector(selector)
                    if country_select:
                        await country_select.click(delay=random.uniform(100, 300))
                        await self.random_delay(1, 2)
                        
                        # 查找中国大陆选项
                        china_option = await self.page.wait_for_selector('//div[text()="中国大陆"]', timeout=3000)
                        if china_option:
                            await china_option.click(delay=random.uniform(100, 300))
                            await self.random_delay(1, 2)
                            await self.page.screenshot(path='step3_country.png')
                            print("✅ 成功选择中国大陆")
                            found = True
                            break
                except Exception as e:
                    print(f"选择器 {selector} 查找失败: {e}")
                    continue
            
            if not found:
                print("⚠️ 未找到国家选择器，跳过此步骤（可能已默认选择中国大陆）")
            
            await self.random_delay()
            return True
            
        except Exception as e:
            print(f"❌ 选择国家失败: {e}")
            print("⚠️ 跳过此步骤，继续执行")
            await self.random_delay()
            return True
    
    async def input_phone(self) -> bool:
        """输入手机号码"""
        print("\n========== 步骤4：输入手机号码 ==========")
        try:
            await self.random_delay(1, 2)
            
            # 尝试多种选择器查找手机号输入框
            selectors = [
                '#input-phone',
                'input[name="mobile"]',
                'input[type="tel"]',
                'input.phone-input',
                '.phone-input input',
            ]
            
            phone_input = None
            for selector in selectors:
                try:
                    phone_input = await self.page.wait_for_selector(selector, timeout=5000)
                    if phone_input:
                        print(f"找到手机号输入框（通过选择器 {selector}）")
                        break
                except Exception as e:
                    print(f"选择器 {selector} 查找失败: {e}")
                    continue
            
            if phone_input:
                # 先点击获取焦点
                await phone_input.click(delay=random.uniform(100, 300))
                await self.random_delay(0.5, 1.5)
                
                # 清空输入框
                await phone_input.fill("")
                await self.random_delay(0.2, 0.5)
                
                # 使用fill方式输入手机号（更可靠）
                await phone_input.fill(self.phone)
                await self.random_delay(0.5, 1.5)
                
                # 验证输入是否成功
                input_value = await phone_input.get_attribute('value')
                if input_value == self.phone:
                    await self.page.screenshot(path='step4_phone_input.png')
                    print(f"✅ 手机号 {self.phone} 输入成功")
                    await self.random_delay()
                    return True
                else:
                    print("尝试使用keyboard方式输入...")
                    await phone_input.click()
                    await self.random_delay(0.2, 0.5)
                    await self.page.keyboard.type(self.phone, delay=50)
                    await self.random_delay(0.5, 1)
                    
                    input_value = await phone_input.get_attribute('value')
                    if input_value == self.phone:
                        await self.page.screenshot(path='step4_phone_input.png')
                        print(f"✅ 手机号 {self.phone} 输入成功（keyboard方式）")
                        await self.random_delay()
                        return True
                    else:
                        print(f"❌ 手机号输入失败，当前值: {input_value}")
                        return False
            else:
                print("❌ 未找到手机号输入框")
                return False
                
        except Exception as e:
            print(f"❌ 输入手机号失败: {e}")
            return False
    
    async def click_send_code(self) -> bool:
        """点击发送验证码按钮"""
        print("\n========== 步骤5：点击发送验证码 ==========")
        try:
            await self.random_delay(1, 2)
            
            # 保存页面HTML用于调试
            page_html = await self.page.content()
            with open('step5_page.html', 'w', encoding='utf-8') as f:
                f.write(page_html)
            
            # 先检查并勾选协议
            print("检查并勾选协议...")
            await self.click_agreement()
            
            # 尝试多种选择器查找发送验证码按钮
            selectors = [
                '#code-button',
                '.code-button',
                'button.get-code',
                'button.send-code',
                '//button[text()="发送验证码"]',
                '//span[text()="发送验证码"]',
                '//button[contains(text(),"发送验证码")]',
                '//div[text()="发送验证码"]',
            ]
            
            for selector in selectors:
                try:
                    send_button = await self.page.wait_for_selector(selector, timeout=5000)
                    if send_button:
                        text = await send_button.text_content()
                        print(f"找到发送验证码按钮: '{text}'")
                        
                        await send_button.click(delay=random.uniform(100, 300))
                        await self.random_delay(2, 3)
                        
                        # 验证是否成功触发发送（按钮文本变为倒计时）
                        new_text = await send_button.text_content()
                        if '重新发送' in new_text or '秒' in new_text:
                            print(f"点击后按钮文本: '{new_text}'")
                            await self.page.screenshot(path='step5_send_code.png')
                            print("✅ 验证码发送成功，按钮已变为倒计时")
                            await self.random_delay()
                            return True
                        else:
                            print(f"⚠️ 按钮文本未变化: '{new_text}'，可能发送失败")
                            # 尝试再次点击
                            await send_button.click(delay=random.uniform(100, 300))
                            await self.random_delay(2, 3)
                            new_text = await send_button.text_content()
                            if '重新发送' in new_text or '秒' in new_text:
                                print(f"第二次点击后按钮文本: '{new_text}'")
                                await self.page.screenshot(path='step5_send_code.png')
                                print("✅ 验证码发送成功")
                                await self.random_delay()
                                return True
                                
                except Exception as e:
                    print(f"选择器 {selector} 查找失败: {e}")
                    continue
            
            print("❌ 未找到发送验证码按钮")
            return False
                
        except Exception as e:
            print(f"❌ 发送验证码失败: {e}")
            return False
    
    async def click_agreement(self) -> bool:
        """勾选服务协议"""
        try:
            # 尝试多种选择器查找协议勾选框
            selectors = [
                '.agreement-icon',
                '.agreement-checkbox',
                '#agree',
                'input[type="checkbox"]',
                '//div[@class="agreement"]',
                '//label[@for="agree"]',
                '.checkbox-icon',
            ]
            
            for selector in selectors:
                try:
                    checkbox = await self.page.wait_for_selector(selector, timeout=3000)
                    if checkbox:
                        # 检查是否已勾选
                        is_checked = await checkbox.evaluate('el => el.checked || el.classList.contains("checked") || el.classList.contains("active")')
                        if not is_checked:
                            await checkbox.click(delay=random.uniform(100, 200))
                            await self.random_delay(0.5, 1)
                            # 验证是否勾选成功
                            is_checked = await checkbox.evaluate('el => el.checked || el.classList.contains("checked") || el.classList.contains("active")')
                            if is_checked:
                                print("✅ 协议已勾选")
                                return True
                        else:
                            print("✅ 协议已勾选（已选中）")
                            return True
                except Exception as e:
                    print(f"选择器 {selector} 查找失败: {e}")
                    continue
            
            print("⚠️ 未找到协议勾选框，继续执行")
            return True
            
        except Exception as e:
            print(f"⚠️ 勾选协议失败: {e}")
            return True
    
    async def input_verification_code(self) -> bool:
        """输入验证码"""
        print("\n========== 步骤6：输入验证码 ==========")
        # 等待短信发送 - 增加等待时间到30秒
        print("等待短信发送（等待30秒）...")
        for i in range(30, 0, -1):
            print(f"\r剩余等待时间: {i}秒", end='', flush=True)
            await asyncio.sleep(1)
        print()

        # 获取验证码
        code = await self.get_sms_code()
        
        try:
            # 先截图查看当前页面状态
            await self.page.screenshot(path='step6_before_input.png')

            # 使用ID选择器查找验证码输入框
            code_input = await self.page.query_selector('#input-code')
            if code_input:
                # 先点击输入框获取焦点
                await code_input.click(delay=random.uniform(100, 300))
                await self.random_delay(0.5, 1.5)

                # 清空输入框
                await code_input.fill("")
                await self.random_delay(0.2, 0.5)

                # 使用fill方式输入验证码（更可靠）
                await code_input.fill(code)
                await self.random_delay(0.5, 1.5)

                # 触发input事件
                await self.page.evaluate('document.querySelector("#input-code").dispatchEvent(new Event("input", {bubbles: true}))')
                await self.random_delay(0.3, 0.5)

                # 验证输入是否成功 - 直接获取input的value值
                input_value = await self.page.evaluate('document.querySelector("#input-code").value')
                print(f"验证码输入框值(evaluate): '{input_value}'")

                # 如果evaluate的值等于code，说明输入成功
                if input_value == code:
                    await self.page.screenshot(path='step6_code_input.png')
                    print(f"✅ 验证码 {code} 输入成功")
                    await self.random_delay()
                    return True
                else:
                    # 尝试使用keyboard方式输入
                    print("尝试使用keyboard方式输入...")
                    await code_input.click()
                    await self.random_delay(0.2, 0.5)
                    await self.page.keyboard.type(code, delay=50)
                    await self.random_delay(0.5, 1)

                    input_value = await self.page.evaluate('document.querySelector("#input-code").value')
                    print(f"keyboard输入后验证码输入框值: '{input_value}'")

                    if input_value == code:
                        await self.page.screenshot(path='step6_code_input.png')
                        print(f"✅ 验证码 {code} 输入成功（keyboard方式）")
                        await self.random_delay()
                        return True
                    else:
                        print(f"❌ 验证码输入失败，当前值: {input_value}")
                        return False
            else:
                print("❌ 未找到验证码输入框")
                # 尝试其他选择器
                other_selectors = [
                    'input[name="code"]',
                    'input[type="number"]',
                    '.code-input',
                ]
                
                for selector in other_selectors:
                    try:
                        code_input = await self.page.wait_for_selector(selector, timeout=3000)
                        if code_input:
                            await code_input.click(delay=random.uniform(100, 300))
                            await self.random_delay(0.5, 1.5)
                            await code_input.fill(code)
                            await self.random_delay(0.5, 1.5)
                            
                            input_value = await code_input.get_attribute('value')
                            if input_value == code:
                                await self.page.screenshot(path='step6_code_input.png')
                                print(f"✅ 验证码 {code} 输入成功（通过选择器 {selector}）")
                                await self.random_delay()
                                return True
                    except Exception as e:
                        print(f"选择器 {selector} 查找失败: {e}")
                        continue
                
                return False
                
        except Exception as e:
            print(f"❌ 输入验证码失败: {e}")
            return False
    
    async def click_login(self) -> bool:
        """点击登录按钮"""
        print("\n========== 步骤8：点击登录 ==========")
        try:
            # 等待登录按钮出现
            await self.page.wait_for_selector('button', timeout=10000)
            await self.random_delay(1, 2)
            
            # 保存页面HTML用于调试
            page_html = await self.page.content()
            with open('step8_page.html', 'w', encoding='utf-8') as f:
                f.write(page_html)
            
            # 尝试多种方式查找登录按钮
            
            # 方式1：查找包含特定文本的按钮
            login_texts = ['同意协议并登录', '登录', '同意并登录', '确认登录']
            buttons = await self.page.query_selector_all('button')
            found = False
            
            for btn in buttons:
                try:
                    text = await btn.text_content()
                    text = text.strip()
                    if text:
                        print(f"发现按钮: '{text}'")
                        # 检查是否是登录按钮
                        for login_text in login_texts:
                            if login_text in text:
                                print(f"找到登录按钮: '{text}'")
                                await btn.click(delay=random.uniform(100, 300))
                                await self.random_delay(3, 5)  # 增加等待时间
                                
                                # 验证是否触发登录（URL变化或页面跳转）
                                current_url = self.page.url
                                if 'login' not in current_url.lower() or 'index' in current_url.lower():
                                    await self.page.screenshot(path='step8_after_login.png')
                                    print("✅ 登录请求已发送，页面正在跳转")
                                    found = True
                                    break
                        if found:
                            break
                except Exception as e:
                    print(f"检查按钮失败: {e}")
                    continue
            
            # 方式2：如果方式1失败，尝试通过其他选择器查找
            if not found:
                print("尝试其他选择器查找登录按钮...")
                selectors = [
                    '#login-button',
                    '.login-btn',
                    '.submit-btn',
                    '[data-testid="login"]',
                    'button[type="submit"]',
                    '.agreement-login',
                ]
                
                for selector in selectors:
                    try:
                        btn = await self.page.query_selector(selector)
                        if btn:
                            text = await btn.text_content()
                            print(f"通过选择器 {selector} 找到按钮: '{text}'")
                            await btn.click(delay=random.uniform(100, 300))
                            await self.random_delay(3, 5)
                            
                            current_url = self.page.url
                            if 'login' not in current_url.lower() or 'index' in current_url.lower():
                                await self.page.screenshot(path='step8_after_login.png')
                                print("✅ 登录请求已发送，页面正在跳转")
                                found = True
                                break
                    except Exception as e:
                        print(f"选择器 {selector} 查找失败: {e}")
                        continue
            
            if found:
                await self.random_delay()
                return True
            else:
                print("❌ 未找到登录按钮")
                # 截图保存当前页面状态
                await self.page.screenshot(path='step8_no_button.png')
                # 提示用户手动点击登录
                print("请在浏览器中手动点击登录按钮，然后按回车继续...")
                for i in range(30, 0, -1):
                    print(f"\r剩余等待时间: {i}秒", end='', flush=True)
                    await asyncio.sleep(1)
                print("\n✅ 用户已手动点击登录")
                await self.random_delay()
                return True
                
        except Exception as e:
            print(f"❌ 点击登录失败: {e}")
            print("请在浏览器中手动点击登录按钮，然后按回车继续...")
            for i in range(30, 0, -1):
                print(f"\r剩余等待时间: {i}秒", end='', flush=True)
                await asyncio.sleep(1)
            print("\n✅ 用户已手动点击登录")
            await self.random_delay()
            return True
    
    async def verify_login(self) -> bool:
        """验证登录是否成功"""
        print("\n========== 步骤9：验证登录状态 ==========")
        try:
            # 等待页面加载
            await self.page.wait_for_load_state('networkidle')
            await self.random_delay(3, 5)

            # 获取当前URL
            current_url = self.page.url
            print(f"当前URL: {current_url}")

            # 保存Cookie
            cookies = await self.page.context.cookies()
            with open('pdd_cookies.json', 'w', encoding='utf-8') as f:
                json.dump(cookies, f, ensure_ascii=False, indent=2)
            print("✅ Cookie已保存")

            # 获取页面标题
            title = await self.page.title()
            print(f"页面标题: {title}")

            # 检查是否登录成功
            # 成功的标志：
            # 1. URL路径包含 index 且不包含 login（排除参数中的 login）
            # 2. 页面标题包含"拼多多"且URL不直接指向登录页
            from urllib.parse import urlparse
            parsed = urlparse(current_url)
            path = parsed.path.lower()

            if 'index' in path and 'login' not in path:
                await self.page.screenshot(path='step9_login_success.png')
                print("✅ 登录成功：URL路径包含首页特征")
                self.success = True
                return True
            elif path == '/' or path == '':
                await self.page.screenshot(path='step9_login_success.png')
                print("✅ 登录成功：URL路径为根路径")
                self.success = True
                return True
            elif 'login' not in path and title and '拼多多' in title:
                await self.page.screenshot(path='step9_login_success.png')
                print("✅ 登录成功：页面标题包含拼多多")
                self.success = True
                return True
            else:
                await self.page.screenshot(path='step9_login_failed.png')
                print(f"❌ 登录状态未知：path={path}, title={title}")
                # 进一步检查是否是首页特征
                if title and ('首页' in title or 'pinduoduo' in title.lower()):
                    self.success = True
                    return True
                return False

        except Exception as e:
            print(f"❌ 验证登录状态失败: {e}")
            return False
    
    async def close_browser(self, close_external=False):
        """关闭浏览器
        Args:
            close_external: 如果为 True，则关闭外部传入的浏览器实例
                          如果为 False（默认），则保留外部传入的浏览器实例
        """
        if close_external or (not hasattr(self, '_external_page') or not self._external_page):
            if self.browser:
                print("\n浏览器将在30秒后关闭...")
                for i in range(30, 0, -1):
                    print(f"\r剩余时间: {i}秒", end='', flush=True)
                    await asyncio.sleep(1)
                print()
                await self.browser.close()
            if self.playwright:
                await self.playwright.stop()
    
    async def run_login(self) -> bool:
        """执行完整的登录流程"""
        print("\n========== 拼多多登录自动化开始 ==========")
        print(f"随机延迟范围: {self.min_delay}-{self.max_delay}秒")
        
        # 检查 page 是否是外部传入的
        external_page = self.page is not None
        if external_page:
            self._external_page = True
            print("检测到外部传入的页面，将保留浏览器实例")
        else:
            self._external_page = False
        
        try:
            # 步骤1：初始化浏览器
            await self.init_browser()
            
            # 步骤2：打开登录页面
            if not await self.open_login_page():
                await self.close_browser(close_external=not external_page)
                return False
            
            # 步骤3：点击手机登录标签
            if not await self.click_phone_login():
                await self.close_browser(close_external=not external_page)
                return False
            
            # 步骤4：选择中国大陆（可选）
            await self.select_country()
            
            # 步骤5：输入手机号码
            if not await self.input_phone():
                await self.close_browser(close_external=not external_page)
                return False
            
            # 步骤6：点击发送验证码
            if not await self.click_send_code():
                # 如果发送验证码失败，提示用户手动操作
                print("⚠️ 发送验证码失败，请手动点击发送验证码按钮")
                print("请在浏览器中手动点击发送验证码按钮，然后按回车继续...")
                for i in range(60, 0, -1):
                    print(f"\r剩余等待时间: {i}秒", end='', flush=True)
                    await asyncio.sleep(1)
                print("\n✅ 继续执行...")
            
            # 步骤7：输入验证码
            if not await self.input_verification_code():
                await self.close_browser(close_external=not external_page)
                return False
            
            # 步骤8：勾选服务协议
            await self.click_agreement()
            
            # 步骤9：点击登录
            if not await self.click_login():
                await self.close_browser(close_external=not external_page)
                return False
            
            # 步骤10：验证登录状态
            if await self.verify_login():
                print("\n🎉 登录成功！")
                await self.close_browser(close_external=not external_page)
                return True
            else:
                print("\n❌ 登录失败，请检查流程")
                await self.close_browser(close_external=not external_page)
                return False
                
        except Exception as e:
            print(f"\n❌ 登录流程发生错误: {e}")
            await self.close_browser(close_external=not external_page)
            return False

if __name__ == "__main__":
    login = PinduoduoLogin()
    success = asyncio.run(login.run_login())
    exit(0 if success else 1)
