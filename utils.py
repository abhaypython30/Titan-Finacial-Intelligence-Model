"""
Shared helper functions - reused as-is from the Tata Motors project.
Copy this file to the Titan project root (G:/Titan/utils.py) so W1D4's
import works without needing to point back at the Tata project folder.
"""

import logging

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
log = logging.getLogger(__name__)


def get_column_with_fallback(df, preferred_col, fallback_col, ratio_name):
    if preferred_col in df.columns:
        log.info(f"[{ratio_name}] Using '{preferred_col}' (preferred)")
        return df[preferred_col]
    elif fallback_col in df.columns:
        log.info(f"[{ratio_name}] '{preferred_col}' not found - using fallback '{fallback_col}'")
        return df[fallback_col]
    else:
        raise KeyError(f"[{ratio_name}] Neither column found.")