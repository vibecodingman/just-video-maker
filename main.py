import asyncio
from fastapi import FastAPI, Form, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
import yt_dlp

app = FastAPI(title="Vibe Downloader")
templates = Jinja2Templates(directory="templates")


# Универсальная функция извлечения прямой ссылки (TikTok и YouTube)
async def get_video_url(video_url: str) -> str:
  ydl_opts = {
      'format': 'bestvideo+bestaudio/best/best',
      'quiet': True,
      'no_warnings': True,
      'http_headers': {
          'User-Agent': (
              'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
              ' (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
          ),
          'Accept': '*/*',
          'Accept-Language': 'en-US,en;q=0.9',
      },
  }

  loop = asyncio.get_event_loop()

  def extract():
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
      info = ydl.extract_info(video_url, download=False)
      return info.get('url') or info['formats'][0]['url']

  try:
    return await loop.run_in_executor(None, extract)
  except Exception as e:
    print(f'Ошибка парсинга: {e}')
    return None


@app.get('/', response_class=HTMLResponse)
async def home(request: Request):
  return templates.TemplateResponse('index.html', {'request': request})


@app.post('/download')
async def download_video(request: Request, url: str = Form(...)):
  # Проверяем, что ссылка принадлежит TikTok или YouTube
  is_valid_url = any(
      domain in url
      for domain in [
          'tiktok.com',
          'youtube.com',
          'youtu.be',
          'shorts',
      ]
  )

  if not url or not is_valid_url:
    return templates.TemplateResponse(
        'index.html',
        {
            'request': request,
            'error': (
                'Пожалуйста, введите корректную ссылку на TikTok или'
                ' YouTube.'
            ),
        },
    )

  video_url = await get_video_url(url)

  if video_url:
    return templates.TemplateResponse(
        'index.html', {'request': request, 'video_url': video_url}
    )
  else:
    return templates.TemplateResponse(
        'index.html',
        {
            'request': request,
            'error': (
                'Не удалось извлечь видео. Возможно, оно приватное или'
                ' сервис изменил защиту.'
            ),
        },
    )
