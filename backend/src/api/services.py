
from typing import Any

from sqlalchemy.orm import Session


def create(
    db: Session,
    model: type,
    data: dict[str, Any],
):
    try:
        record = model(**data)

        db.add(record)
        db.commit()
        db.refresh(record)

        return record

    except Exception:
        db.rollback()
        raise


def get_by_id(
    db: Session,
    model: type,
    record_id: int,
):
    return db.query(model).filter(
        model.id == record_id
    ).first()


def get_all(
    db: Session,
    model: type,
    skip: int = 0,
    limit: int = 100,
):
    return (
        db.query(model)
        .offset(skip)
        .limit(limit)
        .all()
    )


def update(
    db: Session,
    record,
    data: dict[str, Any],
):
    try:
        for field, value in data.items():
            setattr(record, field, value)

        db.commit()
        db.refresh(record)

        return record

    except Exception:
        db.rollback()
        raise


def delete(
    db: Session,
    record,
):
    try:
        db.delete(record)
        db.commit()

        return True

    except Exception:
        db.rollback()
        raise
