import os
import sys
import base64
import aiofiles
import pyzipper
import tempfile
import importlib.util
from datetime import datetime, timezone, timedelta
from fastapi.templating import Jinja2Templates
from fastapi import FastAPI, Form, Request, HTTPException, status
from fastapi.responses import JSONResponse, Response, RedirectResponse

try:
  with pyzipper.AESZipFile(base64.b64decode("X19zZWN1cmVfXw==").decode("utf-8"), 'r') as zf:
    zf.pwd = base64.b64decode(os.getenv(base64.b64decode("dWFwaQ==").decode(), "")).decode("utf-8").encode()
    file_data = zf.read(base64.b64decode("YXBpLnB5").decode("utf-8"))
  with tempfile.NamedTemporaryFile(suffix=base64.b64decode("LnB5").decode("utf-8"), delete=False) as temp_file:
    temp_file.write(file_data)
    temp_module_path = temp_file.name
  original_name = base64.b64decode("YXBp").decode("utf-8")
  new_name = base64.b64decode("dXZhcGk=").decode("utf-8")
  spec = importlib.util.spec_from_file_location(original_name, temp_module_path)
  uvapi = importlib.util.module_from_spec(spec)
  sys.modules[new_name] = uvapi
  spec.loader.exec_module(uvapi)
except:
  raise FileNotFoundError("Required files were not found.")


app = FastAPI()

templates = Jinja2Templates(directory=os.getcwd())

IST = timezone(timedelta(hours=5, minutes=30))

logincodes = ["mespider9123"]


def datetime_format(value):
    try:
        utc_time = datetime.fromisoformat(value)
        if utc_time.tzinfo is None:
            utc_time = utc_time.replace(tzinfo=timezone.utc)
        ist_time = utc_time.astimezone(IST)
        return ist_time.strftime("%d %b %Y, %I:%M %p IST")
    except Exception:
        return value

templates.env.filters["datetime_format"] = datetime_format

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
    try:
        final_url, duration_mins, duration_secs, videoid, ext, format, title, direct = await uvapi.direct_video_url(url, format, download=download, api_key=api_key, ip_address=ip_address)
        if not format:
            raise Exception(final_url)
        if direct:
            final_url = str(request.url_for("stream_video", filename=os.path.basename(final_url)))
        response_content = {'status': 'success', 'message': 'Link Successfully extracted.', 'title': title, 'videoid': videoid, 'ext': ext, 'format': format, 'duration_mins': duration_mins, 'duration_secs': duration_secs, 'url': final_url}
        return JSONResponse(content=response_content)
    except Exception as e:
        return JSONResponse(status_code=500, content={'status': 'failed', 'error': 'Unable to process your request. Please try again later.', 'details': str(e)})


@app.post("/youtubekeys/action")
async def yt_keys_action_handler(action: str = Form(...), api_key: str = Form(...), logincode: str = Form(...), max_requests: int = Form(500)):
    if action == "add_or_update":
        await uvapi.add_or_update_key(api_key, max_requests)
    elif action in ["block", "unblock"]:
        blocked = action == "block"
        await uvapi.update_block_status(api_key, blocked)
    elif action == "reset":
        await uvapi.add_or_update_key(api_key, max_requests=0, reset=True)
    else:
        return RedirectResponse(url=f"/youtube/manage?logincode={logincode}", status_code=303)

    return RedirectResponse(url=f"/youtube/manage?logincode={logincode}", status_code=303)


@app.get("/youtube/manage")
async def yt_keys_dashboard(request: Request, logincode: str = None):
    if logincode not in logincodes:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Unauthorized access.")
    rows = await uvapi.get_all_keys()
    keys = [{"api_key": row[0], "requests": row[1], "max_requests": row[2], "last_used": row[3], "blocked": row[4]} for row in rows]
    return templates.TemplateResponse("youtubedashboard.html", {"request": request, "keys": keys, "logincode": logincode})


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
  