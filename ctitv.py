import subprocess
import os

def get_stream_url(youtube_url):
    """使用 yt-dlp 提取 YouTube 直播流地址"""
    try:
        # 运行 yt-dlp 命令获取流地址，使用 cookies 文件
        result = subprocess.run(
            ["yt-dlp", "--get-url", "--cookies", "cookies.txt", youtube_url],
            capture_output=True, text=True, check=True
        )
        stream_url = result.stdout.strip()
        return stream_url
    except subprocess.CalledProcessError as e:
        print(f"错误：无法提取直播流地址 {e.stderr}")
        return None
    except FileNotFoundError:
        print("错误：找不到 cookies.txt 文件，请确保文件存在。")
        return None

def create_m3u_file(stream_url, output_path="output/ctitv.m3u"):
    """生成 M3U 文件"""
    if stream_url:
        m3u_content = """#EXTM3U
#EXTINF:-1, 中天新闻
{}
""".format(stream_url)
        
        # 确保输出目录存在
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        # 写入 M3U 文件
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(m3u_content)
        print(f"M3U 文件已生成：{output_path}")
    else:
        print("没有有效的流地址，无法生成 M3U 文件。")

def main():
    youtube_url = "https://www.youtube.com/watch?v=vr3XyVCR4T0"  # 中天新闻直播链接
    stream_url = get_stream_url(youtube_url)
    create_m3u_file(stream_url)

if __name__ == "__main__":
    main()
