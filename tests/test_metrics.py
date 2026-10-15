from pathlib import Path

import pandas as pd

from src.data import DataValidationError, validate_data
from src.metrics import (
    calculate_funnel,
    calculate_kpis,
    calculate_revenue_by_period,
    calculate_source_metrics,
    filter_data,
)


def sample_df():
    fixture = pd.read_csv(Path(__file__).parent / "fixtures" / "small_sample.csv")
    return validate_data(fixture)[0]


def test_kpis_are_calculated_correctly():
    kpis = calculate_kpis(sample_df())
    assert kpis["leads"] == 4
    assert kpis["won"] == 2
    assert kpis["revenue"] == 2500
    assert kpis["win_rate"] == 50
    assert kpis["average_won_deal"] == 1250


def test_funnel_is_cumulative():
    funnel = calculate_funnel(sample_df()).set_index("stage")
    assert funnel.loc["New", "leads"] == 4
    assert funnel.loc["Contacted", "leads"] == 4
    assert funnel.loc["Qualified", "leads"] == 3
    assert funnel.loc["Proposal", "leads"] == 2
    assert funnel.loc["Won", "leads"] == 2
    assert funnel.loc["Qualified", "conversion_from_previous_pct"] == 75.0


def test_revenue_is_grouped_by_close_month():
    revenue = calculate_revenue_by_period(sample_df())
    assert len(revenue) == 2
    assert revenue["revenue"].tolist() == [1000.0, 1500.0]


def test_source_metrics():
    metrics = calculate_source_metrics(sample_df()).set_index("source")
    assert metrics.loc["Web", "leads"] == 2
    assert metrics.loc["Web", "win_rate_pct"] == 50
    assert metrics.loc["Ads", "revenue"] == 1500


def test_filters_by_created_date_source_and_status():
    df = sample_df()
    result = filter_data(df, pd.Timestamp("2026-01-01").date(), pd.Timestamp("2026-01-31").date(), ["Web"], ["Won"])
    assert result["lead_id"].tolist() == ["L1"]


def test_validation_drops_invalid_rows_with_warning():
    raw = pd.concat(
        [
            pd.DataFrame([{"lead_id": "L1", "created_at": "2026-01-03", "source": "Web", "status": "Won", "stage": "Won", "deal_amount": 1000, "closed_at": "2026-01-10"}]),
            pd.DataFrame([{"lead_id": "L2", "created_at": "not-a-date", "source": "Ads", "status": "Won", "stage": "Won", "deal_amount": 500, "closed_at": "2026-01-12"}]),
        ],
        ignore_index=True,
    )
    clean, warnings = validate_data(raw)
    assert clean["lead_id"].tolist() == ["L1"]
    assert any("некорректных строк" in warning for warning in warnings)


def test_empty_input_raises_clear_validation_error():
    import pytest

    with pytest.raises(DataValidationError, match="Нет данных"):
        validate_data(pd.DataFrame())


def test_missing_required_columns_raises_clear_validation_error():
    import pytest

    with pytest.raises(DataValidationError, match="отсутствуют обязательные столбцы"):
        validate_data(pd.DataFrame([{"lead_id": "L1", "source": "Web"}]))
