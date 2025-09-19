from __future__ import annotations

from typing import Optional

from sqlalchemy import MetaData, Table, insert, select
from sqlalchemy.exc import IntegrityError, NoSuchTableError
from sqlalchemy.orm import Session

from . import models, schemas
from .config import settings
from .database import SessionLocal


class InstrumentNotFound(Exception):
    """Raised when OHLC inserts reference an unknown symbol."""


_dataset_table: Table | None = None
_dataset_metadata = MetaData()


def _get_dataset_table(session: Session) -> Table:
    global _dataset_table
    if _dataset_table is None:
        cfg = settings.dataset
        try:
            _dataset_table = Table(
                cfg.table,
                _dataset_metadata,
                autoload_with=session.get_bind(),
                extend_existing=True,
            )
        except NoSuchTableError as exc:
            raise RuntimeError(
                f"Dataset table '{cfg.table}' not found. Ensure the database is seeded."
            ) from exc
    return _dataset_table


def create_instrument(db: Session, payload: schemas.InstrumentCreate) -> schemas.Instrument:
    instance = models.Instrument(symbol=payload.symbol, description=payload.description)
    try:
        db.add(instance)
        db.commit()
    except IntegrityError:
        db.rollback()
        instance = (
            db.query(models.Instrument)
            .filter(models.Instrument.symbol == payload.symbol)
            .one()
        )
        if payload.description and instance.description != payload.description:
            instance.description = payload.description
            db.commit()
    db.refresh(instance)
    return schemas.Instrument.from_orm(instance)


def create_ohlc(db: Session, payload: schemas.OHLCCreate) -> schemas.OHLC:
    instrument = (
        db.query(models.Instrument)
        .filter(models.Instrument.symbol == payload.symbol)
        .one_or_none()
    )
    if instrument is None:
        raise InstrumentNotFound(f"Instrument '{payload.symbol}' not found.")

    table = _get_dataset_table(db)
    cfg = settings.dataset

    record = {
        cfg.time_column: payload.time,
        cfg.open_column: payload.open,
        cfg.high_column: payload.high,
        cfg.low_column: payload.low,
        cfg.close_column: payload.close,
        cfg.symbol_column: payload.symbol,
        cfg.timeframe_column: payload.timeframe,
    }

    if cfg.volume_column:
        record[cfg.volume_column] = payload.volume

    if payload.extra:
        for column in cfg.extra_columns:
            if column in payload.extra:
                record[column] = payload.extra[column]

    stmt = insert(table).values(record)
    db.execute(stmt)
    db.commit()

    return schemas.OHLC(
        symbol=payload.symbol,
        timeframe=payload.timeframe,
        time=payload.time,
        open=payload.open,
        high=payload.high,
        low=payload.low,
        close=payload.close,
        volume=payload.volume,
        extra={k: payload.extra.get(k) for k in cfg.extra_columns} if payload.extra else None,
    )


def list_ohlc(
    db: Session,
    symbol: Optional[str] = None,
    timeframe: Optional[str] = None,
    limit: Optional[int] = None,
) -> list[schemas.OHLC]:
    table = _get_dataset_table(db)
    cfg = settings.dataset

    limit_value = min(limit or settings.ohlc_limit, settings.ohlc_limit)

    extra_cols = [col for col in cfg.extra_columns if col in table.c]

    stmt = select(
        table.c[cfg.symbol_column].label("symbol"),
        table.c[cfg.timeframe_column].label("timeframe"),
        table.c[cfg.time_column].label("time"),
        table.c[cfg.open_column].label("open"),
        table.c[cfg.high_column].label("high"),
        table.c[cfg.low_column].label("low"),
        table.c[cfg.close_column].label("close"),
        *(table.c[cfg.volume_column].label("volume"),) if cfg.volume_column else (),
        *(table.c[col].label(col) for col in extra_cols),
    )
    if symbol:
        stmt = stmt.where(table.c[cfg.symbol_column] == symbol)
    if timeframe:
        stmt = stmt.where(table.c[cfg.timeframe_column] == timeframe)

    stmt = stmt.order_by(table.c[cfg.time_column]).limit(limit_value)

    results = db.execute(stmt).all()

    output: list[schemas.OHLC] = []
    for row in results:
        row_dict = row._mapping
        extra_data = {
            col: row_dict[col]
            for col in extra_cols
            if row_dict.get(col) is not None
        } or None
        output.append(
            schemas.OHLC(
                symbol=row_dict["symbol"],
                timeframe=row_dict["timeframe"],
                time=row_dict["time"],
                open=row_dict["open"],
                high=row_dict["high"],
                low=row_dict["low"],
                close=row_dict["close"],
                volume=row_dict.get("volume") if cfg.volume_column else None,
                extra=extra_data,
            )
        )
    return output


def get_metadata(db: Session) -> schemas.Metadata:
    table = _get_dataset_table(db)
    cfg = settings.dataset

    symbol_stmt = (
        select(table.c[cfg.symbol_column])
        .distinct()
        .order_by(table.c[cfg.symbol_column])
    )
    timeframe_stmt = (
        select(table.c[cfg.timeframe_column])
        .distinct()
        .order_by(table.c[cfg.timeframe_column])
    )

    symbols = [row[0] for row in db.execute(symbol_stmt)]
    timeframes = [row[0] for row in db.execute(timeframe_stmt)]
    columns = [column.name for column in table.columns]

    return schemas.Metadata(symbols=symbols, timeframes=timeframes, columns=columns)


def build_chart_state(symbol: Optional[str] = None, timeframe: Optional[str] = None) -> dict:
    with SessionLocal() as db:
        try:
            metadata = get_metadata(db)
        except RuntimeError as exc:
            return {
                "symbols": [],
                "timeframes": [],
                "activeSymbol": None,
                "activeTimeframe": None,
                "limit": settings.ohlc_limit,
                "volumeEnabled": bool(settings.dataset.volume_column),
                "error": str(exc),
            }

    available_symbols = metadata.symbols
    timeframes = [tf for tf in metadata.timeframes if tf]

    active_symbol = symbol if symbol and symbol in available_symbols else (available_symbols[0] if available_symbols else None)
    if not timeframes:
        active_timeframe = None
    else:
        active_timeframe = timeframe if timeframe in timeframes else timeframes[0]

    return {
        "symbols": available_symbols,
        "timeframes": timeframes,
        "activeSymbol": active_symbol,
        "activeTimeframe": active_timeframe,
        "limit": settings.ohlc_limit,
        "volumeEnabled": bool(settings.dataset.volume_column),
        "error": None,
    }
