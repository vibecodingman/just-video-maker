import aiohttp
from fastapi import FastAPI, Form, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

app = FastAPI(title="Vibe Downloader")
templates = Jinja2Templates(directory="templates")

# Ваш проверенный ключ из RapidAPI
RAPIDAPI_KEY = "8aa121c8d0mshc92246aa33b6e2fp182f38jsn13d2d10fc09b"


# Рекурсивный поиск любой рабочей ссылки в JSON ответе
def find_url_in_dict(data):
  if isinstance(data, str) and (
      data.startswith('http://') or data.startswith('https://')
  ):
    if '.mp4' in data or 'googlevideo' in data or 'tiktokcdn' in data:
      return data
  if isinstance(data, dict):
    for key, value in data.items():
      # Приоритет для чистых видео без водяных знаков
      if key in ['nowatermark', 'url', 'video', 'link', 'download_url']:
        res = find_url_in_dict(value)
        if res:
          return res
      res = find_url_in_dict(value)
      if res:
        return res
  if isinstance(data, list):
    for item in data:
      res = find_url_in_dict(item)
      if res:
        return res
  return None


async def get_video_url(video_url: str) -> str:
  # Используем самый популярный и стабильный шлюз на маркетплейсе
  api_url = 'https://rapidapi.com'

  payload = {'url': video_url}

  headers = {
      'x-rapidapi-key': RAPIDAPI_KEY,
      'x-rapidapi-host': '://rapidapi.com',
      'Content-Type': 'application/json',
  }

  try:
    async with aiohttp.ClientSession() as session:
      async with session.post(
          api_url, json=payload, headers=headers, timeout=15
      ) as response:
        if response.status == 200:
          result = await response.json()

          # Запускаем умный поиск ссылки внутри ответа API
          direct_url = find_url_in_dict(result)
          if direct_url:
            return direct_url
        else:
          print(f'API вернуло статус: {response.status}')
    return None
  except Exception as e:
    print(f'Ошибка вызова RapidAPI: {e}')
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
                'Не удалось извлечь видео. Убедитесь, что вы активировали'
                ' бесплатный тариф на RapidAPI (нажали Subscribe).'
            ),
        },
    )
