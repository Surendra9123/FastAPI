import os
import json
import aiofiles
from api import direct_video_url
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse, Response

app = FastAPI()

youtube_keys = ['1spiderkey1']


@app.post("/api/youtube")
@app.get("/api/youtube")
async def download_video(request: Request):
    ip_address = request.headers.get('X-Forwarded-For', request.client.host)
    if ip_address and ',' in ip_address:
        ip_address = ip_address.split(',')[0]
    if request.method == 'POST':
        form_data = await request.form()
        url = form_data.get('url', None)
        format = form_data.get('format', 'audio')
        download = form_data.get('download', True)
        api_key = form_data.get('api_key', None)
    else:
        url = request.query_params.get('url', None)
        api_key = request.query_params.get('api_key', None)
        format = request.query_params.get('format', 'audio')
        download = request.query_params.get('download',True)
    if api_key not in youtube_keys:
        print(f"[{api_key}:Failed]: Invalid API key | {ip_address}")
        return JSONResponse(status_code=401, content={"status": "failed", "error": "Authentication failed: Invalid API key.", "details": "Authentication unsuccessful: The provided API key is invalid. Please contact at @ShraddhaNews for a new key."})
    try:
        final_url, duration_mins, duration_secs, videoid, ext, format, title, direct = await direct_video_url(url, format, download=download, api_key=api_key, ip_address=ip_address)
        if not final_url:
            raise Exception("An unknown error occurred..")
        if direct:
            final_url = str(request.url_for("stream_video", filename=os.path.basename(final_url)))
        response_content = {'status': 'success', 'message': 'Link Successfully extracted.', 'title': title, 'videoid': videoid, 'ext': ext, 'format': format, 'duration_mins': duration_mins, 'duration_secs': duration_secs, 'url': final_url}
        return JSONResponse(content=response_content)
    except Exception as e:
        return JSONResponse(status_code=500, content={'status': 'failed', 'error': 'Unable to process your request. Please try again later.', 'details': str(e)})


@app.get("/videos/{filename}")
async def stream_video(filename: str):
    video_path = os.path.join('downloads', filename)
    if not os.path.exists(video_path):
       raise HTTPException(status_code=404, detail="File not found")
    try:
      async with aiofiles.open(video_path, mode="rb") as file:
         content = await file.read()
      return Response(content, media_type="video/mp4") # return FileResponse(video_path, media_type='video/mp4')
    except Exception as e:
      raise HTTPException(status_code=500, detail=f"Something went wrong: {str(e)}")
  