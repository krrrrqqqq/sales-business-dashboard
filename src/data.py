"""Loading and validation of lead/sales data."""
from __future__ import annotations

from io import BytesIO
from pathlib import Path
from typing import BinaryIO

import pandas as pd

REQUIRED_COLUMNS = {
    "lead_id", "created_at", "source", "status", "stage", "deal_amount", "closed_at"
}
STAGES = ["New", "Contacted", "Qualified", "Proposal", "Won"]
STATUSES = ["Open", "Won", "Lost"]


class DataValidationError(ValueError):
    """Raised when an input CSV cannot be used by the dashboard."""


def read_csv_file(file: BinaryIO | str | Path) -> pd.DataFrame:
    """Read a CSV path or uploaded file-like object with a helpful error message."""
    try:
        if isinstance(file, (str, Path)):
            return pd.read_csv(file)
        raw = file.getvalue() if hasattr(file, "getvalue") else file.read()
        if isinstance(raw, str):
            raw = raw.encode("utf-8")
        return pd.read_csv(BytesIO(raw))
    except pd.errors.EmptyDataError as exc:
        raise DataValidationError("CSV-файл пустой или в нём нет заголовков.") from exc
    except (pd.errors.ParserError, UnicodeDecodeError, OSError) as exc:
        raise DataValidationError(
            "Не удалось прочитать CSV. Проверьте кодировку UTF-8 и разделители столбцов."
        ) from exc


def validate_data(raw: pd.DataFrame) -> tuple[pd.DataFrame, list[str]]:
    """Validate, normalize and clean source rows; return data plus warnings.

    Invalid rows are removed rather than silently converted into plausible values.
    \`closed_at\` is required for closed deals and must not precede \`created_at\`.
    """
    if raw is None or raw.empty:
        raise DataValidationError("Нет данных: загрузите CSV с хотя бы одной строкой.")

    df = raw.copy()
    df.columns = [str(column).strip().lower() for column in df.columns]
    missing = sorted(REQUIRED_COLUMNS - set(df.columns))
    if missing:
        raise DataValidationError(
            "В CSV отсутствуют обязательные столбцы: " + ", ".join(missing)
        )

    warnings: list[str] = []
    initial_count = len(df)

    for col in ["lead_id", "source", "status", "stage"]:
        df[col] = df[col].astype("string").str.strip()
    df["status"] = df["status"].str.title()
    df["stage"] = df["stage"].str.title()
    df["source"] = df["source"].replace("", pd.NA)
    df["lead_id"] = df["lead_id"].replace("", pd.NA)
    raw_closed_at = df["closed_at"].copy()
    has_closed_at_value = raw_closed_at.notna() & raw_closed_at.astype(str).str.strip().ne("")
    df["created_at"] = pd.to_datetime(df["created_at"], errors="coerce")
    df["closed_at"] = pd.to_datetime(df["closed_at"], errors="coerce")
    df["deal_amount"] = pd.to_numeric(df["deal_amount"], errors="coerce")

    valid = (
        df["lead_id"].notna()
        & df["created_at"].notna()
        & df["source"].notna()
        & df["status"].isin(STATUSES)
        & df["stage"].isin(STAGES)
        & df["deal_amount"].notna()
        & df["deal_amount"].ge(0)
    )
    valid &= ~((df["status"].isin(["Won", "Lost"])) & df["closed_at"].isna())
    valid &= ~(has_closed_at_value & df["closed_at"].isna())
    valid &= ~((df["status"] == "Open") & df["closed_at"].notna())
    valid &= ~(df["closed_at"].notna() & (df["closed_at"] < df["created_at"]))
    valid &= ~((df["status"] == "Won") & (df["stage"] != "Won"))
    valid &= ~((df["status"] != "Won") & (df["stage"] == "Won"))

    rejected = int((~valid).sum())
    df = df.loc[valid].copy()
    if rejected:
        warnings.append(f"Пропущено некорректных строк: {rejected} из {initial_count}.")

    before_duplicates = len(df)
    df = df.drop_duplicates(subset="lead_id", keep="first").copy()
    duplicates = before_duplicates - len(df)
    if duplicates:
        warnings.append(f"Удалено строк с повторяющимся lead_id: {duplicates}.")

    if df.empty:
        raise DataValidationError(
            "После проверки не осталось корректных строк. Сверьте столбцы, даты, статусы и суммы."
        )

    df["source"] = df["source"].astype(str)
    df["lead_id"] = df["lead_id"].astype(str)
    df["deal_amount"] = df["deal_amount"].astype(float)
    df["stage_rank"] = df["stage"].map({stage: i for i, stage in enumerate(STAGES)})
    df = df.sort_values("created_at").reset_index(drop=True)
    return df, warnings


def load_and_validate(file: BinaryIO | str | Path) -> tuple[pd.DataFrame, list[str]]:
    """Convenience function to read and validate a CSV in one call."""
    return validate_data(read_csv_file(file))
