import yt_dlp
import asyncio
import logging
import os, glob, re, time
from youtubesearchpython import VideosSearch

COOKIES_SUPPORT = True
MAX_AUDIOPLAY_DURATION = 150
MAX_VIDEOPLAY_DURATION = 150
DOWNLOAD_FOLDER = "./downloads"
os.makedirs(DOWNLOAD_FOLDER, exist_ok=True)
cookies_txt_files = glob.glob("./cookies/*.txt")
cookie_files = [file for file in cookies_txt_files]
user_agent = "Mozilla/5.0 (iPhone; CPU iPhone OS 10_3 like Mac OS X) AppleWebKit/602.1.50 (KHTML, like Gecko) CriOS/56.0.2924.75 Mobile/14E5239e Safari/602.1"
http_headers = {"X-YouTube-Client-Name": "1", "X-YouTube-Client-Version": "16.20"}
REPEAT_LIMIT = 1

async def get_proxy_url():
  return None #PROXY_URL

async def cookie_txt_file():
  if not COOKIES_SUPPORT:
    return None
  global index, repeat_count
  try: index, repeat_count
  except: index, repeat_count = -1, 0
  if not cookies_txt_files:
    raise FileNotFoundError("No .txt files found in the specified folder.")
  if repeat_count >= REPEAT_LIMIT:
    index += 1
    repeat_count = 0
  if index >= len(cookie_files):
    index = 0
  repeat_count += 1
  return cookie_files[index] 


def get_common_ydl_opts(format, outtmpl, proxy_url, cookie_file, extra_opts=None):
     opts = {"format": format,
      "outtmpl": outtmpl,
      "geo-bypass": True,
      "nocheckcertificate": True,
      "quiet": True,
      "progress": True,
      "no_warnings": True,
      "http_chunk_size": 4 * 1024 * 1024,
      "concurrent_fragments": 512,
      "hls_prefer_native": True,
      "rm-cache-dir": True,
      "user-agent": user_agent,
      "http-headers": http_headers,
      "proxy": proxy_url,
      "cookiefile": cookie_file}
     if extra_opts:
         opts.update(extra_opts)
     return opts

def check_file_exists(url, isvideo):
    video_id_pattern = re.compile(r'(?:youtube\.com/(?:watch\?v=|shorts/|live/|embed/|v/|user/[^/]+/|c/[^/]+/live)|youtu\.be/)([a-zA-Z0-9_-]+)')
    match = video_id_pattern.search(url)
    videoid = match.group(1) if match else url
    matching_files = glob.glob(f"{os.getcwd()}/downloads/{videoid}+*{'video' if isvideo else 'audio'}.*")
    if matching_files:
      for file_path in matching_files:
        file_extension = os.path.splitext(file_path)[1].lstrip('.')
        return file_path, file_extension, videoid
    return None, None, None


def ytdetails(videoid):
  results = VideosSearch(videoid, limit=1).result()
  for result in results["result"]:
    title = result["title"]
    duration_mins = result["duration"]
    thumbnail = result["thumbnails"][0]["url"].split("?")[0]
    vidid = result["id"]
    if str(duration_mins) == "None":
      duration_secs, duration_mins = 0, 0
    else:
      duration_secs = int(sum(int(x) * 60**i for i, x in enumerate(reversed(str(duration_mins).split(":")))))
      duration_mins = duration_secs / 60
    return duration_mins, duration_secs, videoid, title

def audio_dl(link, proxy_url, cookie_file, download):
   file_path, ext, videoid = check_file_exists(link, isvideo=False)
   if file_path:
      duration_mins, duration_secs, videoid, title = ytdetails(videoid)
      return file_path, duration_mins, duration_secs, videoid, ext, title, False, True
   opts = get_common_ydl_opts("bestaudio/best", f"{os.getcwd()}/downloads/%(id)s.%(ext)s", proxy_url=proxy_url, cookie_file=cookie_file, extra_opts={"prefer_ffmpeg": True}) #139/599/140
   x = yt_dlp.YoutubeDL(opts)
   info = x.extract_info(link, False)
   url, duration_mins, duration_secs, videoid, ext, title = info.get("url"), (info.get("duration") / 60), info.get("duration"), info['id'], info['ext'], info['title']
   if not url and "formats" in info:
    for fmt in info["formats"]:
      if fmt.get("url") and fmt.get("acodec") != "none":
        url,ext = fmt.get("url"),fmt.get("ext")
        break
   if download and (duration_mins != 0 and duration_mins < MAX_AUDIOPLAY_DURATION):
      xyz = f"{os.getcwd()}/downloads/{info['id']}+{str(time.time()).replace('.','')}audio.{info['ext']}"
      if os.path.exists(xyz):
        return xyz, duration_mins, duration_secs, videoid, ext, title, True, True
      yt_dlp.YoutubeDL(get_common_ydl_opts(None, xyz, proxy_url, cookie_file)).download([url])
      return xyz, duration_mins, duration_secs, videoid, ext, title, True, True
   return url, duration_mins, duration_secs, videoid, ext, title, True, False

      
def video_dl(link, proxy_url, cookie_file, download):
   file_path, ext, videoid = check_file_exists(link, isvideo=True)
   if file_path:
      duration_mins, duration_secs, videoid, title = ytdetails(videoid)
      return file_path, duration_mins, duration_secs, videoid, ext, title, False, True
   opts = get_common_ydl_opts("(bestvideo[height<=?360][width<=?640][ext=mp4])+(bestaudio[ext=m4a])",f"{os.getcwd()}/downloads/%(id)s.%(ext)s",proxy_url=proxy_url, cookie_file=cookie_file, extra_opts=None)
   x = yt_dlp.YoutubeDL(opts)
   info = x.extract_info(link, False)
   url, duration_mins, duration_secs, videoid, ext, title = info.get("url"), (info.get("duration") / 60), info.get("duration"), info['id'], info['ext'], info['title']
   if not url and "formats" in info:
     for fmt in info["formats"]:
       if fmt.get("url") and fmt.get("vcodec") != "none" and fmt.get("acodec") != "none":
         url, ext = fmt.get("url"), fmt.get("ext")
         break
   if download and (duration_mins != 0 and duration_mins < MAX_VIDEOPLAY_DURATION):
      xyz = f"{os.getcwd()}/downloads/{info['id']}+{str(time.time()).replace('.','')}video.{info['ext']}"
      if os.path.exists(xyz):
        return xyz, duration_mins, duration_secs, videoid, ext, title, True, True
      yt_dlp.YoutubeDL(get_common_ydl_opts(None, xyz, proxy_url, cookie_file)).download([url])
      return xyz, duration_mins, duration_secs, videoid, ext, title, True, True
   return url, duration_mins, duration_secs, videoid, ext, title, True, False

def get_file_size(path):
    try: size = os.path.getsize(path)
    except: return "0.00MB"
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size < 1024:
            return f"{size:.2f}{unit}"
        size /= 1024

async def direct_video_url(link, format=None, videoid=None, download=False, api_key=None, ip_address=None):
 try:
   format = 'video' if format=='video' else 'audio'
   if videoid:
       base = "https://www.youtube.com/watch?v="
       link = base + link
   loop = asyncio.get_running_loop()
   cookie_file = await cookie_txt_file()
   proxy_url = await get_proxy_url()
   if format=='video':
      final_url, duration_mins, duration_secs, videoid, ext, title, login, direct = await loop.run_in_executor(None, video_dl, link, proxy_url, cookie_file, download)
   else:
      final_url, duration_mins, duration_secs, videoid, ext, title, login, direct = await loop.run_in_executor(None, audio_dl, link, proxy_url, cookie_file, download)
   if not final_url:
      print(f"YouTube Error while processing this Url : {link}")
      return "🤷 Unknown Issue", None, None, None, None, None, None, None
   print(f"[{api_key}:{login}]: {os.path.basename(cookie_file)} | {videoid}.{ext}({get_file_size(final_url)}) | {ip_address}")
   return final_url, duration_mins, duration_secs, videoid, ext, format, title, direct
 except Exception as exp:
   print(f"{exp}\n\nYouTube Error while processing this Url : {link} [{os.path.basename(cookie_file)} | {repeat_count}/{REPEAT_LIMIT}]")
   return exp, None, None, None, None, None, None, None