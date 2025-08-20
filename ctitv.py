import subprocess
import os

def get_stream_url(youtube_url):
    """使用 yt-dlp 提取 YouTube 直播流地址"""
    try:
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

def append_to_m3u_file(stream_url, target_file="output/rtp/shanghai.m3u"):
    """将中天新闻的频道信息追加到目标 M3U 文件的底部"""
    if stream_url:
        # 中天新闻的频道信息
        channel_entry = f"""#EXTINF:-1, 中天新闻
{stream_url}
"""
        # 确保输出目录存在
        os.makedirs(os.path.dirname(target_file), exist_ok=True)

        # 检查目标文件是否存在
        if os.path.exists(target_file):
            # 如果文件存在，读取现有内容
            with open(target_file, "r", encoding="utf-8") as f:
                existing_content = f.read()
            # 检查是否已存在中天新闻条目，如果存在则删除旧条目
            lines = existing_content.splitlines()
            updated_lines = []
            skip_next = False
            for line in lines:
                if "中天新闻" in line:
                    skip_next = True
                    continue
                if skip_next:
                    skip_next = False
                    continue
                updated_lines.append(line)
            existing_content = "\n".join(updated_lines)
            # 将新内容追加到现有内容后
            updated_content = existing_content.rstrip() + "\n" + channel_entry
        else:
            # 如果文件不存在，直接写入新内容（可以包含头部信息）
            updated_content = f"""#EXTM3U
{channel_entry}"""

        # 写入更新后的内容到目标文件
        with open(target_file, "w", encoding="utf-8") as f:
            f.write(updated_content)
        print(f"中天新闻频道已追加到 {target_file}")
    else:
        print("没有有效的流地址，无法追加到 M3U 文件。")

def append_to_shanghai_txt(stream_url, target_file="config/rtp/shanghai.txt"):
    """将中天新闻的频道信息追加到 config/rtp/shanghai.txt 文件的底部"""
    if stream_url:
        # 格式与 shanghai.txt 对齐：频道名,流地址
        channel_entry = f"中天新闻,{stream_url}"
        # 确保目标目录存在
        os.makedirs(os.path.dirname(target_file), exist_ok=True)

        # 检查目标文件是否存在
        if os.path.exists(target_file):
            # 如果文件存在，读取现有内容
            with open(target_file, "r", encoding="utf-8") as f:
                existing_content = f.read()
            # 检查是否已存在中天新闻条目，如果存在则删除旧条目
            lines = existing_content.splitlines()
            updated_lines = [line for line in lines if "中天新闻" not in line]
            existing_content = "\n".join(updated_lines)
            # 将新内容追加到现有内容后
            updated_content = existing_content.rstrip() + "\n" + channel_entry
        else:
            # 如果文件不存在，直接写入新内容
            updated_content = channel_entry

        # 写入更新后的内容到目标文件
        with open(target_file, "w", encoding="utf-8") as f:
            f.write(updated_content)
        print(f"中天新闻频道已追加到 {target_file}")
    else:
        print("没有有效的流地址，无法追加到 shanghai.txt 文件。")

def main():
    youtube_url = "https://www.youtube.com/watch?v=vr3XyVCR4T0"  # 中天新闻直播链接
    stream_url = get_stream_url(youtube_url)
    append_to_shanghai_txt(stream_url)  # 追加到 config/rtp/shanghai.txt
    append_to_m3u_file(stream_url)  # 追加到 output/rtp/shanghai.m3u

if __name__ == "__main__":
    main()
