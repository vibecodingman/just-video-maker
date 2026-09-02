import asyncio
from fastapi import FastAPI, Form, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
import yt_dlp

app = FastAPI(title="TikTok Downloader")
templates = Jinja2Templates(directory="templates")


# Функция извлечения прямой ссылки без водяного знака
async def get_tiktok_video_url(tiktok_url: str) -> str:
  # Настройки yt-dlp для TikTok
  ydl_opts = {
      'format': 'bestvideo+bestaudio/best',
      'quiet': True,
      'no_warnings': True,
      # Эмуляция браузера, чтобы TikTok не забанил по IP
      'http_headers': {
          'User-Agent': (
              'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
              ' (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
          ),
          'Accept': '*/*',
          'Accept-Language': 'en-US,en;q=0.9',
      },
  }

  # Запуск тяжелой синхронной библиотеки в асинхронном потоке
  loop = asyncio.get_event_loop()

  def extract():
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
      info = ydl.extract_info(tiktok_url, download=False)
      # Пытаемся взять чистую ссылку из форматов или основного url
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
  if not url or 'tiktok.com' not in url:
    return templates.TemplateResponse(
        'index.html',
        {
            'request': request,
            'error': (
                'Пожалуйста, введите корректную ссылку на видео TikTok.'
            ),
        },
    )

  video_url = await get_tiktok_video_url(url)

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
                'Не удалось извлечь видео. Возможно, ссылка приватная или'
                ' TikTok обновил защиту.'
            ),
        },
    )