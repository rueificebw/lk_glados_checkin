"""ESJ论坛自动水经验脚本"""
import os
import time
import random
from playwright.sync_api import sync_playwright

# ESJ论坛配置
ESJ_LOGIN_URL = "https://www.esjzone.one/my/login"
ESJ_POST_URLS = [
    "https://www.esjzone.one/forum/1585405223/103280.html",
    "https://www.esjzone.one/forum/1585405223/80242.html"
]
ESJ_COMMENT_POOL = [
    "(゜∀゜*)",
    "(⁠・⁠∀⁠・⁠)",
    "(⁠ ⁠╹⁠▽⁠╹⁠ ⁠)",
    "(´・ω・｀)",
    "₍˄·͈༝·͈˄*₎◞ ̑̑",
    "(・ω・)",
    "(*╹▽╹*)",
    "(¦3[▓▓]",
    "Ciallo～(∠・ω< )⌒☆",
]

def get_esj_credentials():
    """从环境变量获取ESJ账号密码"""
    username = os.environ.get('ESJ_USERNAME')
    password = os.environ.get('ESJ_PASSWORD')
    
    if not username or not password:
        print("Error: 未设置ESJ_USERNAME或ESJ_PASSWORD环境变量")
        return None, None
    
    return username, password

def auto_login_esj(page, username, password):
    """自动登录ESJ，返回 True 表示成功"""
    try:
        # 访问登录页
        page.goto(ESJ_LOGIN_URL, wait_until='domcontentloaded')
        page.wait_for_timeout(2000)
        print("访问ESJ登录页")
        
        # 填写邮箱和密码（使用更精确的选择器）
        # 选择第一个可见的邮箱输入框
        email_input = page.locator("input[name='email'][type='email']").first
        if not email_input.is_visible():
            print("未找到邮箱输入框")
            return False
            
        email_input.fill(username)
        page.wait_for_timeout(500)
        
        # 找到对应的密码输入框
        password_input = page.locator("input[name='pwd'][type='password']").first
        if not password_input.is_visible():
            print("未找到密码输入框")
            return False
            
        password_input.fill(password)
        page.wait_for_timeout(500)
        print("已填写邮箱和密码")
        
        # 点击登录按钮
        login_button = page.locator("a.btn.btn-primary.margin-bottom-none.btn-send:has-text('登入')").first
        if not login_button.is_visible():
            # 尝试其他选择器
            login_button = page.locator("a:has-text('登入')").first
            
        if login_button.is_visible():
            login_button.click()
            print("点击登录按钮")
            page.wait_for_timeout(3000)
        else:
            print("未找到登录按钮")
            return False
        
        # 验证登录是否成功：检查页面是否跳转到其他页面（如首页）
        current_url = page.url
        if "login" not in current_url.lower():
            print(f"自动登录成功，当前URL: {current_url}")
            return True
        
        # 检查是否有登录成功的提示或用户信息
        try:
            # 检查是否存在用户信息元素
            user_info = page.locator("a[href*='my/profile']").first
            if user_info.is_visible():
                print("自动登录成功（检测到用户信息）")
                return True
        except Exception:
            pass
        
        print(f"自动登录失败，当前URL: {current_url}")
        return False
    except Exception as e:
        print(f"自动登录过程中出现异常: {e}")
        return False

def esj_sign():
    """执行ESJ论坛水经验流程，返回 True 表示成功，False 表示失败"""
    # 获取账号密码
    username, password = get_esj_credentials()
    if not username or not password:
        return False
    
    with sync_playwright() as p:
        # 启动浏览器
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        
        try:
            print("\n=== 开始ESJ论坛水经验 ===")
            
            # 自动登录
            if not auto_login_esj(page, username, password):
                print("登录失败，无法继续水经验")
                return False
            
            # 随机选择一个帖子
            post_url = random.choice(ESJ_POST_URLS)
            print(f"随机选择帖子: {post_url}")
            page.goto(post_url, wait_until='domcontentloaded')
            page.wait_for_timeout(3000)
            
            # 检查登录状态：如果存在昵称输入框，说明未登录
            nickname_input = page.locator("input[name='nickname'][placeholder*='暱稱']").first
            if nickname_input.is_visible():
                print("检测到昵称输入框，说明当前未登录")
                print("尝试重新登录...")
                
                # 重新登录
                if not auto_login_esj(page, username, password):
                    print("重新登录失败")
                    return False
                
                # 重新访问帖子
                page.goto(post_url, wait_until='domcontentloaded')
                page.wait_for_timeout(3000)
                
                # 再次检查登录状态
                nickname_input = page.locator("input[name='nickname'][placeholder*='暱稱']").first
                if nickname_input.is_visible():
                    print("重新登录后仍未登录成功")
                    return False
                print("重新登录成功")
            
            # 进行三次评论，每次必须成功才继续
            for i in range(1, 4):
                print(f"\n--- 第 {i} 次评论 ---")
                try:
                    # 等待评论框可编辑
                    comment_div = page.locator("div[contenteditable='true']").first
                    if not comment_div.is_visible():
                        # 尝试其他选择器
                        comment_div = page.locator("div.comment-content").first
                    
                    if comment_div.is_visible():
                        # 随机选择评论内容
                        comment_text = random.choice(ESJ_COMMENT_POOL)
                        print(f"评论内容: {comment_text}")
                        
                        # 点击评论框激活
                        comment_div.click()
                        page.wait_for_timeout(500)
                        
                        # 使用 JavaScript 注入设置内容（contenteditable div 不能直接用 fill）
                        try:
                            # 先处理字符串转义，避免f-string中使用反斜杠
                            escaped_comment = comment_text.replace("'", "\\'").replace('"', '\\"')
                            js_code = f"""
                                const el = document.querySelector('div[contenteditable="true"]');
                                if (el) {{
                                    el.innerHTML = '{escaped_comment}';
                                    el.dispatchEvent(new Event('input', {{ bubbles: true }}));
                                }}
                            """
                            page.evaluate(js_code)
                            print("已通过JavaScript注入评论内容")
                        except Exception as js_error:
                            print(f"JavaScript注入失败，尝试type方法: {js_error}")
                            # 备用方案：使用 type 方法输入
                            comment_div.type(comment_text)
                        
                        page.wait_for_timeout(1000)
                        
                        # 验证内容是否成功输入
                        try:
                            current_content = comment_div.inner_text()
                            if comment_text in current_content:
                                print(f"✓ 评论内容已成功输入: {current_content}")
                            else:
                                print(f"✗ 评论内容输入失败，当前内容: {current_content}")
                                return False
                        except Exception as e:
                            print(f"验证输入内容时出错: {e}")
                            # 继续尝试，不直接返回失败
                        
                        # 点击送出按钮
                        submit_btn = None
                        submit_selectors = [
                            "a.btn.btn-pill.btn-primary.btn-send",
                            "a.btn-send",
                            "a[class*='btn-send']",
                        ]

                        for selector in submit_selectors:
                            try:
                                btn = page.locator(selector).first
                                if btn.is_visible(timeout=2000):
                                    submit_btn = btn
                                    print(f"找到送出按钮使用选择器: {selector}")
                                    break
                                else:
                                    print(f"选择器 {selector} 存在但不可见")
                            except Exception as e:
                                print(f"选择器 {selector} 错误: {e}")
                                continue

                        if submit_btn and submit_btn.is_visible():
                            print("点击送出按钮...")
                            try:
                                submit_btn.scroll_into_view_if_needed()
                                page.wait_for_timeout(500)
                                submit_btn.click(timeout=5000)
                                print("已点击送出按钮")
                            except Exception as click_error:
                                print(f"普通点击失败，尝试force点击: {click_error}")
                                try:
                                    submit_btn.click(force=True, timeout=5000)
                                    print("已点击送出按钮（force方式）")
                                except Exception as force_error:
                                    print(f"force点击失败，尝试JavaScript点击: {force_error}")
                                    page.evaluate("""
                                        (function() {
                                            const btn = document.querySelector('a.btn.btn-pill.btn-primary.btn-send') || document.querySelector('a.btn-send');
                                            if (btn) btn.click();
                                        })()
                                    """)
                                    print("已点击送出按钮（JavaScript方式）")

                            page.wait_for_timeout(3000)
                            
                            # 等待页面刷新：检测评论框重新出现且内容为空（表示发送成功）
                            success = False
                            for attempt in range(20):  # 最多等待20秒
                                time.sleep(1)
                                try:
                                    new_comment_div = page.locator("div[contenteditable='true']").first
                                    if new_comment_div.is_visible():
                                        current_content = new_comment_div.inner_text()
                                        # 如果内容被清空或变化，说明发送成功
                                        if not current_content or current_content != comment_text:
                                            success = True
                                            print(f"第 {i} 次评论成功（检测到评论框内容变化）")
                                            break
                                except Exception as e:
                                    print(f"检测评论框状态时出错: {e}")
                                    continue
                            if not success:
                                print(f"第 {i} 次评论失败：未检测到成功标志")
                                return False
                        else:
                            print("未找到送出按钮")
                            return False
                    else:
                        print("未找到评论框")
                        return False
                except Exception as e:
                    print(f"第 {i} 次评论过程中出现异常: {e}")
                    return False
            
            print("ESJ论坛水经验流程执行完毕（三次评论成功）")
            return True
        except Exception as e:
            print(f"水经验过程中出现异常: {e}")
            return False
        finally:
            browser.close()
            print("已关闭浏览器")

def main():
    """主函数"""
    success = esj_sign()
    print("\nESJ论坛水经验流程执行完毕")
    return success

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
