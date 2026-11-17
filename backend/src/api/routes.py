
from datetime import datetime
from typing import Any

from fastapi import APIRouter, Body, Depends, HTTPException, Query
from pydantic import BaseModel, ConfigDict, ValidationError
from sqlalchemy import Column, DateTime, Integer, JSON, String, func
from sqlalchemy.orm import Session

from api.database import Base, get_db
from api import services
from schemas.request import UserRequest


class Solicitacao(Base):
    __tablename__ = "solicitacoes"

    id = Column(Integer, primary_key=True, index=True)
    dados = Column(JSON, nullable=False)
    status = Column(String(30), nullable=False, default="recebida")

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

class SolicitacaoCreate(BaseModel):
    dados: UserRequest


class SolicitacaoUpdate(BaseModel):
    dados: UserRequest | None = None
    status: str | None = None


class SolicitacaoResponse(BaseModel):
    id: int
    dados: UserRequest
    status: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

def create_crud_routes(
    model,
    schema_create,
    schema_update,
    schema_response,
    prefix: str,
    tags: list[str] | None = None,
):
    crud_router = APIRouter(
        prefix=prefix,
        tags=tags or [prefix.strip("/")],
    )

    @crud_router.post("/", response_model=schema_response, status_code=201)
    def create_item(
        data: dict[str, Any] = Body(...),
        db: Session = Depends(get_db),
    ):
        try:
            validated_data = schema_create.model_validate(data)
        except ValidationError as error:
            raise HTTPException(
                status_code=422,
                detail=error.errors(),
            ) from error

        return services.create(
            db=db,
            model=model,
            data=validated_data.model_dump(mode="json"),
        )

    @crud_router.get("/", response_model=list[schema_response])
    def get_items(
        skip: int = Query(0, ge=0),
        limit: int = Query(100, ge=1, le=500),
        db: Session = Depends(get_db),
    ):
        return services.get_all(
            db=db,
            model=model,
            skip=skip,
            limit=limit,
        )

    @crud_router.get("/{record_id}", response_model=schema_response)
    def get_item(
        record_id: int,
        db: Session = Depends(get_db),
    ):
        record = services.get_by_id(db, model, record_id)

        if record is None:
            raise HTTPException(
                status_code=404,
                detail="Registro não encontrado.",
            )

        return record

    @crud_router.put("/{record_id}", response_model=schema_response)
    def update_item(
        record_id: int,
        data: dict[str, Any] = Body(...),
        db: Session = Depends(get_db),
    ):
        record = services.get_by_id(db, model, record_id)

        if record is None:
            raise HTTPException(
                status_code=404,
                detail="Registro não encontrado.",
            )

        try:
            validated_data = schema_update.model_validate(data)
        except ValidationError as error:
            raise HTTPException(
                status_code=422,
                detail=error.errors(),
            ) from error

        return services.update(
            db=db,
            record=record,
            data=validated_data.model_dump(
                mode="json",
                exclude_unset=True,
                exclude_none=True,
            ),
        )

    @crud_router.delete("/{record_id}", status_code=204)
    def delete_item(
        record_id: int,
        db: Session = Depends(get_db),
    ):
        record = services.get_by_id(db, model, record_id)

        if record is None:
            raise HTTPException(
                status_code=404,
                detail="Registro não encontrado.",
            )

        services.delete(db, record)

    return crud_router

router = APIRouter()

router.include_router(
    create_crud_routes(
        model=Solicitacao,
        schema_create=SolicitacaoCreate,
        schema_update=SolicitacaoUpdate,
        schema_response=SolicitacaoResponse,
        prefix="/solicitacoes",
        tags=["Solicitações"],
    )
)
