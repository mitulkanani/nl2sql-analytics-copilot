from app.service import AnalyticsService


def test_monthly_revenue_question_returns_chart(analytics_service: AnalyticsService) -> None:
    result = analytics_service.query("Show monthly revenue trend")
    assert result.provider == "mock"
    assert result.chart_type == "line"
    assert result.chart_x == "month"
    assert result.chart_y == "revenue"
    assert result.rows
    assert result.sql.lstrip().lower().startswith("select")


def test_top_products_question_returns_ranked_results(analytics_service: AnalyticsService) -> None:
    result = analytics_service.query("Show top products by revenue")
    assert result.chart_type == "bar"
    assert result.rows[0]["revenue"] >= result.rows[-1]["revenue"]


def test_region_question_returns_regions(analytics_service: AnalyticsService) -> None:
    result = analytics_service.query("Compare sales by region")
    assert {row["region"] for row in result.rows} == {"North", "South", "East", "West"}


def test_query_is_saved_to_history(analytics_service: AnalyticsService) -> None:
    result = analytics_service.query("Count orders by status")
    history = analytics_service.history.list()
    assert len(history) == 1
    assert history[0]["query_id"] == result.query_id
