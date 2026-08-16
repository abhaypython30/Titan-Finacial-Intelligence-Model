"""
Titan Company - Week 6 Day 4: Standalone Synthesis

Pulls together every finding across Weeks 1-5 into one consolidated
narrative, entirely standalone (no Tata Motors reference, per project
decision). This is the "complete story" document - what forecast_log.md
records chronologically, this presents as one coherent analytical read.

Output: data/Titan_Synthesis_Report.md
"""

import os
import logging
import pandas as pd

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
log = logging.getLogger(__name__)

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.join(SCRIPT_DIR, "..")
DATA_DIR = os.path.join(PROJECT_ROOT, "data")
OUTPUT_MD = os.path.join(DATA_DIR, "Titan_Synthesis_Report.md")


def safe_read(filename):
    path = os.path.join(DATA_DIR, filename)
    if not os.path.exists(path):
        log.warning(f"{filename} not found - skipping that section.")
        return None
    return pd.read_csv(path)


def main():
    sections = []
    sections.append("# Titan Company Ltd - Financial Intelligence Synthesis\n")
    sections.append("Standalone analytical summary, FY17-26 historical window.\n")

    # --- Data Integrity Findings ---
    sections.append("## 1. Data Integrity Findings\n")
    sections.append(
        "- `total_debt` confirmed to be Total Liabilities (balance sheet identity "
        "match against `total_assets`), not real debt. Corrected to use `debt` "
        "(verified against actual Borrowings).\n"
        "- Net Profit initially didn't reconcile against HistoricalFS - resolved "
        "via Non-Controlling Interest (NCI) explanation, tied to CaratLane's "
        "minority stake structure.\n"
        "- EBT confirmed to include Other Income at source, matching "
        "HistoricalFS's own \"EBT + Other Inc\" definition exactly.\n"
        "- Face value confirmed as Rs.1 (not an assumed Rs.2).\n"
    )

    # --- COVID Impact ---
    sections.append("## 2. COVID Impact - Growth, Not Margin\n")
    sections.append(
        "Sales growth fell sharply during COVID (22.13% Pre-COVID -> 4.62% COVID), "
        "while EBITDA margin barely moved (9.69% -> 9.83%). Recovery overshot "
        "Pre-COVID growth levels (32.61%). Interpretation: Titan's more variable "
        "cost structure (retail rent, staff scaling with footfall) absorbed the "
        "demand shock without materially compressing margin on the sales that "
        "did occur.\n"
    )

    # --- WACC ---
    assumptions = safe_read("titan_assumptions_derived.csv")
    if assumptions is not None:
        row = assumptions.iloc[0]
        sections.append("## 3. WACC - A Verified, Unusually Low Figure\n")
        sections.append(
            f"WACC = {row['wacc']:.2f}% (Ke={row['ke']:.2f}%, Kd after-tax="
            f"{row['kd_after_tax']:.2f}%, Beta={row['beta']}). The implied Kd "
            f"({row['kd_implied']:.2f}%) sits below the risk-free rate, initially "
            f"flagged as suspicious - CONFIRMED via an external source (Titan "
            f"management referenced Gold Metal Loan financing cost at \"~3%\" "
            f"on an analyst call). Not a data error; reflects Titan's genuine "
            f"gold-sourcing financing structure.\n"
        )

    # --- Margin Driver ---
    margin_drivers = safe_read("titan_margin_drivers.csv")
    if margin_drivers is not None:
        row = margin_drivers.iloc[0]
        sections.append("## 4. Margin Structure - Narrow and Stable\n")
        sections.append(
            f"Locked margin range: Bear {row['final_bear']:.2f}% / Base "
            f"{row['final_base']:.2f}% / Bull {row['final_bull']:.2f}% - a "
            f"remarkably tight ~1.2pp band. Main correlated driver: "
            f"'{row['main_margin_driver']}' - not raw material/gold cost as "
            f"initially predicted, a reminder to report actual findings over "
            f"predictions.\n"
        )

    # --- Structural Profile ---
    capex_dep = safe_read("titan_capex_dep_terminal.csv")
    if capex_dep is not None:
        row = capex_dep.iloc[0]
        sections.append("## 5. Structural Profile - Asset-Light, Working-Capital-Intensive\n")
        sections.append(
            f"CAPEX% of sales: {row['capex_pct_sales']:.2f}%, Depreciation%: "
            f"{row['depreciation_pct_sales']:.2f}% - both far below a capital-"
            f"intensive manufacturer's typical range, consistent with leased-store "
            f"retail. NWC intensity separately verified at ~40% of sales, driven "
            f"by gold/jewellery inventory (inventory days ~178, per Week2). "
            f"Terminal growth locked at {row['terminal_growth_rate']:.2f}% - "
            f"capped tightly against WACC, given the thin buffer.\n"
        )

    # --- DCF Valuation ---
    dcf = safe_read("titan_dcf_valuation.csv")
    if dcf is not None:
        sections.append("## 6. DCF Valuation (Growth-Tapered)\n")
        for _, r in dcf.iterrows():
            sections.append(f"- {r['scenario'].upper()}: Rs.{r['value_per_share']:.2f}/share "
                             f"(EV Rs.{r['enterprise_value_cr']:.0f}cr)\n")
        sections.append(
            "\nNote: an initial flat-growth version produced implausible negative "
            "valuations across all scenarios due to unmoderated compounding against "
            "high NWC intensity - corrected via linear growth tapering toward "
            "terminal growth, a standard DCF refinement.\n"
        )

    # --- Sensitivity & Driver Ranking ---
    driver_ranking = safe_read("titan_driver_ranking.csv")
    if driver_ranking is not None:
        sections.append("## 7. Driver Ranking - WACC Dominates\n")
        for _, r in driver_ranking.sort_values("rank").iterrows():
            sections.append(f"- #{int(r['rank'])}: {r['driver']} - "
                             f"Rs.{r['absolute_swing_rs']:.2f} swing "
                             f"({r['swing_as_pct_of_base_value']:.1f}% of base)\n")
        sections.append(
            "\nWACC ranks #1, not margin or growth - driven by the thin buffer "
            "between WACC (4.58%) and terminal growth (2.58%), which amplifies "
            "the terminal value formula's sensitivity to small WACC moves. This "
            "is a structural fragility tied directly to Titan's Gold Metal Loan "
            "financing, not a coincidence.\n"
        )

    # --- Monte Carlo ---
    mc = safe_read("titan_montecarlo_summary.csv")
    if mc is not None:
        row = mc.iloc[0]
        sections.append("## 8. Monte Carlo Simulation\n")
        sections.append(
            f"Median: Rs.{row['median']:.2f}, Range: Rs.{row['min']:.2f} to "
            f"Rs.{row['max']:.2f}, {row['probability_negative_equity_pct']:.1f}% "
            f"probability of negative equity value. Methodology used per-year "
            f"independent sampling with tapering toward terminal growth, refined "
            f"through two rounds of correction after an external methodology "
            f"review identified real issues with the initial single-pair "
            f"approach.\n"
        )

    # --- Implied Multiples ---
    multiples = safe_read("titan_implied_multiples.csv")
    if multiples is not None:
        sections.append("## 9. Implied Multiples vs Market\n")
        for _, r in multiples.iterrows():
            sections.append(f"- {r['scenario'].upper()}: {r['implied_ev_ebitda']:.2f}x EV/EBITDA\n")
        sections.append(
            "\nCompared against Titan's own current market multiple (~49.80x) and "
            "the Retail-Cyclical sector median (~8.71x). DCF-implied multiples sit "
            "between these two benchmarks - consistent with the market pricing "
            "Titan as a premium quality/growth compounder relative to its sector, "
            "while this DCF captures a somewhat more conservative view given the "
            "growth-tapering assumption.\n"
        )

    with open(OUTPUT_MD, "w", encoding="utf-8") as f:
        f.writelines(sections)

    log.info(f"Synthesis report saved to {OUTPUT_MD}")
    log.info("This is a standalone Titan narrative ")


if __name__ == "__main__":
    main()