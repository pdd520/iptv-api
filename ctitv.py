import subprocess
import os
import requests
import json

def get_stream_url_ytdlp(youtube_url):
    """使用 yt-dlp 提取 YouTube 直播流地址（无认证方式）"""
    try:
        result = subprocess.run([
            "yt-dlp", 
            "--get-url",
            "--format", "best",
            youtube_url
        ], capture_output=True, text=True, check=True, timeout=30)
        
        stream_url = result.stdout.strip()
        if stream_url:
            print(f"✅ yt-dlp 方式成功: {youtube_url}")
            return stream_url
        else:
            print(f"❌ 无法获取流地址: {youtube_url}")
            return None
            
    except subprocess.CalledProcessError as e:
        print(f"❌ yt-dlp 方式失败: {e.stderr}")
        return None
    except Exception as e:
        print(f"❌ yt-dlp 方式错误: {e}")
        return None

def get_stream_url_youtube_api(youtube_url):
    """使用 YouTube Data API 获取直播流信息"""
    api_key = os.getenv('YOUTUBE_API_KEY')
    
    if not api_key:
        print("❌ 未设置 YOUTUBE_API_KEY")
        return None
    
    try:
        # 提取视频ID
        video_id = None
        if "v=" in youtube_url:
            video_id = youtube_url.split("v=")[1].split("&")[0]
        elif "youtu.be/" in youtube_url:
            video_id = youtube_url.split("youtu.be/")[1].split("?")[0]
        
        if not video_id:
            print("❌ 无法从URL中提取视频ID")
            return None
        
        # 调用 YouTube Data API
        api_url = f"https://www.googleapis.com/youtube/v3/videos"
        params = {
            'part': 'snippet,liveStreamingDetails',
            'id': video_id,
            'key': api_key
        }
        
        response = requests.get(api_url, params=params, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            if data.get('items'):
                item = data['items'][0]
                # 检查是否是直播
                if 'liveStreamingDetails' in item:
                    # 对于直播视频，我们可以获取直播流信息
                    print(f"✅ YouTube API 成功获取直播信息")
                    # 返回原始 YouTube URL，让 yt-dlp 处理
                    return youtube_url
                else:
                    print("❌ 该视频不是直播")
                    return None
            else:
                print("❌ 未找到视频信息")
                return None
        else:
            print(f"❌ YouTube API 请求失败: {response.status_code}")
            print(f"响应: {response.text}")
            return None
            
    except Exception as e:
        print(f"❌ YouTube API 错误: {e}")
        return None

def get_stream_url(youtube_url):
    """获取 YouTube 直播流地址（主函数）"""
    print(f"正在处理: {youtube_url}")
    
    # 首先尝试使用 YouTube API 验证直播状态
    api_result = get_stream_url_youtube_api(youtube_url)
    if api_result:
        # 如果 API 验证成功，使用 yt-dlp 获取实际流地址
        return get_stream_url_ytdlp(youtube_url)
    else:
        # 如果 API 失败，直接尝试 yt-dlp
        print("YouTube API 失败，直接尝试 yt-dlp...")
        return get_stream_url_ytdlp(youtube_url)

def append_to_m3u_file(channels, target_file="output/rtp/shanghai.m3u"):
    """将频道信息追加到目标 M3U 文件的底部"""
    # 确保输出目录存在
    os.makedirs(os.path.dirname(target_file), exist_ok=True)

    # 检查目标文件是否存在
    if os.path.exists(target_file):
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
        # 只添加有有效流地址的频道
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
        # 如果文件不存在，创建新文件
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

    # 写入更新后的内容到目标文件
    with open(target_file, "w", encoding="utf-8") as f:
        f.write(updated_content)
    print(f"频道已更新到 {target_file}")

def append_to_shanghai_txt(channels, target_file="config/rtp/shanghai.txt"):
    """将频道信息追加到 config/rtp/shanghai.txt 文件的底部"""
    os.makedirs(os.path.dirname(target_file), exist_ok=True)

    if os.path.exists(target_file):
        with open(target_file, "r", encoding="utf-8") as f:
            existing_content = f.read()
        
        # 移除旧的中天相关条目
        lines = existing_content.splitlines()
        updated_lines = [
            line for line in lines 
            if not any(name in line for name in ["中天电视-1", "中天电视-2", "中天新闻"])
        ]
        existing_content = "\n".join(updated_lines)
        
        # 只添加有有效流地址的频道
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
            print(f"✅ {channel['name']} 获取成功: {stream_url[:50]}...")
        else:
            print(f"❌ {channel['name']} 获取失败")

    # 追加到文件
    append_to_shanghai_txt(channel_data)
    append_to_m3u_file(channel_data)

if __name__ == "__main__":
    main()
