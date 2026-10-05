import sqlite3
from pathlib import Path
from datetime import datetime


BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = BASE_DIR / "CortexOps.db"


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db():

    conn = get_connection()

    conn.executescript("""
    CREATE TABLE IF NOT EXISTS customers (
        id INTEGER PRIMARY KEY,
        name TEXT NOT NULL,
        age INTEGER NOT NULL,
        income REAL NOT NULL,
        credit_score INTEGER NOT NULL,
        employment_type TEXT NOT NULL
    );

    CREATE TABLE IF NOT EXISTS applications (
        id INTEGER PRIMARY KEY,
        customer_id INTEGER NOT NULL,
        product TEXT NOT NULL,
        requested_amount REAL NOT NULL,
        tenure_months INTEGER NOT NULL,
        status TEXT DEFAULT 'UNDER_REVIEW',
        created_at TEXT DEFAULT CURRENT_TIMESTAMP,

        FOREIGN KEY(customer_id)
            REFERENCES customers(id)
    );

    CREATE TABLE IF NOT EXISTS documents (
        id INTEGER PRIMARY KEY,
        application_id INTEGER NOT NULL,
        document_type TEXT NOT NULL,
        status TEXT NOT NULL,

        FOREIGN KEY(application_id)
            REFERENCES applications(id)
    );

    CREATE TABLE IF NOT EXISTS policies (
        id INTEGER PRIMARY KEY,
        policy_name TEXT NOT NULL,
        rule_type TEXT NOT NULL,
        threshold REAL,
        description TEXT NOT NULL
    );

    CREATE TABLE IF NOT EXISTS agent_tasks (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        application_id INTEGER NOT NULL,
        agent_name TEXT NOT NULL,
        task TEXT NOT NULL,
        status TEXT DEFAULT 'PENDING',
        result TEXT,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP,

        FOREIGN KEY(application_id)
            REFERENCES applications(id)
    );

    CREATE TABLE IF NOT EXISTS audit_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        application_id INTEGER NOT NULL,
        event TEXT NOT NULL,
        details TEXT,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP,

        FOREIGN KEY(application_id)
            REFERENCES applications(id)
    );
    """)

    seed_database(conn)

    conn.commit()
    conn.close()


def seed_database(conn):

    customer_count = conn.execute(
        "SELECT COUNT(*) FROM customers"
    ).fetchone()[0]

    if customer_count > 0:
        return

    # ---------------------------------------------------------
    # CUSTOMERS
    # ---------------------------------------------------------

    customers = [
        (1, "Aarav Sharma", 29, 850000, 782, "SALARIED"),
        (2, "Riya Mehta", 34, 620000, 691, "SALARIED"),
        (3, "Kabir Singh", 41, 1200000, 812, "BUSINESS"),
        (4, "Ananya Patel", 27, 480000, 648, "SALARIED"),
        (5, "Vihaan Gupta", 38, 950000, 735, "BUSINESS"),
        (6, "Ishita Rao", 31, 720000, 675, "SALARIED"),
        (7, "Arjun Malhotra", 45, 1500000, 820, "BUSINESS"),
        (8, "Meera Kapoor", 26, 420000, 632, "SALARIED"),
        (9, "Aditya Verma", 36, 880000, 705, "SALARIED"),
        (10, "Sara Khan", 40, 1100000, 760, "BUSINESS"),
    ]

    conn.executemany("""
        INSERT INTO customers
        (id, name, age, income, credit_score, employment_type)
        VALUES (?, ?, ?, ?, ?, ?)
    """, customers)

    # ---------------------------------------------------------
    # APPLICATIONS
    # ---------------------------------------------------------

    applications = [
        (101, 1, "PERSONAL_LOAN", 500000, 36),
        (102, 2, "PERSONAL_LOAN", 300000, 24),
        (103, 3, "BUSINESS_LOAN", 1500000, 60),
        (104, 4, "PERSONAL_LOAN", 700000, 48),
        (105, 5, "HOME_LOAN", 2500000, 120),
        (106, 6, "PERSONAL_LOAN", 600000, 36),
        (107, 7, "BUSINESS_LOAN", 3000000, 84),
        (108, 8, "PERSONAL_LOAN", 900000, 48),
        (109, 9, "HOME_LOAN", 1800000, 120),
        (110, 10, "BUSINESS_LOAN", 2000000, 60),
    ]

    conn.executemany("""
        INSERT INTO applications
        (id, customer_id, product, requested_amount, tenure_months)
        VALUES (?, ?, ?, ?, ?)
    """, applications)

    # ---------------------------------------------------------
    # DOCUMENTS
    # ---------------------------------------------------------

    documents = [

        # Application 101
        (1, 101, "PAN", "VERIFIED"),
        (2, 101, "SALARY_SLIP", "VERIFIED"),
        (3, 101, "BANK_STATEMENT", "VERIFIED"),

        # Application 102
        (4, 102, "PAN", "VERIFIED"),
        (5, 102, "SALARY_SLIP", "PENDING"),
        (6, 102, "BANK_STATEMENT", "VERIFIED"),

        # Application 103
        (7, 103, "PAN", "VERIFIED"),
        (8, 103, "GST_CERTIFICATE", "VERIFIED"),
        (9, 103, "BANK_STATEMENT", "VERIFIED"),

        # Application 104
        (10, 104, "PAN", "VERIFIED"),
        (11, 104, "SALARY_SLIP", "MISMATCH"),
        (12, 104, "BANK_STATEMENT", "VERIFIED"),

        # Application 105
        (13, 105, "PAN", "VERIFIED"),
        (14, 105, "INCOME_PROOF", "VERIFIED"),
        (15, 105, "BANK_STATEMENT", "VERIFIED"),

        # Application 106
        (16, 106, "PAN", "VERIFIED"),
        (17, 106, "SALARY_SLIP", "VERIFIED"),
        (18, 106, "BANK_STATEMENT", "VERIFIED"),

        # Application 107
        (19, 107, "PAN", "VERIFIED"),
        (20, 107, "GST_CERTIFICATE", "VERIFIED"),
        (21, 107, "BANK_STATEMENT", "MISMATCH"),

        # Application 108
        (22, 108, "PAN", "VERIFIED"),
        (23, 108, "SALARY_SLIP", "VERIFIED"),
        (24, 108, "BANK_STATEMENT", "VERIFIED"),

        # Application 109
        (25, 109, "PAN", "VERIFIED"),
        (26, 109, "INCOME_PROOF", "VERIFIED"),
        (27, 109, "BANK_STATEMENT", "VERIFIED"),

        # Application 110
        (28, 110, "PAN", "VERIFIED"),
        (29, 110, "GST_CERTIFICATE", "VERIFIED"),
        (30, 110, "BANK_STATEMENT", "VERIFIED"),
    ]

    conn.executemany("""
        INSERT INTO documents
        (id, application_id, document_type, status)
        VALUES (?, ?, ?, ?)
    """, documents)

    # ---------------------------------------------------------
    # CREDIT POLICIES
    # ---------------------------------------------------------

    policies = [
        (
            1,
            "Minimum Credit Score",
            "CREDIT_SCORE",
            650,
            "Applications below 650 require escalation."
        ),
        (
            2,
            "Preferred Credit Score",
            "CREDIT_SCORE",
            700,
            "Scores above 700 are considered lower risk."
        ),
        (
            3,
            "Loan To Income Threshold",
            "LOAN_INCOME",
            2.0,
            "Requested amount should normally remain below 2x annual income."
        ),
        (
            4,
            "Document Verification",
            "DOCUMENT_STATUS",
            None,
            "Pending or mismatched documents require review."
        )
    ]

    conn.executemany("""
        INSERT INTO policies
        (id, policy_name, rule_type, threshold, description)
        VALUES (?, ?, ?, ?, ?)
    """, policies)


# -------------------------------------------------------------
# APPLICATION QUERIES
# -------------------------------------------------------------

def get_applications():

    conn = get_connection()

    rows = conn.execute("""
        SELECT
            a.id,
            c.name,
            c.income,
            c.credit_score,
            c.employment_type,
            a.product,
            a.requested_amount,
            a.tenure_months,
            a.status,
            a.created_at

        FROM applications a

        JOIN customers c
            ON a.customer_id = c.id

        ORDER BY a.id
    """).fetchall()

    conn.close()

    return [dict(row) for row in rows]


def get_application(application_id):

    conn = get_connection()

    application = conn.execute("""
        SELECT
            a.id,
            c.name,
            c.age,
            c.income,
            c.credit_score,
            c.employment_type,

            a.product,
            a.requested_amount,
            a.tenure_months,
            a.status,
            a.created_at

        FROM applications a

        JOIN customers c
            ON a.customer_id = c.id

        WHERE a.id = ?
    """, (application_id,)).fetchone()

    if not application:
        conn.close()
        return None

    documents = conn.execute("""
        SELECT
            document_type,
            status

        FROM documents

        WHERE application_id = ?
    """, (application_id,)).fetchall()

    conn.close()

    result = dict(application)

    result["documents"] = [
        dict(document)
        for document in documents
    ]

    return result


def get_policies():

    conn = get_connection()

    rows = conn.execute("""
        SELECT *
        FROM policies
        ORDER BY id
    """).fetchall()

    conn.close()

    return [dict(row) for row in rows]


# -------------------------------------------------------------
# AUDIT
# -------------------------------------------------------------

def add_audit_log(application_id, event, details):

    conn = get_connection()

    conn.execute("""
        INSERT INTO audit_logs
        (application_id, event, details)
        VALUES (?, ?, ?)
    """, (
        application_id,
        event,
        details
    ))

    conn.commit()
    conn.close()


def add_agent_task(
    application_id,
    agent_name,
    task,
    status,
    result
):

    conn = get_connection()

    conn.execute("""
        INSERT INTO agent_tasks
        (application_id, agent_name, task, status, result)
        VALUES (?, ?, ?, ?, ?)
    """, (
        application_id,
        agent_name,
        task,
        status,
        result
    ))

    conn.commit()
    conn.close()