import aiohttp
from fastapi import FastAPI, Form, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

app = FastAPI(title="Vibe Downloader")
templates = Jinja2Templates(directory="templates")

# Вставьте ваш скопированный секретный ключ из RapidAPI между кавычек
RAPIDAPI_KEY = "8aa121c8d0mshc92246aa33b6e2fp182f38jsn13d2d10fc09b"


async def get_video_url(video_url: str) -> str:
    # Используем стабильный шлюз RapidAPI, обходящий любые баны хостингов
    api_url = "https://rapidapi.com"

    payload = {"url": video_url}

    headers = {
        "x-rapidapi-key": RAPIDAPI_KEY,
        "x-rapidapi-host": "popular-video-downloader.p.rapidapi.com",
        "Content-Type": "application/json",
    }

    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                api_url, json=payload, headers=headers, timeout=15
            ) as response:
                if response.status == 200:
                    result = await response.json()

                    # Извлекаем прямую ссылку в зависимости от структуры ответа API
                    if "result" in result:
                        data = result.get("result", {})
                        # Возвращает чистый линк без водяных знаков или лучший поток
                        return (
                            data.get("url")
                            or data.get("nowatermark")
                            or data.get("video")
                        )
                    elif "url" in result:
                        return result.get("url")
        return None
    except Exception as e:
        print(f"Ошибка вызова RapidAPI: {e}")
        return None


@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@app.post("/download")
async def download_video(request: Request, url: str = Form(...)):
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
                    "Не удалось извлечь видео через шлюз. Возможно, ссылка"
                    " неверна или лимиты тарифа исчерпаны."
                ),
            },
        )
