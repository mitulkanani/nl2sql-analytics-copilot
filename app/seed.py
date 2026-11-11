import sqlite3
from pathlib import Path


SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS customers (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    email TEXT NOT NULL,
    region TEXT NOT NULL,
    created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS products (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    category TEXT NOT NULL,
    unit_price REAL NOT NULL
);
CREATE TABLE IF NOT EXISTS orders (
    id INTEGER PRIMARY KEY,
    customer_id INTEGER NOT NULL REFERENCES customers(id),
    order_date TEXT NOT NULL,
    status TEXT NOT NULL,
    total_amount REAL NOT NULL
);
CREATE TABLE IF NOT EXISTS order_items (
    id INTEGER PRIMARY KEY,
    order_id INTEGER NOT NULL REFERENCES orders(id),
    product_id INTEGER NOT NULL REFERENCES products(id),
    quantity INTEGER NOT NULL,
    unit_price REAL NOT NULL
);
"""


def initialize_database(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(path) as connection:
        connection.executescript(SCHEMA_SQL)
        count = connection.execute("SELECT COUNT(*) FROM customers").fetchone()[0]
        if count:
            return
        customers = [
            (1, "Avery Chen", "avery@example.test", "West", "2024-01-12"),
            (2, "Jordan Patel", "jordan@example.test", "North", "2024-02-04"),
            (3, "Morgan Rivera", "morgan@example.test", "South", "2024-02-19"),
            (4, "Taylor Brooks", "taylor@example.test", "East", "2024-03-02"),
            (5, "Casey Kim", "casey@example.test", "West", "2024-03-21"),
            (6, "Riley Shah", "riley@example.test", "North", "2024-04-05"),
            (7, "Quinn Davis", "quinn@example.test", "South", "2024-04-17"),
            (8, "Skyler Morgan", "skyler@example.test", "East", "2024-05-09"),
        ]
        products = [
            (1, "Wireless Headphones", "Electronics", 129.0),
            (2, "Standing Desk", "Office", 449.0),
            (3, "USB-C Hub", "Electronics", 59.0),
            (4, "Ergonomic Chair", "Office", 329.0),
            (5, "Travel Backpack", "Accessories", 89.0),
            (6, "4K Monitor", "Electronics", 599.0),
        ]
        orders = [
            (1001, 1, "2024-01-15", "completed", 188.0),
            (1002, 2, "2024-01-23", "completed", 449.0),
            (1003, 3, "2024-02-02", "completed", 658.0),
            (1004, 4, "2024-02-12", "cancelled", 129.0),
            (1005, 5, "2024-02-25", "completed", 777.0),
            (1006, 6, "2024-03-04", "processing", 508.0),
            (1007, 7, "2024-03-18", "completed", 778.0),
            (1008, 8, "2024-03-29", "completed", 688.0),
            (1009, 1, "2024-04-03", "completed", 658.0),
            (1010, 2, "2024-04-19", "pending", 89.0),
            (1011, 3, "2024-05-01", "completed", 1046.0),
            (1012, 4, "2024-05-14", "completed", 778.0),
            (1013, 5, "2024-06-07", "completed", 658.0),
            (1014, 6, "2024-06-16", "cancelled", 449.0),
            (1015, 7, "2024-06-28", "completed", 777.0),
            (1016, 8, "2024-07-11", "completed", 688.0),
            (1017, 1, "2024-07-25", "processing", 129.0),
            (1018, 2, "2024-08-02", "completed", 1046.0),
            (1019, 3, "2024-08-18", "completed", 508.0),
            (1020, 4, "2024-09-03", "completed", 777.0),
        ]
        items = [
            (1, 1001, 3, 1, 59.0), (2, 1001, 5, 1, 89.0), (3, 1001, 1, 1, 129.0),
            (4, 1002, 2, 1, 449.0), (5, 1003, 6, 1, 599.0), (6, 1003, 3, 1, 59.0),
            (7, 1004, 1, 1, 129.0), (8, 1005, 4, 1, 329.0), (9, 1005, 2, 1, 449.0),
            (10, 1006, 5, 1, 89.0), (11, 1006, 4, 1, 329.0), (12, 1007, 2, 1, 449.0),
            (13, 1007, 4, 1, 329.0), (14, 1008, 6, 1, 599.0), (15, 1008, 3, 1, 59.0),
            (16, 1009, 6, 1, 599.0), (17, 1009, 3, 1, 59.0), (18, 1010, 5, 1, 89.0),
            (19, 1011, 2, 1, 449.0), (20, 1011, 6, 1, 599.0), (21, 1012, 2, 1, 449.0),
            (22, 1012, 4, 1, 329.0), (23, 1013, 6, 1, 599.0), (24, 1013, 3, 1, 59.0),
            (25, 1014, 2, 1, 449.0), (26, 1015, 4, 1, 329.0), (27, 1015, 2, 1, 449.0),
            (28, 1016, 6, 1, 599.0), (29, 1016, 3, 1, 59.0), (30, 1017, 1, 1, 129.0),
            (31, 1018, 2, 1, 449.0), (32, 1018, 6, 1, 599.0), (33, 1019, 4, 1, 329.0),
            (34, 1019, 5, 2, 89.0), (35, 1020, 2, 1, 449.0), (36, 1020, 4, 1, 329.0),
        ]
        connection.executemany("INSERT INTO customers VALUES (?, ?, ?, ?, ?)", customers)
        connection.executemany("INSERT INTO products VALUES (?, ?, ?, ?)", products)
        connection.executemany("INSERT INTO orders VALUES (?, ?, ?, ?, ?)", orders)
        connection.executemany("INSERT INTO order_items VALUES (?, ?, ?, ?, ?)", items)
        connection.commit()
