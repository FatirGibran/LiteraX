from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from literax.api.routes import router
from literax.config import settings

app = FastAPI(
    title="LiteraX API",
    description="AI-Powered Academic Research Assistant & Multi-Source Engine",
    version="0.1.0"
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "service": "LiteraX API Gateway",
        "version": "0.1.0"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
