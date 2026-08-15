"""Titan Company - Week5 Day4: Driver Ranking (Elasticity Analysis)"""
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
OUTPUT_CSV = os.path.join(PROJECT_ROOT, "data", "titan_driver_ranking.csv")

PERTURBATION_PCT = 0.10
DRIVERS = {
    "wacc": "wacc_at_C9",
    "terminal_growth": "terminal_growth_C22",
    "revenue_growth": "revenue_base_C12",
    "ebitda_margin": "margin_base_C17",
}


def load_data():
    df = pd.read_csv(PIPELINE_CSV)
    return df.sort_values("year").reset_index(drop=True)


def run_single_valuation(df, checks):
    wacc, tg = checks["wacc_at_C9"], checks["terminal_growth_C22"]
    forecast_df = w4d5.project_financials(df, checks, "base", tg)
    valuation = w4d5.discount_and_value(forecast_df, wacc, tg, df, checks)
    return valuation["value_per_share"]


def rank_drivers(df, base_checks):
    base_value = run_single_valuation(df, base_checks)
    log.info(f"Base value/share (locked assumptions): Rs.{base_value:.2f}")

    results = []
    for driver_name, check_key in DRIVERS.items():
        base_input = base_checks[check_key]

        up_checks = dict(base_checks)
        up_checks[check_key] = base_input * (1 + PERTURBATION_PCT)
        down_checks = dict(base_checks)
        down_checks[check_key] = base_input * (1 - PERTURBATION_PCT)

        # Safety check: if perturbing terminal growth up gets too close to
        # WACC, cap it - same defensive pattern as Week4 Day4.
        if check_key == "terminal_growth_C22" and up_checks[check_key] >= up_checks["wacc_at_C9"] - 1.0:
            log.warning(f"Terminal growth +10% ({up_checks[check_key]:.2f}%) too "
                        f"close to WACC - capping perturbation.")
            up_checks[check_key] = up_checks["wacc_at_C9"] - 1.0

        value_up = run_single_valuation(df, up_checks)
        value_down = run_single_valuation(df, down_checks)
        swing = abs(value_up - value_down)
        pct_swing = swing / base_value * 100

        results.append({
            "driver": driver_name, "base_input": round(base_input, 2),
            "value_at_minus10pct": round(value_down, 2), "value_at_base": round(base_value, 2),
            "value_at_plus10pct": round(value_up, 2), "absolute_swing_rs": round(swing, 2),
            "swing_as_pct_of_base_value": round(pct_swing, 1),
        })
        log.info(f"{driver_name}: -10% -> Rs.{value_down:.2f} | base -> Rs.{base_value:.2f} "
                  f"| +10% -> Rs.{value_up:.2f} | swing: Rs.{swing:.2f} ({pct_swing:.1f}%)")

    ranking = pd.DataFrame(results).sort_values("absolute_swing_rs", ascending=False).reset_index(drop=True)
    ranking["rank"] = ranking.index + 1

    log.info("Driver ranking (most impactful first):")
    for _, row in ranking.iterrows():
        log.info(f"  #{row['rank']}: {row['driver']} - Rs.{row['absolute_swing_rs']:.2f} "
                  f"({row['swing_as_pct_of_base_value']:.1f}% of base)")
    return ranking


def main():
    df = load_data()
    base_checks = w4d5.preflight_cross_check()
    ranking = rank_drivers(df, base_checks)
    ranking.to_csv(OUTPUT_CSV, index=False)
    log.info(f"Saved to {OUTPUT_CSV}")


if __name__ == "__main__":
    main()