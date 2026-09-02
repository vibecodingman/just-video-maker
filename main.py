import aiohttp
from fastapi import FastAPI, Form, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

app = FastAPI(title="Vibe Downloader")
templates = Jinja2Templates(directory="templates")


# Универсальная функция извлечения прямой ссылки через глобальное API Cobalt
async def get_video_url(video_url: str) -> str:
    # Официальный публичный инстанс Cobalt API для обхода любых блокировок Google
    api_endpoint = "https://cobalt.tools"

    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json",
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        ),
    }

    # Настройки для получения лучшего качества со звуком
    payload = {
        "url": video_url,
        "videoQuality": "720",  # Оптимальное качество для быстрой отдачи
        "downloadMode": "auto",
    }

    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                api_endpoint, json=payload, headers=headers
            ) as response:
                if response.status == 200:
                    result = await response.json()

                    # Cobalt возвращает прямую ссылку в поле 'url' при статусе 'stream' или 'redirect'
                    if result.get("status") in ["stream", "redirect", "success"]:
                        return result.get("url")

                    # Если это фото-галерея TikTok, Cobalt может вернуть список картинок (picker)
                    elif result.get("status") == "picker":
                        picker_list = result.get("picker", [])
                        if picker_list and "url" in picker_list[0]:
                            return picker_list[0].get("url")

        return None
    except Exception as e:
        print(f"Ошибка Cobalt API: {e}")
        return None


@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@app.post("/download")
async def download_video(request: Request, url: str = Form(...)):
    # Валидация поддерживаемых доменов
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
                    "Не удалось извлечь видео. Возможно, сервис перегружен,"
                    " попробуйте еще раз через минуту."
                ),
            },
        )
