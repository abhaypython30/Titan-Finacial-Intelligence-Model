"""
Titan Company - Week 3, Day 5: Load Into Shared 4-Table Schema (Multi-Company)

"""



import pandas as pd
from sqlalchemy import create_engine, text
from sqlalchemy.engine import URL
import os
import logging
from dotenv import load_dotenv

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')
logger = logging.getLogger(__name__)

load_dotenv()
password = os.getenv("DB_PASSWORD")

url = URL.create(
    drivername="mysql+pymysql",
    username="root",
    password=password,
    host="localhost",
    database="financial_analytics_db",  # RENAMED from tata_db - neutral name
                                          # since this now hosts multiple
                                          # companies across sectors, not
                                          # just Tata Motors
)
engine = create_engine(url)

TICKER = "TITAN.NS"
COMPANY_NAME = "Titan Company Ltd"
SECTOR = "Jewellery & Watches"  # NEW: supports sector-based peer grouping
PIPELINE_CSV = "data/titan_pipeline_new.csv"
EXCEL_PATH = "data/Titan project.xlsx"


def create_schema(engine):
    """
    Same 4-table schema, with ONE addition: 'sector' column on companies,
    needed to support same-sector peer comparison (Tata + auto peers,
    Titan + jewellery peers) rather than just a single Tata-vs-Titan
    comparison. CREATE TABLE IF NOT EXISTS is safe to run even if the
    table already exists without this column - see the ALTER TABLE
    fallback below for that case.
    """
    with engine.connect() as conn:
        
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS companies (
                company_id   INT PRIMARY KEY AUTO_INCREMENT,
                ticker       VARCHAR(20)  NOT NULL UNIQUE,
                company_name VARCHAR(100) NOT NULL,
                sector       VARCHAR(50)
            )
        """))
        # Fallback: if 'companies' already existed from before this sector
        # column was added, this adds it without erroring on re-run.
        try:
            conn.execute(text("ALTER TABLE companies ADD COLUMN sector VARCHAR(50)"))
            conn.commit()
        except Exception:
            pass  # column already exists - safe to ignore
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS income_statement (
                id                  INT PRIMARY KEY AUTO_INCREMENT,
                company_id          INT NOT NULL,
                fiscal_year         INT NOT NULL,
                sales               DECIMAL(15,2),
                raw_material_cost   DECIMAL(15,2),
                change_in_inventory DECIMAL(15,2),
                power_fuel          DECIMAL(15,2),
                employee_cost       DECIMAL(15,2),
                selling_admin       DECIMAL(15,2),
                other_expenses      DECIMAL(15,2),
                other_income        DECIMAL(15,2),
                cogs                DECIMAL(15,2),
                gross_profit        DECIMAL(15,2),
                ebitda              DECIMAL(15,2),
                ebit                DECIMAL(15,2),
                interest            DECIMAL(15,2),
                depreciation        DECIMAL(15,2),
                ebt                 DECIMAL(15,2),
                tax                 DECIMAL(15,2),
                net_profit          DECIMAL(15,2),
                gross_margin        DECIMAL(10,4),
                ebitda_margin       DECIMAL(10,4),
                ebit_margin         DECIMAL(10,4),
                ebt_margin          DECIMAL(10,4),
                net_margin          DECIMAL(10,4),
                sales_growth        DECIMAL(10,4),
                ebitda_growth       DECIMAL(10,4),
                ebit_growth         DECIMAL(10,4),
                net_profit_growth   DECIMAL(10,4),
                FOREIGN KEY (company_id) REFERENCES companies(company_id)
            )
        """))
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS balance_sheet (
                id               INT PRIMARY KEY AUTO_INCREMENT,
                company_id       INT NOT NULL,
                fiscal_year      INT NOT NULL,
                total_assets     DECIMAL(15,2),
                fixed_assets     DECIMAL(15,2),
                capital_employed DECIMAL(15,2),
                total_debt       DECIMAL(15,2),
                debt             DECIMAL(15,2),
                reserves         DECIMAL(15,2),
                equity_share_cap DECIMAL(15,2),
                dividend_amount  DECIMAL(15,2),
                debtors          DECIMAL(15,2),
                avg_debtors      DECIMAL(15,2),
                inventory        DECIMAL(15,2),
                payables         DECIMAL(15,2),
                cash_operating   DECIMAL(15,2),
                FOREIGN KEY (company_id) REFERENCES companies(company_id)
            )
        """))
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS ratios (
                id                        INT PRIMARY KEY AUTO_INCREMENT,
                company_id                INT NOT NULL,
                fiscal_year               INT NOT NULL,
                debtor_turnover           DECIMAL(10,2),
                inventory_turnover        DECIMAL(10,2),
                creditor_turnover         DECIMAL(10,2),
                fixed_asset_turnover      DECIMAL(10,2),
                capital_turnover          DECIMAL(10,2),
                debtor_days               DECIMAL(10,2),
                inventory_days            DECIMAL(10,2),
                payables_days             DECIMAL(10,2),
                cash_conversion_cycle     DECIMAL(10,2),
                roce                      DECIMAL(10,4),
                interest_coverage         DECIMAL(10,2),
                debt_to_ebitda            DECIMAL(10,2),
                roce_flag                 BOOLEAN,
                cash_conversion_cycle_flag BOOLEAN,
                FOREIGN KEY (company_id) REFERENCES companies(company_id)
            )
        """))
        conn.commit()
    logger.info("4-table schema verified/created successfully (shared across companies).")


def load_data(engine):
    """
    Loads titan_pipeline_new.csv into the shared 4-table schema.
    FIXED: uses DELETE-then-INSERT scoped to this company_id, making
    re-runs safe (unlike the original's broken duplicate-guard).
    """
    df = pd.read_csv(PIPELINE_CSV)

    with engine.connect() as conn:
        conn.execute(text("""
            INSERT IGNORE INTO companies (ticker, company_name)
            VALUES (:ticker, :name)
        """), {"ticker": TICKER, "name": COMPANY_NAME})
        conn.commit()
        result = conn.execute(text(
            "SELECT company_id FROM companies WHERE ticker = :ticker"
        ), {"ticker": TICKER})
        company_id = result.fetchone()[0]

        # FIX: delete this company's existing rows first, so re-running
        # after a data correction doesn't create duplicates or require
        # a manual truncate.
        for table in ["income_statement", "balance_sheet", "ratios"]:
            deleted = conn.execute(text(
                f"DELETE FROM {table} WHERE company_id = :cid"
            ), {"cid": company_id})
            if deleted.rowcount > 0:
                logger.info(f"Removed {deleted.rowcount} existing row(s) "
                            f"from {table} for company_id={company_id} "
                            f"before reload.")
        conn.commit()

    income_df = df[[
        'year', 'sales', 'raw_material_cost', 'change_in_inventory',
        'power_fuel', 'employee_cost', 'selling_admin',
        'other_expenses', 'other_income', 'cogs', 'gross_profit',
        'ebitda', 'ebit', 'interest', 'depreciation',
        'ebt', 'tax', 'net_profit',
        'gross_margin', 'ebitda_margin', 'ebit_margin',
        'ebt_margin', 'net_margin',
        'sales_growth', 'ebitda_growth', 'ebit_growth', 'net_profit_growth'
    ]].copy()
    income_df['company_id'] = company_id
    income_df.rename(columns={'year': 'fiscal_year'}, inplace=True)

    balance_df = df[[
        'year', 'total_assets', 'fixed_assets', 'capital_employed',
        'total_debt', 'debt', 'reserves', 'equity_share_cap',
        'dividend_amount', 'debtors', 'avg_debtors',
        'inventory', 'payables', 'cash_operating'
    ]].copy()
    balance_df['company_id'] = company_id
    balance_df.rename(columns={'year': 'fiscal_year'}, inplace=True)

    ratios_df = df[[
        'year', 'debtor_turnover', 'inventory_turnover',
        'creditor_turnover', 'fixed_asset_turnover', 'capital_turnover',
        'debtor_days', 'inventory_days', 'payables_days',
        'cash_conversion_cycle', 'roce', 'interest_coverage',
        'debt_to_ebitda', 'roce_flag', 'cash_conversion_cycle_flag'
    ]].copy()
    ratios_df['company_id'] = company_id
    ratios_df.rename(columns={'year': 'fiscal_year'}, inplace=True)

    income_df.to_sql('income_statement', engine, if_exists='append', index=False)
    balance_df.to_sql('balance_sheet', engine, if_exists='append', index=False)
    ratios_df.to_sql('ratios', engine, if_exists='append', index=False)

    logger.info(f"income_statement: {len(income_df)} rows loaded for {COMPANY_NAME}.")
    logger.info(f"balance_sheet: {len(balance_df)} rows loaded for {COMPANY_NAME}.")
    logger.info(f"ratios: {len(ratios_df)} rows loaded for {COMPANY_NAME}.")


def run_query(engine):
    """
    UNCHANGED from Tata Motors' version - no company filter existed in
    the original query, so this now returns BOTH Tata Motors AND Titan
    ranked together automatically. This is the multi-company peer
    comparison the schema was designed for, arriving in Week3 instead
    of Week8.
    """
    query = """
    WITH base AS (
        SELECT
            c.company_name,
            i.fiscal_year,
            i.ebitda_margin,
            b.debt,
            b.capital_employed,
            r.roce,
            r.cash_conversion_cycle
        FROM companies c
        JOIN income_statement i ON c.company_id = i.company_id
        JOIN balance_sheet b ON c.company_id = b.company_id AND i.fiscal_year = b.fiscal_year
        JOIN ratios r ON c.company_id = r.company_id AND i.fiscal_year = r.fiscal_year
    ),
    yoy AS (
        SELECT
            company_name, fiscal_year, ebitda_margin, debt,
            capital_employed, cash_conversion_cycle, roce,
            (roce - LAG(roce, 1) OVER (PARTITION BY company_name ORDER BY fiscal_year)) * 100
                AS roce_change_pct
        FROM base
    ),
    ranked AS (
        SELECT
            company_name, fiscal_year, ebitda_margin, debt,
            capital_employed, cash_conversion_cycle, roce, roce_change_pct,
            RANK() OVER (PARTITION BY company_name ORDER BY roce DESC) AS roce_rank,
            NTILE(4) OVER (PARTITION BY company_name ORDER BY roce DESC) AS roce_quartile
        FROM yoy
    )
    SELECT * FROM ranked ORDER BY company_name, fiscal_year
    """
    # FIXED: was selecting b.total_debt (confirmed mislabeled as Total
    # Liabilities in Week1) - now correctly uses b.debt (verified against
    # actual Borrowings for both companies).

    result_df = pd.read_sql(query, engine)
    logger.info(f"Query returned {len(result_df)} rows (both companies).")
    logger.info(f"\n{result_df.to_string()}")

    with pd.ExcelWriter(EXCEL_PATH, engine='openpyxl', mode='a', if_sheet_exists='replace') as writer:
        result_df.to_excel(writer, sheet_name='SQL Output', index=False)

    logger.info("Exported combined Tata+Titan ranking to SQL Output tab.")
    return result_df


if __name__ == "__main__":
    create_schema(engine)
    load_data(engine)
    run_query(engine)