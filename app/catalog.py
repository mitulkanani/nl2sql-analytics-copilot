from dataclasses import dataclass


@dataclass(frozen=True)
class Column:
    name: str
    data_type: str
    description: str


@dataclass(frozen=True)
class Table:
    name: str
    description: str
    columns: tuple[Column, ...]


CATALOG: dict[str, Table] = {
    "customers": Table(
        name="customers",
        description="Synthetic customer accounts. One row per customer.",
        columns=(
            Column("id", "INTEGER", "Unique customer identifier."),
            Column("name", "TEXT", "Customer display name."),
            Column("email", "TEXT", "Synthetic email address."),
            Column("region", "TEXT", "Sales region: North, South, East, or West."),
            Column("created_at", "TEXT", "Account creation date in ISO format."),
        ),
    ),
    "products": Table(
        name="products",
        description="Product catalog. One row per product.",
        columns=(
            Column("id", "INTEGER", "Unique product identifier."),
            Column("name", "TEXT", "Product name."),
            Column("category", "TEXT", "Product category."),
            Column("unit_price", "REAL", "Current catalog price in USD."),
        ),
    ),
    "orders": Table(
        name="orders",
        description="Customer orders. One row per order.",
        columns=(
            Column("id", "INTEGER", "Unique order identifier."),
            Column("customer_id", "INTEGER", "References customers.id."),
            Column("order_date", "TEXT", "Order date in YYYY-MM-DD format."),
            Column("status", "TEXT", "Order status: pending, processing, completed, or cancelled."),
            Column("total_amount", "REAL", "Order total in USD."),
        ),
    ),
    "order_items": Table(
        name="order_items",
        description="Line items belonging to each order.",
        columns=(
            Column("id", "INTEGER", "Unique order line identifier."),
            Column("order_id", "INTEGER", "References orders.id."),
            Column("product_id", "INTEGER", "References products.id."),
            Column("quantity", "INTEGER", "Quantity purchased."),
            Column("unit_price", "REAL", "Unit price at the time of purchase."),
        ),
    ),
}

ALLOWED_TABLES = frozenset(CATALOG)
ALLOWED_COLUMNS = {
    table_name: frozenset(column.name for column in table.columns)
    for table_name, table in CATALOG.items()
}


def schema_for_prompt() -> str:
    lines: list[str] = []
    for table in CATALOG.values():
        lines.append(f"TABLE {table.name}: {table.description}")
        for column in table.columns:
            lines.append(f"  - {column.name} ({column.data_type}): {column.description}")
    lines.extend(
        [
            "RELATIONSHIPS:",
            "  orders.customer_id = customers.id",
            "  order_items.order_id = orders.id",
            "  order_items.product_id = products.id",
            "All monetary values are USD. Use orders.status = 'completed' for realized revenue.",
        ]
    )
    return "\n".join(lines)


def public_schema() -> list[dict[str, object]]:
    return [
        {
            "name": table.name,
            "description": table.description,
            "columns": [
                {"name": column.name, "type": column.data_type, "description": column.description}
                for column in table.columns
            ],
        }
        for table in CATALOG.values()
    ]
