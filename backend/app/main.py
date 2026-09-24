from fastapi import FastAPI

app = FastAPI(
    title="Emotional Mapping API",
    description="Backend API for the Emotional Mapping filmmaking tool",
    version="0.1.0",
)


@app.get("/")
def health_check():
    return {
        "status": "Emotional Mapping backend is running"
    }


@app.get("/health")
def health():
    return {
        "status": "healthy"
    }