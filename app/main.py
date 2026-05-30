from fastapi import FastAPI

from app.scheduler import start_scheduler


app = FastAPI()


@app.on_event("startup")
def startup_event():
    start_scheduler()


@app.get("/")
def root():
    return {
        "status": "running"
    }