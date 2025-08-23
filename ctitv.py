import subprocess
import os
import time
import json

def get_stream_url_direct(youtube_url):
    """直接使用 yt-dlp 获取流地址（不依赖 cookies）"""
    try:
        # 使用 yt-dlp 获取流信息
        result = subprocess.run([
            "yt-dlp", 
            "-g",  # 只获取 URL，不下载
            "-f", "best",  # 选择最佳格式
            "--no-check-certificates",
            "--user-agent", "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            youtube_url
        ], capture_output=True, text=True, timeout=30)
        
        if result.returncode == 0:
            stream_url = result.stdout.strip()
            if stream_url:
                print(f"✅ 直接获取成功: {stream_url[:80]}...")
                return stream_url
        
        # 如果失败，尝试其他方法
        return get_stream_url_fallback(youtube_url)
            
    except Exception as e:
        print(f"❌ 直接获取失败: {e}")
        return get_stream_url_fallback(youtube_url)

def get_stream_url_fallback(youtube_url):
    """备用方法：尝试多种方式获取流地址"""
    methods = [
        # 方法1: 使用默认格式
        ["yt-dlp", "-g", "-f", "best", youtube_url],
        # 方法2: 尝试 m3u8 格式
        ["yt-dlp", "-g", "-f", "best[ext=m3u8]", youtube_url],
        # 方法3: 尝试 http 格式
        ["yt-dlp", "-g", "-f", "best[protocol=https]", youtube_url],
        # 方法4: 不使用格式筛选
        ["yt-dlp", "-g", youtube_url],
    ]
    
    for i, method in enumerate(methods):
        try:
            result = subprocess.run(method, capture_output=True, text=True, timeout=20)
            if result.returncode == 0 and result.stdout.strip():
                stream_url = result.stdout.strip()
                print(f"✅ 备用方法 {i+1} 成功")
                return stream_url
        except:
            continue
    
    return None

def get_stream_url(youtube_url):
    """获取 YouTube 直播流地址"""
    print(f"正在处理: {youtube_url}")
    return get_stream_url_direct(youtube_url)

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
