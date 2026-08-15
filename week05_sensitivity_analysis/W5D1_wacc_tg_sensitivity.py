"""
Titan Company - Week 5 Day 1: WACC x Terminal Growth Sensitivity

"""
import sys, os, logging
import numpy as np
import pandas as pd

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
log = logging.getLogger(__name__)

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DAY5_DIR = os.path.join(SCRIPT_DIR, "..", "week04_financial_model")
sys.path.append(DAY5_DIR)
import W4D5_dcf_valuation as w4d5

PROJECT_ROOT = os.path.join(SCRIPT_DIR, "..")
PIPELINE_CSV = os.path.join(PROJECT_ROOT, "data", "titan_pipeline_new.csv")
OUTPUT_CSV = os.path.join(PROJECT_ROOT, "data", "titan_sensitivity_wacc_tg.csv")

# Ranges centered on TITAN's own values, not Tata's
WACC_RANGE = [3.58, 4.08, 4.58, 5.08, 5.58]
TG_RANGE = [0.58, 1.58, 2.58, 3.58, 4.58]
MIN_BUFFER_BELOW_WACC = 1.0


def load_data():
    df = pd.read_csv(PIPELINE_CSV)
    df = df.sort_values("year").reset_index(drop=True)
    return df


def build_sensitivity_grid(df, base_checks):
    results = []
    for wacc in WACC_RANGE:
        row = {"wacc": wacc}
        for tg in TG_RANGE:
            if tg >= wacc - MIN_BUFFER_BELOW_WACC:
                log.warning(f"WACC={wacc}%, TG={tg}% - invalid, marked N/A")
                row[f"tg_{tg}"] = None
                continue
            scenario_checks = dict(base_checks)
            scenario_checks["wacc_at_C9"] = wacc
            scenario_checks["terminal_growth_C22"] = tg
            forecast_df = w4d5.project_financials(df, scenario_checks, "base", tg)
            valuation = w4d5.discount_and_value(forecast_df, wacc, tg, df, scenario_checks)
            row[f"tg_{tg}"] = round(valuation["value_per_share"], 2)
        results.append(row)
        log.info(f"WACC={wacc}%: {row}")
    return pd.DataFrame(results)


def main():
    df = load_data()
    base_checks = w4d5.preflight_cross_check()
    grid = build_sensitivity_grid(df, base_checks)
    grid.to_csv(OUTPUT_CSV, index=False)
    log.info(f"Saved to {OUTPUT_CSV}")

    numeric_vals = [v for v in grid.drop(columns=["wacc"]).values.flatten() if pd.notna(v)]
    log.info(f"Value/share range: Rs.{min(numeric_vals):.2f} to Rs.{max(numeric_vals):.2f} "
              f"({max(numeric_vals)/min(numeric_vals):.1f}x spread)")


if __name__ == "__main__":
    main()