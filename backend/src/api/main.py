
from contextlib import asynccontextmanager
from uuid import uuid4

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from .database import Base, engine
from .routes import router

from ..graph.checkpointer import (
    iniciar_checkpointer,
    fechar_checkpointer,
)
from ..graph.pomora_workflow import (
    inicializar_grafos,
    processar_mensagem_pomora,
)


Base.metadata.create_all(bind=engine)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Gerencia o ciclo de vida dos recursos do POMORA.

    Inicializa o PostgreSQL Checkpointer e os grafos
    antes de disponibilizar a API.
    """

    try:
        checkpointer = iniciar_checkpointer()

        inicializar_grafos(checkpointer)

        yield

    finally:
        fechar_checkpointer()


app = FastAPI(
    title="POMORA API",
    description="API de planejamento pedagógico com LangGraph.",
    version="1.2.0",
    lifespan=lifespan,
)

app.include_router(router)


class ChatRequest(BaseModel):
    message: str = Field(
        min_length=1,
        description="Mensagem enviada pelo usuário.",
    )

    thread_id: str | None = Field(
        default=None,
        description="Identificador da conversa.",
    )


class ChatResponse(BaseModel):
    thread_id: str
    intake: dict
    planning: dict | None = None


@app.get("/")
def home():
    return {
        "message": "POMORA API funcionando!",
        "version": "1.2.0",
    }


@app.post("/chat", response_model=ChatResponse)
def chat(data: ChatRequest):
    thread_id = data.thread_id or str(uuid4())

    try:
        resultado = processar_mensagem_pomora(
            mensagem=data.message,
            thread_id=thread_id,
        )

        return {
            "thread_id": thread_id,
            "intake": resultado["intake"],
            "planning": resultado.get("planning"),
        }

    except ValueError as error:
        raise HTTPException(
            status_code=422,
            detail=str(error),
        ) from error

    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail="Erro ao processar a conversa com os agentes.",
        ) from error
