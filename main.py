import uvicorn
from fastapi import FastAPI
from ai_server import router as ai_router

app = FastAPI(title="AI Portfolio Analyzer")
app.include_router(ai_router)

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
