"""
Titan Company - Week5 Day3: Monte Carlo (per-year paired bootstrap)

REVISED per methodology review:
1. FIXED: was sampling ONE (growth, margin) pair per simulation and
   applying it across all 5 forecast years. This meant only 8 distinct
   outcomes were possible regardless of how many simulations ran. Now
   samples a NEW pair for EACH forecast year independently.

   HONEST TRADEOFF, not a strictly-better fix: this assumes zero
   year-to-year correlation in growth/margin, which is not realistic -
   real business performance has momentum (a strong year tends to be
   followed by another reasonably strong one, not a random unrelated
   draw). This version likely OVERSTATES 5-year cumulative volatility
   compared to reality. Neither approach is "more correct" in an
   absolute sense - this one answers "what if each year independently
   resembles some historical year" rather than "what if the next 5
   years resemble one particular historical regime."

2. FIXED: COVID exclusion window extended to [2020, 2021, 2022] for the
   bootstrap pool specifically. 2022's growth (33.06%) is calculated
   against a 2021 base that was still COVID-suppressed (2.81% growth) -
   this "recovery bounce" inflates 2022's growth figure artificially,
   the same base-effect distortion pattern. NOTE: Day2/Day3(margin)/Day4
   of Week4 still use COVID_YEARS=[2020,2021] - this is a DELIBERATE,
   FLAGGED inconsistency pending a decision on whether to extend the
   window project-wide. Do not assume this has been reconciled.
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
RESULTS_CSV = os.path.join(PROJECT_ROOT, "data", "titan_montecarlo_results.csv")
SUMMARY_CSV = os.path.join(PROJECT_ROOT, "data", "titan_montecarlo_summary.csv")

# EXTENDED per review point 2 - see module docstring for rationale.
# NOTE: differs from Week4 Day2/3/4's [2020,2021] - flagged, not reconciled.
COVID_YEARS_MONTE_CARLO = [2020, 2021, 2022]
N_SIMULATIONS = 5000
RANDOM_SEED = 42


def load_data():
    df = pd.read_csv(PIPELINE_CSV)
    return df.sort_values("year").reset_index(drop=True)


def get_paired_history(df):
    df["growth_pct"] = df["sales"].pct_change() * 100
    df["margin_pct"] = (df["ebitda"] / df["sales"]) * 100
    non_covid = df[~df["year"].isin(COVID_YEARS_MONTE_CARLO)]
    paired = non_covid[["year", "growth_pct", "margin_pct"]].dropna().reset_index(drop=True)
    log.info(f"Bootstrap pool - {len(paired)} paired (year, growth, margin) rows "
              f"(COVID+recovery-bounce years {COVID_YEARS_MONTE_CARLO} excluded):")
    for _, r in paired.iterrows():
        log.info(f"  {int(r['year'])}: growth={r['growth_pct']:.2f}%, margin={r['margin_pct']:.2f}%")
    if len(paired) < 5:
        log.warning(f"Bootstrap pool is small ({len(paired)} years) - even with "
                    f"per-year sampling, results draw from a limited real-world "
                    f"vocabulary. Treat tails with caution.")
    return paired


def project_financials_montecarlo(df, checks, sampled_rows, terminal_growth):
    """
    Per-year independent sampling, COMBINED with tapering toward terminal
    growth - this is the corrected version.

    A prior version applied each year's sampled growth rate RAW, with no
    moderation. Since every year in the bootstrap pool has growth between
    18-45% (none low), compounding 5 unmoderated years of that magnitude
    against a ~40% NWC ratio guaranteed negative FCFF in literally every
    simulation - a 100% negative-equity result that reflected the
    modeling choice, not a genuine probabilistic finding. Fixed by
    tapering each year's SAMPLED rate toward terminal growth using the
    same linear weighting as the deterministic scenarios (Week4 Day5) -
    preserves year-to-year sampling diversity while preventing runaway
    unmoderated compounding.
    """
    dep_pct = checks["depreciation_pct_C23"] / 100
    capex_pct = checks["capex_pct_C24"] / 100
    tax_rate = checks["effective_tax_C25"] / 100
    tg_dec = terminal_growth / 100

    last_sales = df["sales"].iloc[-1]
    payables = w4d5.get_column_with_fallback(df, "payables", "other_liabilities", "nwc")
    last_nwc = (df["debtors"] + df["inventory"] + df["cash_operating"] - payables).iloc[-1]
    nwc_pct_sales = last_nwc / last_sales

    rows = []
    prev_sales, prev_nwc = last_sales, last_nwc
    n_years = len(w4d5.FORECAST_YEARS)

    for i, year in enumerate(w4d5.FORECAST_YEARS):
        raw_sampled_growth = sampled_rows[i]["growth_pct"] / 100
        margin = sampled_rows[i]["margin_pct"] / 100

        # TAPER: blend this year's sampled rate toward terminal growth,
        # same linear weighting as the deterministic case.
        step = i / (n_years - 1) if n_years > 1 else 0
        growth = raw_sampled_growth - (raw_sampled_growth - tg_dec) * step

        sales = prev_sales * (1 + growth)
        ebitda = sales * margin
        depreciation = sales * dep_pct
        ebit = ebitda - depreciation
        tax = max(ebit, 0) * tax_rate
        nopat = ebit - tax
        capex = sales * capex_pct
        nwc = sales * nwc_pct_sales
        d_nwc = nwc - prev_nwc
        fcff = nopat + depreciation - capex - d_nwc

        rows.append({"year": year, "sampled_from_year": sampled_rows[i]["year"],
                     "raw_sampled_growth": raw_sampled_growth * 100,
                     "applied_growth_after_taper": growth * 100,
                     "applied_margin": margin * 100, "sales": sales, "fcff": fcff})
        prev_sales, prev_nwc = sales, nwc

    return pd.DataFrame(rows)


def run_simulation(df, base_checks, paired_history):
    rng = np.random.default_rng(RANDOM_SEED)
    wacc, tg = base_checks["wacc_at_C9"], base_checks["terminal_growth_C22"]
    n_years = len(w4d5.FORECAST_YEARS)

    results = []
    for i in range(N_SIMULATIONS):
        # NEW: sample a DIFFERENT pair for EACH forecast year, not one
        # pair for the whole simulation.
        sampled_rows = [
            paired_history.sample(n=1, random_state=rng.integers(0, 1_000_000)).iloc[0]
            for _ in range(n_years)
        ]

        forecast_df = project_financials_montecarlo(df, base_checks, sampled_rows, tg)
        valuation = w4d5.discount_and_value(forecast_df, wacc, tg, df, base_checks)

        results.append({
            "sim": i,
            "sampled_years": [int(r["year"]) for r in sampled_rows],
            "value_per_share": round(valuation["value_per_share"], 2),
        })
        if (i + 1) % 1000 == 0:
            log.info(f"Completed {i+1}/{N_SIMULATIONS}")

    return pd.DataFrame(results)


def summarize(results_df):
    values = results_df["value_per_share"].values
    negative_count = (values < 0).sum()
    summary = {
        "n_simulations": N_SIMULATIONS, "mean": np.mean(values), "median": np.median(values),
        "std": np.std(values), "p5": np.percentile(values, 5), "p25": np.percentile(values, 25),
        "p50": np.percentile(values, 50), "p75": np.percentile(values, 75),
        "p95": np.percentile(values, 95), "min": np.min(values), "max": np.max(values),
        "probability_negative_equity_pct": negative_count / len(values) * 100,
    }
    log.info("Monte Carlo summary (per-year independent sampling):")
    for k, v in summary.items():
        log.info(f"  {k}: {v:.2f}" if isinstance(v, float) else f"  {k}: {v}")
    if negative_count > 0:
        log.warning(f"{negative_count}/{N_SIMULATIONS} simulations produced negative "
                    f"equity value.")
    return pd.DataFrame([summary])


def main():
    df = load_data()
    base_checks = w4d5.preflight_cross_check()
    paired = get_paired_history(df)

    results_df = run_simulation(df, base_checks, paired)
    results_df.to_csv(RESULTS_CSV, index=False)

    summary_df = summarize(results_df)
    summary_df.to_csv(SUMMARY_CSV, index=False)
    log.info(f"Saved to {SUMMARY_CSV}")


if __name__ == "__main__":
    main()