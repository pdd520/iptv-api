import subprocess
import os
import time
import json
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service

def setup_selenium():
    """设置 Selenium WebDriver"""
    chrome_options = Options()
    chrome_options.add_argument("--headless=new")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--window-size=1920,1080")
    chrome_options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")
    chrome_options.add_argument("--lang=zh-CN")
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option('useAutomationExtension', False)
    
    # 使用 webdriver-manager 自动管理驱动
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)
    
    # 隐藏自动化特征
    driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
    
    return driver

def save_cookies_netscape_format(cookies, filename="cookies.txt"):
    """保存 cookies 为 Netscape 格式"""
    with open(filename, 'w', encoding='utf-8') as f:
        f.write("# Netscape HTTP Cookie File\n")
        f.write("# This file contains cookies for YouTube\n")
        f.write("# HttpOnly cookies are included\n\n")
        
        for cookie in cookies:
            if 'youtube.com' in cookie.get('domain', ''):
                domain = cookie['domain']
                if domain.startswith('.'):
                    domain = domain[1:]  # 移除开头的点
                
                flag = "TRUE" if cookie.get('httpOnly', False) else "FALSE"
                path = cookie.get('path', '/')
                secure = "TRUE" if cookie.get('secure', False) else "FALSE"
                expiry = str(cookie.get('expiry', int(time.time()) + 3600))
                name = cookie['name']
                value = cookie['value']
                
                f.write(f"{domain}\t{flag}\t{path}\t{secure}\t{expiry}\t{name}\t{value}\n")

def get_fresh_cookies():
    """获取完整的 YouTube cookies（通过模拟用户行为）"""
    print("开始获取完整的 YouTube cookies...")
    
    driver = setup_selenium()
    
    try:
        # 第一步：访问 YouTube 主页
        print("访问 YouTube 主页...")
        driver.get("https://www.youtube.com")
        time.sleep(5)
        
        # 等待页面加载
        WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.TAG_NAME, "body"))
        )
        
        # 模拟一些用户行为
        print("模拟用户行为...")
        try:
            # 滚动页面
            driver.execute_script("window.scrollTo(0, 500)")
            time.sleep(2)
            
            # 点击一些元素（如果有的话）
            try:
                accept_button = driver.find_elements(By.XPATH, "//button[contains(., '接受') or contains(., '同意') or contains(., 'Accept')]")
                if accept_button:
                    accept_button[0].click()
                    print("点击了同意按钮")
                    time.sleep(3)
            except:
                pass
                
        except Exception as e:
            print(f"模拟用户行为时出错: {e}")
        
        # 等待更长时间确保 cookies 加载完整
        time.sleep(8)
        
        # 获取所有 cookies
        cookies = driver.get_cookies()
        print(f"获取到 {len(cookies)} 个 cookies")
        
        # 筛选出 YouTube 相关的 cookies
        youtube_cookies = [c for c in cookies if 'youtube.com' in c.get('domain', '')]
        print(f"其中 {len(youtube_cookies)} 个是 YouTube cookies")
        
        # 保存为正确的 Netscape 格式
        save_cookies_netscape_format(youtube_cookies)
        
        # 验证 cookies 文件
        if os.path.exists("cookies.txt"):
            with open("cookies.txt", "r") as f:
                lines = f.readlines()
                print(f"Cookies 文件包含 {len(lines)} 行")
                
                # 检查是否包含重要的 cookies
                content = "\n".join(lines)
                important_cookies = ['VISITOR_INFO1_LIVE', 'PREF', 'YSC', 'LOGIN_INFO']
                found_cookies = [cookie for cookie in important_cookies if cookie in content]
                print(f"找到重要 cookies: {found_cookies}")
        
        return True
        
    except Exception as e:
        print(f"获取 cookies 失败: {e}")
        return False
        
    finally:
        driver.quit()

def get_stream_url_advanced(youtube_url):
    """高级方法获取流地址"""
    max_retries = 2
    
    for attempt in range(max_retries):
        try:
            # 首先尝试使用 cookies
            if os.path.exists("cookies.txt"):
                result = subprocess.run([
                    "yt-dlp", 
                    "--get-url",
                    "--cookies", "cookies.txt",
                    youtube_url
                ], capture_output=True, text=True, check=True, timeout=30)
                
                stream_url = result.stdout.strip()
                if stream_url:
                    print(f"✅ 成功获取流地址 (尝试 {attempt + 1})")
                    return stream_url
            
            # 如果失败，获取新的 cookies
            if attempt < max_retries - 1:
                print(f"尝试 {attempt + 1} 失败，获取新的完整 cookies...")
                get_fresh_cookies()  # 这里使用正确的函数名
                time.sleep(3)
                
        except subprocess.CalledProcessError as e:
            print(f"❌ 尝试 {attempt + 1} 失败")
            if attempt < max_retries - 1:
                get_fresh_cookies()  # 这里使用正确的函数名
                time.sleep(3)
        except Exception as e:
            print(f"❌ 尝试 {attempt + 1} 错误: {e}")
            if attempt < max_retries - 1:
                get_fresh_cookies()  # 这里使用正确的函数名
                time.sleep(3)
    
    return None

def main():
    # 定义三个频道的YouTube链接和台标
    channel_data = [
        {
            "name": "中天电视-1",
            "url": "https://www.youtube.com/watch?v=vr3XyVCR4T0",
            "logo": "https://raw.githubusercontent.com/pdd520/iptv-api/master/tv/CtiTV.png"
        },
        {
            "name": "中天新闻",
            "url": "https://www.youtube.com/watch?v=Df9kT_HB2NY",
            "logo": "https://raw.githubusercontent.com/pdd520/iptv-api/master/tv/CtiNews.png"
        },
        {
            "name": "中天电视-2",
            "url": "https://www.youtube.com/watch?v=U-NFviWcoQY",
            "logo": "https://raw.githubusercontent.com/pdd520/iptv-api/master/tv/CtiTV.png"
        }
    ]

    # 先获取一次新鲜的 cookies
    get_fresh_cookies()  # 这里使用正确的函数名

    # 获取每个频道的直播流地址
    for channel in channel_data:
        print(f"\n正在获取 {channel['name']} 的流地址...")
        stream_url = get_stream_url(channel["url"])
        channel["stream_url"] = stream_url if stream_url else ""
        if stream_url:
            print(f"✅ {channel['name']} 获取成功")
        else:
            print(f"❌ {channel['name']} 获取失败")

    # 追加到文件
    append_to_shanghai_txt(channel_data)
    append_to_m3u_file(channel_data)

if __name__ == "__main__":
    main()
