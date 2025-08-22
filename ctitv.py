import subprocess
import os
import time
import json
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException

def setup_selenium():
    """设置 Selenium WebDriver"""
    chrome_options = Options()
    chrome_options.add_argument("--headless=new")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--window-size=1920,1080")
    chrome_options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")
    
    # 设置中文语言
    chrome_options.add_argument("--lang=zh-CN")
    
    driver = webdriver.Chrome(options=chrome_options)
    return driver

def auto_solve_captcha(driver):
    """尝试自动处理验证码（基础版本）"""
    try:
        # 检查是否有验证码页面
        if "verify" in driver.current_url or "captcha" in driver.current_url.lower():
            print("检测到验证码页面，尝试自动处理...")
            
            # 等待验证码元素加载
            time.sleep(5)
            
            # 尝试点击可能的验证按钮
            try:
                verify_button = driver.find_element(By.XPATH, "//button[contains(text(), '验证')]")
                verify_button.click()
                print("点击验证按钮")
                time.sleep(3)
            except:
                pass
                
            # 尝试点击 "我不是机器人" 按钮
            try:
                not_robot = driver.find_element(By.XPATH, "//div[contains(text(), '我不是机器人')]")
                not_robot.click()
                print("点击'我不是机器人'")
                time.sleep(3)
            except:
                pass
                
            return True
    except Exception as e:
        print(f"验证码处理失败: {e}")
    
    return False

def get_fresh_cookies():
    """自动获取新的 YouTube cookies"""
    print("开始自动获取新的 YouTube cookies...")
    
    driver = setup_selenium()
    
    try:
        # 访问 YouTube 主页
        driver.get("https://www.youtube.com")
        print("访问 YouTube 主页")
        time.sleep(3)
        
        # 检查是否需要验证
        auto_solve_captcha(driver)
        
        # 等待页面加载完成
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.TAG_NAME, "body"))
        )
        
        # 获取 cookies
        cookies = driver.get_cookies()
        
        # 保存为 Netscape 格式的 cookies.txt
        with open('cookies.txt', 'w') as f:
            f.write("# Netscape HTTP Cookie File\n")
            for cookie in cookies:
                if cookie['domain'].endswith('youtube.com'):
                    f.write(f"{cookie['domain']}\tTRUE\t/\tTRUE\t{cookie.get('expiry', '0')}\t{cookie['name']}\t{cookie['value']}\n")
        
        print(f"成功获取 {len(cookies)} 个 cookies")
        return True
        
    except Exception as e:
        print(f"获取 cookies 失败: {e}")
        return False
        
    finally:
        driver.quit()

def get_stream_url_with_retry(youtube_url, max_retries=3):
    """带重试机制的获取流地址函数"""
    for attempt in range(max_retries):
        try:
            # 首先尝试使用现有 cookies
            if os.path.exists('cookies.txt'):
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
            
            # 如果失败，获取新的 cookies 并重试
            if attempt < max_retries - 1:
                print(f"尝试 {attempt + 1} 失败，获取新的 cookies...")
                get_fresh_cookies()
                time.sleep(2)  # 等待一下再重试
                
        except subprocess.CalledProcessError as e:
            print(f"❌ 尝试 {attempt + 1} 失败: {e.stderr}")
            if attempt < max_retries - 1:
                get_fresh_cookies()
                time.sleep(2)
        except Exception as e:
            print(f"❌ 尝试 {attempt + 1} 错误: {e}")
            if attempt < max_retries - 1:
                get_fresh_cookies()
                time.sleep(2)
    
    return None

def get_stream_url(youtube_url):
    """获取 YouTube 直播流地址"""
    print(f"正在处理: {youtube_url}")
    return get_stream_url_with_retry(youtube_url)

# 以下 append_to_m3u_file 和 append_to_shanghai_txt 函数保持不变
def append_to_m3u_file(channels, target_file="output/rtp/shanghai.m3u"):
    """将频道信息追加到目标 M3U 文件的底部"""
    os.makedirs(os.path.dirname(target_file), exist_ok=True)

    if os.path.exists(target_file):
        with open(target_file, "r", encoding="utf-8") as f:
            existing_content = f.read()
        
        lines = existing_content.splitlines()
        updated_lines = []
        skip_next = False
        for line in lines:
            if any(name in line for name in ["中天电视-1", "中天电视-2", "中天新闻"]):
                skip_next = True
                continue
            if skip_next:
                skip_next = False
                continue
            updated_lines.append(line)
        
        existing_content = "\n".join(updated_lines)
        valid_channels = [channel for channel in channels if channel.get("stream_url")]
        if valid_channels:
            new_entries = "\n".join([
                f'#EXTINF:-1 tvg-name="{channel["name"]}" tvg-logo="{channel["logo"]}" group-title="📺专题频道", {channel["name"]}\n{channel["stream_url"]}'
                for channel in valid_channels
            ])
            updated_content = existing_content.rstrip() + "\n" + new_entries
        else:
            updated_content = existing_content
    else:
        valid_channels = [channel for channel in channels if channel.get("stream_url")]
        if valid_channels:
            new_entries = "\n".join([
                f'#EXTINF:-1 tvg-name="{channel["name"]}" tvg-logo="{channel["logo"]}" group-title="📺专题频道", {channel["name"]}\n{channel["stream_url"]}'
                for channel in valid_channels
            ])
            updated_content = f"""#EXTM3U
{new_entries}"""
        else:
            updated_content = "#EXTM3U"

    with open(target_file, "w", encoding="utf-8") as f:
        f.write(updated_content)
    print(f"频道已更新到 {target_file}")

def append_to_shanghai_txt(channels, target_file="config/rtp/shanghai.txt"):
    """将频道信息追加到 config/rtp/shanghai.txt 文件的底部"""
    os.makedirs(os.path.dirname(target_file), exist_ok=True)

    if os.path.exists(target_file):
        with open(target_file, "r", encoding="utf-8") as f:
            existing_content = f.read()
        
        lines = existing_content.splitlines()
        updated_lines = [
            line for line in lines 
            if not any(name in line for name in ["中天电视-1", "中天电视-2", "中天新闻"])
        ]
        existing_content = "\n".join(updated_lines)
        
        valid_channels = [channel for channel in channels if channel.get("stream_url")]
        if valid_channels:
            new_entries = "\n".join([
                f'{channel["name"]},{channel["stream_url"]}'
                for channel in valid_channels
            ])
            updated_content = existing_content.rstrip() + "\n" + new_entries
        else:
            updated_content = existing_content
    else:
        valid_channels = [channel for channel in channels if channel.get("stream_url")]
        if valid_channels:
            new_entries = "\n".join([
                f'{channel["name"]},{channel["stream_url"]}'
                for channel in valid_channels
            ])
            updated_content = new_entries
        else:
            updated_content = ""

    with open(target_file, "w", encoding="utf-8") as f:
        f.write(updated_content)
    print(f"频道已更新到 {target_file}")

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
    get_fresh_cookies()

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
