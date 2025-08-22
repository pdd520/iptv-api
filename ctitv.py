import subprocess
import os

def get_stream_url(youtube_url):
    """使用 yt-dlp 和 API Key 提取 YouTube 直播流地址"""
    api_key = os.getenv('YOUTUBE_API_KEY')
    
    if api_key:
        print("使用 API Key 方式获取流地址...")
        try:
            result = subprocess.run([
                "yt-dlp", 
                "--get-url",
                "--api-key", api_key,
                youtube_url
            ], capture_output=True, text=True, check=True, timeout=30)
            
            stream_url = result.stdout.strip()
            if stream_url:
                print(f"✅ API Key 方式成功: {youtube_url}")
                return stream_url
                
        except subprocess.CalledProcessError as e:
            print(f"❌ API Key 方式失败: {e.stderr}")
        except Exception as e:
            print(f"❌ API Key 方式错误: {e}")
    
    # API Key 方式失败或未设置，尝试无认证方式
    print("尝试无认证方式获取流地址...")
    try:
        result = subprocess.run([
            "yt-dlp", 
            "--get-url",
            youtube_url
        ], capture_output=True, text=True, check=True, timeout=30)
        
        stream_url = result.stdout.strip()
        if stream_url:
            print(f"✅ 无认证方式成功: {youtube_url}")
            return stream_url
        else:
            print(f"❌ 无法获取流地址: {youtube_url}")
            return None
            
    except subprocess.CalledProcessError as e:
        print(f"❌ 无认证方式失败: {e.stderr}")
        return None
    except Exception as e:
        print(f"❌ 无认证方式错误: {e}")
        return None

def append_to_m3u_file(channels, target_file="output/rtp/shanghai.m3u"):
    """将频道信息追加到目标 M3U 文件的底部"""
    # 确保输出目录存在
    os.makedirs(os.path.dirname(target_file), exist_ok=True)

    # 检查目标文件是否存在
    if os.path.exists(target_file):
        # 如果文件存在，读取现有内容
        with open(target_file, "r", encoding="utf-8") as f:
            existing_content = f.read()
        # 移除旧的中天相关条目
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
        # 追加新频道条目
        new_entries = "\n".join([
            f'#EXTINF:-1 tvg-name="{channel["name"]}" tvg-logo="{channel["logo"]}" group-title="📺专题频道", {channel["name"]}\n{channel["stream_url"]}'
            for channel in channels if channel["stream_url"]
        ])
        updated_content = existing_content.rstrip() + "\n" + new_entries
    else:
        # 如果文件不存在，直接写入新内容（包含头部信息）
        new_entries = "\n".join([
            f'#EXTINF:-1 tvg-name="{channel["name"]}" tvg-logo="{channel["logo"]}" group-title="📺专题频道", {channel["name"]}\n{channel["stream_url"]}'
            for channel in channels if channel["stream_url"]
        ])
        updated_content = f"""#EXTM3U
{new_entries}"""

    # 写入更新后的内容到目标文件
    with open(target_file, "w", encoding="utf-8") as f:
        f.write(updated_content)
    print(f"频道已追加到 {target_file}")

def append_to_shanghai_txt(channels, target_file="config/rtp/shanghai.txt"):
    """将频道信息追加到 config/rtp/shanghai.txt 文件的底部"""
    # 确保目标目录存在
    os.makedirs(os.path.dirname(target_file), exist_ok=True)

    # 检查目标文件是否存在
    if os.path.exists(target_file):
        # 如果文件存在，读取现有内容
        with open(target_file, "r", encoding="utf-8") as f:
            existing_content = f.read()
        # 移除旧的中天相关条目
        lines = existing_content.splitlines()
        updated_lines = [
            line for line in lines 
            if not any(name in line for name in ["中天电视-1", "中天电视-2", "中天新闻"])
        ]
        existing_content = "\n".join(updated_lines)
        # 追加新频道条目
        new_entries = "\n".join([
            f'{channel["name"]},{channel["stream_url"]}'
            for channel in channels if channel["stream_url"]
        ])
        updated_content = existing_content.rstrip() + "\n" + new_entries
    else:
        # 如果文件不存在，直接写入新内容
        new_entries = "\n".join([
            f'{channel["name"]},{channel["stream_url"]}'
            for channel in channels if channel["stream_url"]
        ])
        updated_content = new_entries

    # 写入更新后的内容到目标文件
    with open(target_file, "w", encoding="utf-8") as f:
        f.write(updated_content)
    print(f"频道已追加到 {target_file}")

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

    # 获取每个频道的直播流地址
    for channel in channel_data:
        print(f"正在获取 {channel['name']} 的流地址...")
        stream_url = get_stream_url(channel["url"])
        channel["stream_url"] = stream_url if stream_url else ""
        if stream_url:
            print(f"✅ {channel['name']} 获取成功")
        else:
            print(f"❌ {channel['name']} 获取失败")

    # 追加到文件
    append_to_shanghai_txt(channel_data)  # 追加到 config/rtp/shanghai.txt
    append_to_m3u_file(channel_data)  # 追加到 output/rtp/shanghai.m3u

if __name__ == "__main__":
    main()
