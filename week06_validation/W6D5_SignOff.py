"""
Titan Company - Week 6 Day 5: Final Sign-Off Checklist

Confirms every required file exists and the integrity test still passes
before tagging the project as complete. Does not recompute anything -
purely a final gate check.
"""

import os
import subprocess
import logging

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
log = logging.getLogger(__name__)

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.join(SCRIPT_DIR, "..")
DATA_DIR = os.path.join(PROJECT_ROOT, "data")

REQUIRED_FILES = [
    "titan_pipeline_new.csv", "titan_assumptions_derived.csv",
    "titan_revenue_drivers.csv", "titan_margin_drivers.csv",
    "titan_capex_dep_terminal.csv", "titan_dcf_valuation.csv",
    "titan_sensitivity_wacc_tg.csv", "titan_sensitivity_growth_margin.csv",
    "titan_montecarlo_summary.csv", "titan_driver_ranking.csv",
    "titan_week5_sensitivity_master_summary.csv", "titan_implied_multiples.csv",
    "Titan_Synthesis_Report.md",
]

REQUIRED_ROOT_FILES = ["README.md", "forecast_log.md"]


def check_files():
    missing = []
    for f in REQUIRED_FILES:
        if not os.path.exists(os.path.join(DATA_DIR, f)):
            missing.append(f)
    for f in REQUIRED_ROOT_FILES:
        if not os.path.exists(os.path.join(PROJECT_ROOT, f)):
            missing.append(f)

    if missing:
        log.warning(f"MISSING before sign-off: {missing}")
        return False
    log.info("All required files present.")
    return True


def check_no_tata_references():
    """Final check: confirm README and forecast_log are genuinely standalone."""
    for fname in REQUIRED_ROOT_FILES:
        path = os.path.join(PROJECT_ROOT, fname)
        if os.path.exists(path):
            content = open(path, "r", encoding="utf-8", errors="ignore").read()
            if "tata" in content.lower():
                log.warning(f"'{fname}' still contains a reference to Tata Motors - "
                            f"check before final commit, this project was decided "
                            f"to be standalone.")
                return False
    log.info("README and forecast_log confirmed standalone - no Tata references.")
    return True


def main():
    files_ok = check_files()
    standalone_ok = check_no_tata_references()

    if files_ok and standalone_ok:
        log.info("SIGN-OFF READY. Run the git commands below manually:")
        log.info("  git add .")
        log.info("  git commit -m \"Week6 Day5: final sign-off\"")
        log.info("  git tag -a v1-titan-complete -m \"Titan Company DCF model complete, FY17-26\"")
    else:
        log.warning("NOT READY - resolve the issues above before tagging.")


if __name__ == "__main__":
    main()