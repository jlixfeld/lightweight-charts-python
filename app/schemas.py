from __future__ import annotations

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel


class Instrument(BaseModel):
    id: int
    symbol: str
    description: Optional[str] = None

    model_config = {"from_attributes": True}


class InstrumentCreate(BaseModel):
    symbol: str
    description: Optional[str] = None


class OHLC(BaseModel):
    symbol: str
    timeframe: str
    time: datetime
    open: float
    high: float
    low: float
    close: float
    volume: Optional[float] = None
    extra: Optional[dict] = None


class OHLCCreate(BaseModel):
    symbol: str
    timeframe: str
    time: datetime
    open: float
    high: float
    low: float
    close: float
    volume: Optional[float] = None
    extra: Optional[dict] = None


class Metadata(BaseModel):
    symbols: List[str]
    timeframes: List[str]
    columns: List[str]
