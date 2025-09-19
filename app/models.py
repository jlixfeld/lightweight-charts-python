from __future__ import annotations

from sqlalchemy import Column, Integer, String, UniqueConstraint

from .database import Base


class Instrument(Base):
    __tablename__ = "instruments"

    id = Column(Integer, primary_key=True, autoincrement=True)
    symbol = Column(String(64), unique=True, nullable=False, index=True)
    description = Column(String(255), nullable=True)

    __table_args__ = (UniqueConstraint("symbol", name="uq_instrument_symbol"),)
