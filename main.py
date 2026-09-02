import aiohttp
from fastapi import FastAPI, Form, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

app = FastAPI(title="Vibe Downloader")
templates = Jinja2Templates(directory="templates")


# Универсальная функция извлечения прямой ссылки через стабильное внешнее API
async def get_video_url(video_url: str) -> str:
    # Используем бесплатное стабильное API для обхода блокировок IP
    api_endpoint = f"https://vreden.my.id{video_url}"

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(api_endpoint) as response:
                if response.status == 200:
                    result = await response.json()

                    if result.get("status") is True:
                        data = result.get("result", {})

                        # Если скачиваем с YouTube
                        if (
                            "youtube.com" in video_url
                            or "youtu.be" in video_url
                        ):
                            # Ищем ссылку в массиве или в корне ответа
                            return data.get("url") or data.get("video")

                        # Если скачиваем с TikTok
                        elif "tiktok.com" in video_url:
                            # Извлекаем чистое видео без водяного знака
                            return data.get("nowatermark") or data.get("video")
        return None
    except Exception as e:
        print(f"Ошибка парсинга через API: {e}")
        return None


@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@app.post("/download")
async def download_video(request: Request, url: str = Form(...)):
    # Проверяем валидность введенной ссылки
    is_valid_url = any(
        domain in url
        for domain in ["tiktok.com", "youtube.com", "youtu.be", "shorts"]
    )

    if not url or not is_valid_url:
        return templates.TemplateResponse(
            "index.html",
            {
                "request": request,
                "error": (
                    "Пожалуйста, введите корректную ссылку на TikTok или"
                    " YouTube."
                ),
            },
        )

    video_url = await get_video_url(url)

    if video_url:
        return templates.TemplateResponse(
            "index.html", {"request": request, "video_url": video_url}
        )
    else:
        return templates.TemplateResponse(
            "index.html",
            {
                "request": request,
                "error": (
                    "Не удалось извлечь видео. Возможно, оно приватное или"
                    " защита сервиса временно обновилась."
                ),
            },
        )
