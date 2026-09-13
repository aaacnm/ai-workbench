import os

from cryptography.fernet import Fernet, InvalidToken
from sqlalchemy import String, Text
from sqlalchemy.orm import Mapped, mapped_column

from .database import Base, SessionLocal


class StoredModelConfig(Base):
    __tablename__ = "model_config"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    provider: Mapped[str] = mapped_column(String(40))
    model_name: Mapped[str] = mapped_column(String(120))
    base_url: Mapped[str | None] = mapped_column(String(300), nullable=True)
    encrypted_api_key: Mapped[str | None] = mapped_column(Text, nullable=True)
    temperature: Mapped[float] = mapped_column(default=0.2)
    max_tokens: Mapped[int] = mapped_column(default=1024)
    timeout_seconds: Mapped[float] = mapped_column(default=30)


def _fernet() -> Fernet:
    key = os.getenv("CONFIG_ENCRYPTION_KEY")
    if not key:
        raise RuntimeError("未配置 CONFIG_ENCRYPTION_KEY，无法安全保存 API Key")
    try:
        return Fernet(key.encode())
    except (ValueError, TypeError) as exc:
        raise RuntimeError("CONFIG_ENCRYPTION_KEY 格式无效") from exc


def save_config(values: dict) -> None:
    with SessionLocal() as db:
        row = db.query(StoredModelConfig).filter_by(provider=values["provider"], model_name=values["model_name"]).first() or StoredModelConfig()
        for field in ("provider", "model_name", "base_url", "temperature", "max_tokens", "timeout_seconds"):
            setattr(row, field, values[field])
        if values.get("api_key"):
            row.encrypted_api_key = _fernet().encrypt(values["api_key"].encode()).decode()
        db.add(row)
        db.commit()


def load_config(provider: str | None = None, model_name: str | None = None) -> dict | None:
    with SessionLocal() as db:
        query = db.query(StoredModelConfig)
        if provider and model_name:
            query = query.filter_by(provider=provider, model_name=model_name)
        row = query.order_by(StoredModelConfig.id.desc()).first()
        if row is None:
            return None
        api_key = None
        if row.encrypted_api_key:
            try:
                api_key = _fernet().decrypt(row.encrypted_api_key.encode()).decode()
            except (RuntimeError, InvalidToken) as exc:
                raise RuntimeError("无法解密已保存的 API Key") from exc
        return {"provider": row.provider, "model_name": row.model_name, "base_url": row.base_url, "api_key": api_key, "temperature": row.temperature, "max_tokens": row.max_tokens, "timeout_seconds": row.timeout_seconds}


def list_configs() -> list[dict]:
    with SessionLocal() as db:
        return [{"provider": row.provider, "model_name": row.model_name, "base_url": row.base_url, "temperature": row.temperature, "max_tokens": row.max_tokens, "timeout_seconds": row.timeout_seconds, "api_key_configured": bool(row.encrypted_api_key)} for row in db.query(StoredModelConfig).order_by(StoredModelConfig.id.desc()).all()]


def clear_config(provider: str | None = None, model_name: str | None = None) -> None:
    with SessionLocal() as db:
        query = db.query(StoredModelConfig)
        if provider and model_name:
            query = query.filter_by(provider=provider, model_name=model_name)
        query.delete(synchronize_session=False)
        db.commit()


def delete_config(provider: str, model_name: str) -> None:
    with SessionLocal() as db:
        row = db.query(StoredModelConfig).filter_by(provider=provider, model_name=model_name).first()
        if row is not None:
            db.delete(row)
            db.commit()
