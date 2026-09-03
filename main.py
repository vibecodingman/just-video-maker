import aiohttp
from fastapi import FastAPI, Form, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

app = FastAPI(title="Vibe Downloader")
templates = Jinja2Templates(directory="templates")


# Полностью анонимная функция скачивания через свободный публичный шлюз
async def get_video_url(video_url: str) -> str:
  # Используем стабильное бесплатное API, не требующее ключей и карт
  api_endpoint = f'https://dilame.net{video_url}'

  try:
    async with aiohttp.ClientSession() as session:
      async with session.get(api_endpoint, timeout=12) as response:
        if response.status == 200:
          result = await response.json()

          if result.get('success') is True or result.get('status') == 'success':
            data = result.get('data', {})

            # Логика для TikTok
            if 'tiktok.com' in video_url:
              return (
                  data.get('nowatermark')
                  or data.get('video_url')
                  or data.get('url')
              )

            # Логика для YouTube / Shorts
            elif 'youtube.com' in video_url or 'youtu.be' in video_url:
              # Ищем лучший формат mp4 со звуком
              formats = data.get('formats', [])
              if formats:
                for f in formats:
                  if f.get('ext') == 'mp4' and f.get('acodec') != 'none':
                    return f.get('url')
                return formats[0].get('url')
              return data.get('url') or data.get('video_url')

        print(f'API ответило со статусом: {response.status}')
        return None
  except Exception as e:
    print(f'Ошибка анонимного API: {e}')
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
                'Не удалось извлечь видео. Возможно, защита сервиса временно'
                ' обновилась, попробуйте другую ссылку.'
            ),
        },
    )
