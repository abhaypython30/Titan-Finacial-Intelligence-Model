# Forecast Log — Titan Company Ltd

This log records every material assumption, decision, and correction made
during model construction — kept separate from commit messages so the
full reasoning stays in one place.

---

## Week 1 — Data Cleaning & Ratio Foundation

- **Critical fix required before anything else worked:** the raw sheet
  labels the pre-tax profit metric `pbt`, not `ebt`. Every downstream
  formula referencing `df['ebt']` would have thrown a `KeyError` without
  a rename applied immediately after load.

- **Confirmed via balance sheet check:** `total_debt` in the raw sheet
  exactly equals `total_assets` in every year. Investigated using the
  raw balance sheet source and confirmed this is a labeling issue, not
  a data error: the liabilities-side "Total" (Equity + Reserves +
  Borrowings + Other Liabilities) and the assets-side "Total" are
  mathematically required to be equal by the balance sheet identity —
  the row was simply named `total_debt` when it's actually Total
  Liabilities. Real debt is the separate `debt` row, verified to exactly
  match the raw sheet's "Borrowings" line item (1,882.43 / 1,691.01 /
  2,392.98 / 3,562 / 5,638 / 7,275 / 9,367 / 15,528 / 20,777 / 30,621
  across FY17-26).

- **Face value confirmed as Rs.1** (constant across all 10 years, derived
  and cross-checked).

- **Gold Metal Loan / lease liability:** not separately broken out in
  this data source. Decision: proceed using the `debt` (Borrowings)
  figure as-is; if GML or lease liabilities are embedded within it,
  they are not separately decomposed. Documented as a known limitation.

- **EBITDA, EBIT, Gross Profit formulas verified** against the company's
  own `HistoricalFS` tab — all three reconcile exactly (e.g. FY24 EBITDA
  Rs.5,292cr matches Excel exactly).

- **Net Profit discrepancy investigated and resolved:** Data Sheet's
  `net_profit` initially did not match `HistoricalFS`'s reported Net
  Profit (gap grew from ~Rs.98cr in FY18 to over Rs.530cr by FY24).
  Root cause identified as Non-Controlling Interest (NCI) in the
  consolidated accounts (e.g. CaratLane's minority stake prior to a
  FY24 stake increase) — reported Net Profit is attributable to
  shareholders only, after the NCI share is removed, so it does not
  always equal EBT − Tax exactly. Net Profit is therefore treated as a
  directly-sourced figure, not derived via formula.

- **EBT definition confirmed to include Other Income at source.**
  HistoricalFS explicitly labels this row "Earning Before Tax + Other
  Inc" (Rs.4,623cr for FY24). Verified the `ebt` value already present in
  `titan_clean.csv` matches this combined figure exactly.

- **Minor bug fixed while building:** intermediate CSV saves were
  initially missing `index=False`, which would silently accumulate an
  `Unnamed: 0` column on repeated runs. Fixed.

## Week 2 — Era Analysis, CAGR, Anomaly Detection

- **COVID impact resolved as growth-side, not margin-side.** Sales
  growth fell sharply during COVID (22.13% Pre-COVID -> 4.62% COVID)
  while EBITDA margin barely moved (9.69% -> 9.83%). Interpretation: a
  more variable cost structure (retail rent, staff scaling with
  footfall) absorbed the demand shock without materially compressing
  margin on the sales that did occur.
- **Recovery era shows overshoot, not just return to baseline** (32.61%
  sales growth, above the 22.13% Pre-COVID rate) — partly organic,
  partly tied to the CaratLane stake increase.
- **CCC and Debt/EBITDA show a steady structural climb across all three
  eras** (CCC: 77.5 -> 90.5 -> 113.4; Debt/EBITDA: 1.27 -> 2.35 -> 2.86),
  not a COVID-shaped dip-and-recovery. Attributed to inventory growth
  and acquisition financing rather than the pandemic itself.
- **CAGR findings (10-year period, FY17-26):** Debt CAGR (36.33%)
  exceeds EBITDA CAGR (24.49%); Inventory CAGR (27.14%) exceeds Sales
  CAGR (23.34%) — both flagged, consistent with acquisition-financed
  growth and rising working-capital intensity.
- **ROCE anomaly: FY2021 (10.28%, vs a ~18% average)** — explained by
  COVID-related capital-turnover slowdown, not a data error. Recovered
  in subsequent years.
- Output: `titan_pipeline_new.csv` built — ready for Week 3.

## Week 3 — SQL Analysis & Multi-Company Schema

- Built a 4-table normalized schema (companies, income_statement,
  balance_sheet, ratios) with `company_id` as a shared key, designed to
  support future multi-company work.
- **Bug found and fixed:** the original load logic had a duplicate-guard
  function that was silently overwritten by a later function of the same
  name, meaning re-running the load script would have inserted duplicate
  rows. Fixed with a DELETE-then-INSERT pattern scoped to Titan's own
  company_id, making re-runs after a data correction safe.
- **Bug found and fixed:** window functions (LAG/RANK/NTILE) needed
  explicit `PARTITION BY company_name` once the schema held more than
  one company's data, to prevent trend/ranking calculations from
  bleeding across company boundaries.
- **Bug found and fixed:** a query was pulling the mislabeled
  `total_debt` column instead of the verified `debt` column — corrected.
- Established Titan's own verified EBITDA margin benchmark range
  (7.97%–12.03%) via SQL, used as a sanity-check anchor in later weeks.

## Week 4, Day 1 — WACC & Core Assumption Derivation

- **Beta = 0.18** (Yahoo Finance, 5Y monthly) — notably low, consistent
  with a steady, lower-market-correlation consumer discretionary business.
- **Implied Kd = 3.42%** — initially flagged as unusual (below the
  risk-free rate, atypical for corporate borrowing). INVESTIGATED AND
  CONFIRMED, not a data error: management referenced Gold Metal Loan
  (GML) cost at "~3%" directly on an analyst earnings call. Since GML is
  a significant share of gold-sourcing debt financing, the blended Kd
  computed from aggregate interest/debt data is legitimately pulled
  toward this externally-confirmed rate. DECISION: retained the
  data-implied Kd (3.42%) as the primary figure, documented explicitly
  as GML-driven rather than swapped for a market-based alternative.
- **Resulting WACC = 4.58%** (Ke=8.52%, Kd after-tax=2.57%, E-weight
  33.90%, D-weight 66.10%). PRESENTATION NOTE for the Week7 dashboard:
  annotate this figure directly wherever shown ("Low Kd reflects Gold
  Metal Loan financing, ~3% per management commentary — not a data
  anomaly").
- **Known downstream implication**: a WACC this low tightens the
  terminal-growth safety buffer significantly (max allowed ~2.58% at a
  standard 2pp buffer), which later proved to be the single most
  consequential structural fact in the whole model (see Week5 Day4).

## Week 4, Day 2 — Revenue Growth Scenarios

- **Fixed a measurement design flaw**: the initial COVID check compared
  "last 3 years" incl./excl. COVID — but Titan's last 3 years (2024-2026)
  never actually contain a COVID year, making that comparison show ~0
  difference regardless of the decision. Corrected to compare
  full-distribution Bear/Base/Bull percentiles directly with vs without
  COVID years — this is the metric that actually drives the locked
  scenario values.
- **Decision:** COVID years (2020-2021) excluded from the Base case.
  Full-distribution Base (P50) shifts from 22.70% (incl.) to 25.90%
  (excl.) — a real, decision-relevant 3.2pp difference.
- **Final locked values:** Bear 22.13%, Base 25.90%, Bull 36.97%.

## Week 4, Day 3 — EBITDA Margin & Cost Structure

- Used the existing verified `ebitda` column rather than recomputing
  from cost lines, avoiding the kind of formula-mismatch risk found
  elsewhere in this project.
- **Finding:** `other_expenses` is the strongest correlated driver of
  margin movement (-0.88) — not raw material/gold cost as initially
  predicted. Reported the actual finding rather than forcing the
  prediction. Fixed an earlier omission where `other_mfr_exp` was
  missing from the tested cost-line list.
- Margin COVID impact confirmed minimal (Base P50 diff = 0.00pp),
  consistent with Week2's finding that COVID affected growth, not margin.
- **Final locked values:** Bear 9.51%, Base 10.14%, Bull 10.67% — a
  remarkably tight ~1.2pp band.

## Week 4, Day 4 — CAPEX%, Depreciation%, Tax Rate, Terminal Growth

- Effective tax rate (26.78%) reused from Day 1's implied calculation.
- **CAPEX% (2.81%) and Depreciation% (1.08%) both very low** — consistent
  with an asset-light, leased-store retail model rather than owned
  manufacturing capacity.
- **Terminal growth capped to 2.58%** — the conventional 4% assumption
  exceeded the safe buffer below the low WACC (4.58%), triggering the
  hard flow-check cap automatically.

## Week 4, Day 5 — FY27-31 Forecast & DCF Valuation

- **Shares outstanding available directly** via the `equity_shares`
  column — cross-checked against a derivation from Share Capital ÷ Face
  Value, matching within 0.00%.
- **Critical bug found and fixed:** an initial flat-growth version (no
  tapering) produced deeply implausible NEGATIVE valuations across all
  three scenarios — worse for Bull than Bear, the opposite of expected
  ordering. Root cause: Titan's high working-capital intensity (~40% of
  sales, tied to inventory) combined with high locked growth rates
  (22-37%) held flat for 5 straight years, compounding a cash drag that
  overwhelmed margin-driven cash generation every year. FIXED by
  introducing linear growth tapering toward terminal growth by year 5 —
  a standard DCF refinement. Post-fix valuations landed in a plausible
  range consistent with real-world market capitalization scale.
- **Final valuation (per share):** Bear Rs.2,199.83, Base Rs.2,761.44,
  Bull Rs.3,827.55 — a notably tight spread relative to the underlying
  margin band's narrowness.

## Week 5, Day 1-2 — Sensitivity Grids

- WACC x Terminal Growth grid and Growth x Margin grid built, ranges
  centered on Titan's own locked values (not reused from any other
  project's ranges).

## Week 5, Day 3 — Monte Carlo Methodology (two rounds of correction)

- **Round 1 issue (external methodology review):** original
  implementation sampled ONE (growth, margin) pair per simulation and
  applied it flat across all 5 forecast years — meant only a handful of
  distinct outcomes were possible regardless of simulation count. FIXED:
  now samples a NEW pair independently for each forecast year. Documented
  tradeoff: this assumes zero year-to-year correlation, which likely
  overstates 5-year cumulative volatility versus reality.
- **Round 1 issue (external methodology review):** 2022's growth
  (33.06%) is calculated against a still-COVID-suppressed 2021 base
  (2.81% growth), producing an inflated "recovery bounce" figure. FIXED:
  bootstrap pool's COVID exclusion window extended to [2020, 2021, 2022]
  for Monte Carlo specifically. NOTE: Week4 Day2/3/4 still use
  [2020, 2021] — this inconsistency is deliberate and flagged, not yet
  reconciled project-wide.
- **Round 2 issue (self-caught after first re-run):** removing the
  taper entirely for per-year sampling caused ALL 5000 simulations to
  produce negative equity value (100%). Root cause: every year in the
  6-year bootstrap pool has growth between 18-45% — compounding 5
  consecutive years of unmoderated high growth against the ~40% NWC
  ratio guarantees negative FCFF every year, for every combination. This
  was a mathematical certainty given the inputs, not a genuine
  probabilistic finding. FIXED: reintroduced tapering, applied to each
  year's independently sampled rate.
- **Final result**: mean Rs.3,023.96, median Rs.2,882.35, range
  Rs.1,988.73-Rs.5,512.82, 0% probability of negative equity. Median
  closely matches the deterministic Base case (Rs.2,761.44).

## Week 5, Day 4 — Driver Ranking

- **WACC ranks #1** (Rs.1,602.86 swing, 58.0% of base value) — ahead of
  EBITDA margin (#2, 45.5%), terminal growth (#3, 24.8%), and revenue
  growth (#4, 10.3%). This is driven by the thin buffer between WACC
  (4.58%) and terminal growth (2.58%) — because terminal value scales
  with 1/(WACC−g), a small WACC move produces an outsized swing when
  that denominator is already thin. This is a structural fragility tied
  directly to the Gold Metal Loan financing story from Week4 Day1, not
  a coincidence.

## Week 6, Day 1-2 — Implied Multiples & Full Integrity Test

- **Implied EV/EBITDA**: Bear 26.42x, Base 32.40x, Bull 43.76x.
- Cross-checked against the company's own current market multiple
  (49.80x) and the Retail-Cyclical sector median (8.71x). All three DCF
  scenarios, including Bull, sit below the current market pricing —
  likely reflecting the growth-taper assumption versus whatever longer
  sustained-growth assumption the market may be implicitly pricing in.
  Stated as a quantified, explainable gap, not evidence the model is wrong.
- **Full integrity test: 13/13 checks passed** across Week4 Day1-5 and
  Week5 Day1-4, confirming no drift or regression since each piece was
  originally built and locked.

---

## Outstanding Items

1. Week5 Day3's Monte Carlo uses an extended COVID exclusion window
   ([2020,2021,2022]) versus Week4 Day2/3/4's [2020,2021] — flagged,
   not yet reconciled project-wide.
2. Gold Metal Loan / lease liability amounts remain embedded within the
   aggregate `debt` figure, not separately disclosed or decomposed.