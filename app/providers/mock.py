from app.models import GeneratedQuery


class MockQueryProvider:
    """Deterministic provider for local development, demos, and CI."""

    name = "mock"

    def generate(self, question: str, schema: str) -> GeneratedQuery:
        text = question.lower()
        if any(token in text for token in ("top product", "best-selling product", "best selling product", "product revenue")):
            return GeneratedQuery(
                sql="""SELECT p.name AS product, SUM(oi.quantity * oi.unit_price) AS revenue
FROM order_items oi
JOIN products p ON p.id = oi.product_id
JOIN orders o ON o.id = oi.order_id
WHERE o.status = 'completed'
GROUP BY p.id, p.name
ORDER BY revenue DESC
LIMIT 10""",
                explanation="Ranks products by completed-order line-item revenue.",
                chart_type="bar", chart_x="product", chart_y="revenue",
            )
        if "month" in text or "monthly" in text or "trend" in text:
            return GeneratedQuery(
                sql="""SELECT substr(order_date, 1, 7) AS month, SUM(total_amount) AS revenue
FROM orders
WHERE status = 'completed'
GROUP BY substr(order_date, 1, 7)
ORDER BY month""",
                explanation="Shows completed-order revenue grouped by calendar month.",
                chart_type="line", chart_x="month", chart_y="revenue",
            )
        if "region" in text:
            return GeneratedQuery(
                sql="""SELECT c.region AS region, SUM(o.total_amount) AS revenue
FROM orders o
JOIN customers c ON c.id = o.customer_id
WHERE o.status = 'completed'
GROUP BY c.region
ORDER BY revenue DESC""",
                explanation="Compares completed-order revenue across customer regions.",
                chart_type="bar", chart_x="region", chart_y="revenue",
            )
        if "status" in text or "order count" in text or "orders by" in text:
            return GeneratedQuery(
                sql="""SELECT status, COUNT(*) AS order_count
FROM orders
GROUP BY status
ORDER BY order_count DESC""",
                explanation="Counts orders in each current order status.",
                chart_type="pie", chart_x="status", chart_y="order_count",
            )
        if "customer" in text or "client" in text:
            return GeneratedQuery(
                sql="""SELECT c.name AS customer, SUM(o.total_amount) AS revenue
FROM orders o
JOIN customers c ON c.id = o.customer_id
WHERE o.status = 'completed'
GROUP BY c.id, c.name
ORDER BY revenue DESC
LIMIT 10""",
                explanation="Ranks customers by completed-order revenue.",
                chart_type="bar", chart_x="customer", chart_y="revenue",
            )
        if "revenue" in text or "sales" in text:
            return GeneratedQuery(
                sql="""SELECT SUM(total_amount) AS revenue, COUNT(*) AS completed_orders
FROM orders
WHERE status = 'completed'""",
                explanation="Calculates total revenue and completed-order count.",
                chart_type="table", chart_x=None, chart_y=None,
            )
        return GeneratedQuery(
            sql="SELECT status, COUNT(*) AS order_count FROM orders GROUP BY status ORDER BY order_count DESC",
            explanation=(
                "I used order status counts as a safe default. Try asking about revenue, "
                "monthly trends, top products, top customers, or sales by region."
            ),
            chart_type="pie", chart_x="status", chart_y="order_count",
        )
