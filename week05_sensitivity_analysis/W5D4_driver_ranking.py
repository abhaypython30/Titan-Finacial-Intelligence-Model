"""
Titan Company - Week5 Day4: Driver Ranking (REVISED methodology)

"""

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

PERTURBATION_PP = 1.00  # standardized absolute percentage-point move, ALL drivers

DRIVERS = {
    "wacc": "wacc_at_C9",
    "terminal_growth": "terminal_growth_C22",
    "revenue_growth": "revenue_base_C12",
    "ebitda_margin": "margin_base_C17",
}

# Human-readable labels - fixes the raw-key-name display issue flagged in review
DRIVER_DISPLAY_NAMES = {
    "wacc": "WACC",
    "terminal_growth": "Terminal Growth",
    "revenue_growth": "Revenue Growth",
    "ebitda_margin": "EBITDA Margin",
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
        up_checks[check_key] = base_input + PERTURBATION_PP
        down_checks = dict(base_checks)
        down_checks[check_key] = base_input - PERTURBATION_PP

        # Safety check: if perturbing terminal growth up gets too close to
        # WACC, cap it - same defensive pattern as Week4 Day4.
        if check_key == "terminal_growth_C22" and up_checks[check_key] >= up_checks["wacc_at_C9"] - 1.0:
            log.warning(f"Terminal growth +{PERTURBATION_PP}pp ({up_checks[check_key]:.2f}%) "
                        f"too close to WACC - capping perturbation.")
            up_checks[check_key] = up_checks["wacc_at_C9"] - 1.0

        value_up = run_single_valuation(df, up_checks)
        value_down = run_single_valuation(df, down_checks)
        swing = abs(value_up - value_down)
        pct_swing = swing / base_value * 100

        # Direction computed DATA-DRIVENLY, not assumed - checks which
        # way the value actually moved, doesn't presume the sign.
        direction = "increases_value" if value_up > value_down else "decreases_value"

        results.append({
            "driver": driver_name,
            "driver_display": DRIVER_DISPLAY_NAMES[driver_name],
            "base_input": round(base_input, 2),
            "perturbation_pp": PERTURBATION_PP,
            "value_at_minus_1pp": round(value_down, 2),
            "value_at_base": round(base_value, 2),
            "value_at_plus_1pp": round(value_up, 2),
            "absolute_swing_rs": round(swing, 2),
            "swing_as_pct_of_base_value": round(pct_swing, 1),
            "direction_as_driver_increases": direction,
        })
        log.info(f"{DRIVER_DISPLAY_NAMES[driver_name]}: -1pp -> Rs.{value_down:.2f} | "
                  f"base -> Rs.{base_value:.2f} | +1pp -> Rs.{value_up:.2f} | "
                  f"swing: Rs.{swing:.2f} ({pct_swing:.1f}%) | direction: {direction}")

    ranking = pd.DataFrame(results).sort_values("absolute_swing_rs", ascending=False).reset_index(drop=True)
    ranking["rank"] = ranking.index + 1

    log.info("Driver ranking (most impactful first, standardized +/-1.00 percentage point basis):")
    for _, row in ranking.iterrows():
        arrow = "^ raises value" if row["direction_as_driver_increases"] == "increases_value" else "v lowers value"
        log.info(f"  #{row['rank']}: {row['driver_display']} - Rs.{row['absolute_swing_rs']:.2f} "
                  f"swing, increasing this driver {arrow}")
    return ranking


def main():
    df = load_data()
    base_checks = w4d5.preflight_cross_check()
    ranking = rank_drivers(df, base_checks)
    ranking.to_csv(OUTPUT_CSV, index=False)
    log.info(f"Saved to {OUTPUT_CSV}")


if __name__ == "__main__":
    main()