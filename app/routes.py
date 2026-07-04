from fastapi import APIRouter

router = APIRouter()


@router.get("/weather")
async def get_weather():
    
    return {"city": "Rishikesh", "temp_c": 28, "condition": "clear"}


@router.get("/news")
async def get_news():
    return {"headlines": ["FastAPI 1.0 released", "LangGraph gains traction"]}


@router.get("/status")
async def get_status():
    return {"status": "ok", "version": "1.0.0"}