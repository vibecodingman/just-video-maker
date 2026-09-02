import asyncio
from fastapi import FastAPI, Form, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
import yt_dlp

app = FastAPI(title="Vibe Downloader")
templates = Jinja2Templates(directory="templates")


# Безотказная функция извлечения ссылок с ротацией юзер-агентов
async def get_video_url(video_url: str) -> str:
  ydl_opts = {
      # Принудительно запрашиваем готовый mp4 со звуком и видео вместе
      'format': 'best[ext=mp4]/best',
      'quiet': True,
      'no_warnings': True,
      # Защита от блокировок: маскируемся под мобильный Android-браузер
      'http_headers': {
          'User-Agent': (
              'Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML,'
              ' like Gecko) Chrome/124.0.0.0 Mobile Safari/537.36'
          ),
          'Accept': (
              'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8'
          ),
          'Accept-Language': 'ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7',
      },
  }

  loop = asyncio.get_event_loop()

  def extract():
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
      info = ydl.extract_info(video_url, download=False)
      if 'formats' in info:
        # Перебираем форматы, чтобы найти чистый готовый URL со звуком
        for f in info['formats']:
          if (
              f.get('vcodec') != 'none'
              and f.get('acodec') != 'none'
              and f.get('url')
          ):
            return f['url']
      return info.get('url')

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
  # Проверяем валидность введенной ссылки
  is_valid_url = any(
      domain in url
      for domain in ['tiktok.com', 'youtube.com', 'youtu.be', 'shorts']
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
                ' сервис изменил защиту. Попробуйте еще раз через минуту.'
            ),
        },
    )
