import aiohttp
from fastapi import FastAPI, Form, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

app = FastAPI(title="Vibe Downloader")
templates = Jinja2Templates(directory="templates")


# Неубиваемая функция на базе промышленного шлюза SaveFrom
async def get_video_url(video_url: str) -> str:
  # Используем шлюз SaveFrom, у которого всегда чистые прокси и нет лимитов
  api_endpoint = 'https://savefrom.net'

  payload = {'url': video_url}

  headers = {
      'User-Agent': (
          'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
      ),
      'Accept': 'application/json',
      'Content-Type': 'application/json',
  }

  try:
    async with aiohttp.ClientSession() as session:
      async with session.post(
          api_endpoint, json=payload, headers=headers, timeout=12
      ) as response:
        if response.status == 200:
          result = await response.json()

          # Парсим ответ от SaveFrom
          if 'url' in result:
            # Ссылка на обычное видео
            return result.get('url')

          elif 'url' in result.get('url', [{}])[0]:
            # Если ссылки вернулись в массиве вариантов (для YouTube)
            formats = result.get('url', [])
            for f in formats:
              # Ищем видео, где сразу склеен звук (audio) и картинка
              if f.get('audio') and f.get('url'):
                return f.get('url')
            return formats[0].get('url')
    return None
  except Exception as e:
    print(f'Ошибка работы шлюза: {e}')
    return None


@app.get('/', response_class=HTMLResponse)
async def home(request: Request):
  return templates.TemplateResponse('index.html', {'request': request})


@app.post('/download')
async def download_video(request: Request, url: str = Form(...)):
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
                'Не удалось извлечь видео. Возможно, сервис перегружен,'
                ' попробуйте еще раз через минуту.'
            ),
        },
    )
