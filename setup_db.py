"""Create a sample SQLite banking database with customers, accounts and transactions."""
import random
import sqlite3
from datetime import date, timedelta

DB_PATH = "bank.db"

CUSTOMERS = [
    (1, "Amit Ramgoolam", "Beau Bassin", "amit@example.com"),
    (2, "Priya Doorgakant", "Quatre Bornes", "priya@example.com"),
    (3, "Kevin Lee", "Curepipe", "kevin@example.com"),
    (4, "Nadia Hossen", "Port Louis", "nadia@example.com"),
]

ACCOUNTS = [
    (101, 1, "savings", 45200.0),
    (102, 1, "current", 18750.5),
    (103, 2, "current", 26900.0),
    (104, 3, "savings", 9100.75),
    (105, 4, "current", 310400.0),
]


def main():
    random.seed(42)
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.executescript(
        """
        DROP TABLE IF EXISTS transactions;
        DROP TABLE IF EXISTS accounts;
        DROP TABLE IF EXISTS customers;
        CREATE TABLE customers (
            customer_id INTEGER PRIMARY KEY,
            full_name TEXT,
            city TEXT,
            email TEXT
        );
        CREATE TABLE accounts (
            account_id INTEGER PRIMARY KEY,
            customer_id INTEGER REFERENCES customers(customer_id),
            account_type TEXT,
            balance REAL
        );
        CREATE TABLE transactions (
            txn_id INTEGER PRIMARY KEY,
            account_id INTEGER REFERENCES accounts(account_id),
            txn_date TEXT,
            description TEXT,
            amount REAL
        );
        """
    )
    cur.executemany("INSERT INTO customers VALUES (?, ?, ?, ?)", CUSTOMERS)
    cur.executemany("INSERT INTO accounts VALUES (?, ?, ?, ?)", ACCOUNTS)

    descriptions = ["Salary credit", "Grocery store", "Utility bill", "ATM withdrawal",
                    "Restaurant", "Online transfer", "Fuel", "Mobile top-up"]
    txn_id = 1
    today = date.today()
    for account_id, *_ in ACCOUNTS:
        for day in range(60):
            desc = random.choice(descriptions)
            amount = round(random.uniform(200, 5000), 2)
            if desc == "Salary credit":
                amount = abs(amount) * 2
            else:
                amount = -amount
            txn_date = (today - timedelta(days=day)).isoformat()
            cur.execute(
                "INSERT INTO transactions VALUES (?, ?, ?, ?, ?)",
                (txn_id, account_id, txn_date, desc, amount),
            )
            txn_id += 1

    conn.commit()
    conn.close()
    print(f"Created {DB_PATH} with {len(CUSTOMERS)} customers, {len(ACCOUNTS)} accounts, {txn_id - 1} transactions.")


if __name__ == "__main__":
    main()
