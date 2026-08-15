"""Titan Company - Week5 Day2: Growth x Margin Sensitivity"""
import sys, os, logging
import pandas as pd

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
log = logging.getLogger(__name__)

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DAY5_DIR = os.path.join(SCRIPT_DIR, "..", "week04_financial_model")
sys.path.append(DAY5_DIR)
import W4D5_dcf_valuation as w4d5

PROJECT_ROOT = os.path.join(SCRIPT_DIR, "..")
PIPELINE_CSV = os.path.join(PROJECT_ROOT, "data", "titan_pipeline_new.csv")
OUTPUT_CSV = os.path.join(PROJECT_ROOT, "data", "titan_sensitivity_growth_margin.csv")

# Ranges centered on Titan's own locked values (Base growth=25.9%, margin=10.14%)
GROWTH_RANGE = [15.9, 20.9, 25.9, 30.9, 35.9]
MARGIN_RANGE = [8.14, 9.14, 10.14, 11.14, 12.14]
HIST_MARGIN_MIN, HIST_MARGIN_MAX = 7.97, 12.03  # Titan's own verified range


def load_data():
    df = pd.read_csv(PIPELINE_CSV)
    return df.sort_values("year").reset_index(drop=True)


def build_sensitivity_grid(df, base_checks):
    results = []
    for growth in GROWTH_RANGE:
        row = {"revenue_growth": growth}
        for margin in MARGIN_RANGE:
            if margin < HIST_MARGIN_MIN or margin > HIST_MARGIN_MAX:
                log.warning(f"Margin={margin}% outside historical range - extrapolation.")

            scenario_checks = dict(base_checks)
            scenario_checks["revenue_base_C12"] = growth
            scenario_checks["margin_base_C17"] = margin
            wacc = base_checks["wacc_at_C9"]
            tg = base_checks["terminal_growth_C22"]

            forecast_df = w4d5.project_financials(df, scenario_checks, "base", tg)
            valuation = w4d5.discount_and_value(forecast_df, wacc, tg, df, scenario_checks)
            row[f"margin_{margin}"] = round(valuation["value_per_share"], 2)
        results.append(row)
        log.info(f"Growth={growth}%: {row}")
    return pd.DataFrame(results)


def main():
    df = load_data()
    base_checks = w4d5.preflight_cross_check()
    grid = build_sensitivity_grid(df, base_checks)
    grid.to_csv(OUTPUT_CSV, index=False)
    log.info(f"Saved to {OUTPUT_CSV}")


if __name__ == "__main__":
    main()