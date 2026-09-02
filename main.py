import asyncio
import aiohttp
from fastapi import FastAPI, Form, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
import yt_dlp

app = FastAPI(title="Vibe Downloader")
templates = Jinja2Templates(directory="templates")

# Запасной метод: локальный yt-dlp с жесткой маскировкой под мобильный Chrome
async def get_video_url_fallback(video_url: str) -> str:
    ydl_opts = {
        'format': 'best[ext=mp4]/best',
        'quiet': True,
        'no_warnings': True,
        'http_headers': {
            'User-Agent': 'Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Mobile Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
            'Accept-Language': 'ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7',
        }
    }
    loop = asyncio.get_event_loop()
    def extract():
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(video_url, download=False)
            if 'formats' in info:
                # Ищем прямой рабочий URL без разбивки на потоки
                for f in info['formats']:
                    if f.get('vcodec') != 'none' and f.get('acodec') != 'none' and f.get('url'):
                        return f['url']
            return info.get('url')
    try:
        return await loop.run_in_executor(None, extract)
    except Exception as e:
        print(f"Ошибка резервного yt-dlp: {e}")
        return None

# Основной метод через быстрое API
async def get_video_url(video_url: str) -> str:
    api_endpoint = f"https://vreden.my.id{video_url}"
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(api_endpoint) as response:
                if response.status == 200:
                    result = await response.json()
                    if result.get("status") is True:
                        data = result.get("result", {})
                        if "youtube.com" in video_url or "youtu.be" in video_url:
                            url = data.get("url") or data.get("video")
                            if url: return url
                        elif "tiktok.com" in video_url:
                            url = data.get("nowatermark") or data.get("video")
                            if url: return url
        
        # Если API не вернуло ссылку, включаем резервный метод
        print("API не справилось, запуск резервного yt-dlp...")
        return await get_video_url_fallback(video_url)
    except Exception as e:
        print(f"Ошибка основного API: {e}")
        return await get_video_url_fallback(video_url)

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.post("/download")
async def download_video(request: Request, url: str = Form(...)):
    is_valid_url = any(domain in url for domain in ["tiktok.com", "youtube.com", "youtu.be", "shorts"])
    if not url or not is_valid_url:
        return templates.TemplateResponse("index.html", {"request": request, "error": "Пожалуйста, введите корректную ссылку на TikTok или YouTube."})

    video_url = await get_video_url(url)
    if video_url:
        return templates.TemplateResponse("index.html", {"request": request, "video_url": video_url})
    else:
        return templates.TemplateResponse("index.html", {"request": request, "error": "Не удалось извлечь видео. Возможно, оно приватное или защита сервиса временно обновилась."})
