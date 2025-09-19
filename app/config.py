from __future__ import annotations

from functools import lru_cache
from typing import List

from pydantic import BaseModel, Field, field_validator
from pydantic_settings import BaseSettings


class DatasetConfig(BaseModel):
    """Describes how database columns map onto the OHLC schema expected by the app."""
    table: str = Field("ohlc", description="Name of the table or view that holds OHLC data")
    time_column: str = Field("time")
    open_column: str = Field("open")
    high_column: str = Field("high")
    low_column: str = Field("low")
    close_column: str = Field("close")
    volume_column: str | None = Field("volume")
    symbol_column: str = Field("symbol")
    timeframe_column: str = Field("timeframe")
    extra_columns: List[str] = Field(default_factory=list)

    @field_validator("table", "time_column", "open_column", "high_column", "low_column", "close_column", "symbol_column", "timeframe_column")
    @classmethod
    def validate_identifier(cls, value: str) -> str:
        if not isinstance(value, str):
            raise ValueError(f"Identifier must be a string: {value}")
        # Allow alphanumeric, underscore, but prevent SQL injection patterns
        cleaned = value.replace("_", "").replace("-", "")
        if not cleaned.isalnum() or len(value) > 64 or "--" in value or ";" in value:
            raise ValueError(f"Invalid SQL identifier: {value}")
        return value

    @field_validator("extra_columns", mode="before")
    @classmethod
    def split_extra_columns(cls, value):
        if isinstance(value, str):
            return [col.strip() for col in value.split(",") if col.strip()]
        return value


class Settings(BaseSettings):
    """Top-level application settings hydrated from environment variables."""
    database_url: str = Field(
        "postgresql+psycopg2://postgres:postgres@db:5432/ohlc",
        env="DATABASE_URL",
    )
    ohlc_limit: int = Field(0, ge=0, le=50_000)
    dataset: DatasetConfig = Field(default_factory=DatasetConfig)

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "env_nested_delimiter": "__"
    }


@lru_cache()
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
