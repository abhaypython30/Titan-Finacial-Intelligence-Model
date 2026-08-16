"""
Titan Company - Week 6 Day 1: Implied Multiples Cross-Check

Benchmarks (sourced, dated):
  - Titan's OWN current market EV/EBITDA: 49.80x (GuruFocus, May 2026)
  - Retail-Cyclical sector MEDIAN EV/EBITDA: 8.71x (same source) -
    Titan trades worse than 92.8% of 930 sector peers, i.e. at a huge
    premium - the market prices Titan as a quality/growth compounder,
    not a typical sector peer.
"""

import os
import logging
import pandas as pd

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
log = logging.getLogger(__name__)

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.join(SCRIPT_DIR, "..")
DATA_DIR = os.path.join(PROJECT_ROOT, "data")

PIPELINE_CSV = os.path.join(DATA_DIR, "titan_pipeline_new.csv")
DCF_CSV = os.path.join(DATA_DIR, "titan_dcf_valuation.csv")
OUTPUT_CSV = os.path.join(DATA_DIR, "titan_implied_multiples.csv")

MARKET_EV_EBITDA_CURRENT = 49.80   # Titan's own current market multiple
SECTOR_MEDIAN_EV_EBITDA = 8.71     # Retail-Cyclical sector median
DEVIATION_FLAG_THRESHOLD = 2.0


def load_data():
    hist = pd.read_csv(PIPELINE_CSV)
    hist = hist.sort_values("year").reset_index(drop=True)
    dcf = pd.read_csv(DCF_CSV)
    return hist, dcf


def compute_implied_multiples(hist, dcf):
    fy26_ebitda = hist["ebitda"].iloc[-1]
    log.info(f"FY26 historical EBITDA: Rs.{fy26_ebitda:,.2f}cr")

    results = []
    for _, row in dcf.iterrows():
        scenario = row["scenario"]
        ev = row["enterprise_value_cr"]
        implied_multiple = ev / fy26_ebitda
        results.append({"scenario": scenario, "enterprise_value_cr": ev,
                         "fy26_ebitda_cr": fy26_ebitda,
                         "implied_ev_ebitda": round(implied_multiple, 2)})
        log.info(f"[{scenario.upper()}] Implied EV/EBITDA: {implied_multiple:.2f}x")

    return pd.DataFrame(results)


def cross_check_against_market(multiples_df):
    log.info(f"Market benchmark (Titan's OWN current multiple): {MARKET_EV_EBITDA_CURRENT}x")
    log.info(f"Sector benchmark (Retail-Cyclical median): {SECTOR_MEDIAN_EV_EBITDA}x")

    for _, row in multiples_df.iterrows():
        implied = row["implied_ev_ebitda"]
        vs_own_market = implied / MARKET_EV_EBITDA_CURRENT
        vs_sector = implied / SECTOR_MEDIAN_EV_EBITDA

        log.info(f"{row['scenario'].upper()}: {implied:.2f}x is {vs_own_market:.2f}x Titan's "
                  f"own current market multiple, and {vs_sector:.2f}x the sector median.")

        if implied < MARKET_EV_EBITDA_CURRENT:
            log.info(f"  -> DCF suggests {row['scenario']} case is BELOW current market "
                      f"pricing - i.e. the market may be pricing in more optimism than "
                      f"this DCF captures, even in the Bull case if this holds there too.")

    log.warning("NOTE: Titan trades at a large premium to its own sector (49.80x vs "
                "8.71x median) - the market treats Titan as a quality/growth compounder, "
                "not a typical sector peer. A DCF-implied multiple sitting between the "
                "sector median and Titan's own market multiple is a reasonable, "
                "explainable outcome, not a red flag by itself.")


def main():
    hist, dcf = load_data()
    multiples_df = compute_implied_multiples(hist, dcf)
    cross_check_against_market(multiples_df)
    multiples_df.to_csv(OUTPUT_CSV, index=False)
    log.info(f"Saved to {OUTPUT_CSV}")


if __name__ == "__main__":
    main()