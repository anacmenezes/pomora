
from fastapi import FastAPI

from api.database import Base, engine
from api.routes import router

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="POMORA API",
    description="API de gerenciamento de solicitações pedagógicas.",
    version="1.0.0",
)

app.include_router(router)


@app.get("/")
def home():
    return {
        "message": "POMORA API funcionando!",
        "version": "1.0.0",
    }
