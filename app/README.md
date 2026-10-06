# Semiconductor Credit Intelligence

Launch from the repository root (the local `.venv` has been prepared):

```powershell
.\.venv\Scripts\python.exe -m streamlit run app/community_main.py --server.address 127.0.0.1 --server.port 8501
```

Open http://127.0.0.1:8501. For a fresh machine, create a Python 3.12 environment and install `requirements.txt` first. No public deployment is configured by this work.

## Reference design update

The dashboard now follows the approved light portfolio reference: navy icon navigation, large titles, blue/teal stress bars, a warning-signal donut, icon KPI cards and a compact evidence review table. `reference_theme.py` applies the shared visual system to all eight workspaces without external font requests or generated images. Top filters are shared; search and additional filters are in the sidebar expander.

Universe cards always describe the complete ecosystem; charts and evidence coverage describe the selected cohort. The overview shows the four highest archived severe-stress scores and five highest-priority flagged projects; full records, downloads and geographic concentration remain in the expandable portfolio register. Chart scores keep the actual 0–100 scale. The exported report is a working CSV of selected records.

The fresh redesign preview runs on http://127.0.0.1:8502. To run it there, replace `8501` with `8502` in the launch command above. Restart any older server to load the new imported presentation modules.

The analysis-page refinement adds larger color-consistent PCA markers, segment composition, percentage-formatted explained variation, blue/amber stress comparisons and a chart-first Monte Carlo page with mean/P95/P99 markers. Model Health presents human-readable readiness checks instead of JSON. Coverage denominators distinguish manufacturing from the whole ecosystem. The absent SEM-0002 borrower-panel entry is reported as a financial evidence collection gap, not repaired with fabricated data or another project's figures. Monte Carlo uses completed simulations; new reruns remain unavailable until reproducibility checks are complete.

## Architecture

The existing `community_main.py` → `banking_dashboard_v2.render_app` entry point now uses `intelligence_dashboard.py`. Existing legacy page functions remain for compatibility. `intelligence_data.py` owns the explicit source registry, schema checks, content-hash cache invalidation, filters and identifier joins. `intelligence_services.py` owns calculations and scenario storage. Styling reuses `ui_theme.py` and the approved reference overrides in `reference_theme.py`.

All eight workspaces use the same selected project IDs. Manufacturing is the default scope; ecosystem and design/DLI scopes remain available. The present data contains 36 ecosystem observations, 12 manufacturing projects and 24 design/DLI projects; these counts are computed from source rows, never fixed in the UI. Manufacturing investment totals ₹1,64,301 crore. Investment is not bank exposure. Financial evidence coverage is source-row coverage, not proof of sufficient underwriting.

## Data precedence and failure behavior

Every exact source path, required columns and uniqueness key is in `SOURCES` in `intelligence_data.py`. There is no recursive latest-file lookup or modification-time source selection.

1. Ecosystem master supplies the universe and exact source-project ID mapping. Canonical manufacturing data supplies current identity/investment and any newly canonicalized manufacturing rows.
2. Validated cluster assignments supply archived PCA coordinates and structural segments, joined by ecosystem ID.
3. Integrated dashboard master supplies current banking evidence/status fields; the integrated committee register adds research grades.
4. Phase 3E supplies deterministic inputs and saved scenarios. Phase 6B supplies exact missing Monte Carlo statistics, including P95, by project ID.
5. Borrower and EWS panels supply additional evidence fields. Final frozen bank-credit outputs fill remaining historical research fields only.

An existing non-missing value wins over a lower-precedence source. There is no substitute percentile, zero imputation, fuzzy entity join, or silent key deduplication. Missing files, required columns, nonnumeric numeric fields, null keys and duplicate keys mark a source unavailable. Missing expected matches and orphan identifiers are reported in Health. Optional sources degrade to explicit unavailable states. If the ecosystem identity contract fails, the app stops with an actionable source-health table.

The cache key hashes registered file content on each interaction. Displayed timestamps are file modification times in UTC, not asserted publication dates. Health distinguishes artifact availability from validation evidence.

## Analytical connections and boundaries

- **Structural ML:** reads the actual Phase 3B PCA coordinates, cluster assignments, diagnostics and economic interpretation; Phase 3A explained variance; frozen scaler/components/centroids, manifest and validation report. No fitting, new cluster assignment or preprocessing change occurs on application load.
- **Stress:** imports `stress_score` and `validate_deterministic_method` from `13_Continuous_Ingestion/07_Automated_Evaluation/evaluate_new_projects.py`. Every new calculation first reproduces the full archived reference. Baseline/mild/moderate/severe use 0/.10/.25/.50 severity. Custom severity stays within 0–.50. Only the four macro channels change. Contributions are exact weighted score terms, not SHAP. Rankings are within the selected supported cohort. Unsupported newly added projects remain unscored.
- **Monte Carlo:** reads saved project summaries and all 10,000 actual archived draws. Mean and P95 reconstruct from raw draws in tests. The Phase 13F/15E reproducibility gate remains open; original random seed, shock generation and dependence contract are not recovered. Reruns are deliberately unavailable. New-project gate records and full-cohort cross-method statistics are visible.
- **Allocation:** original solver/objective code is not present in the inspected repository. The dashboard therefore selects actual Phase 4B archived policies and scales their saved shares to the entered budget. It checks full portfolio identity, finite/nonnegative shares, total budget, project minimum/maximum and state maximum. Tighter review limits can reject a saved policy but do not solve for replacement shares. All archived policies are tested. Historical sensitivity tables are explicitly saved outputs. Budget scaling does not optimize the budget or change concentration. It requires the full supported manufacturing portfolio.
- **Committee/evidence:** integrated committee posture and current EWS remain distinct from legacy research grades and historical EWS. Parent/group financial statement scope is shown. Missing data remains missing. Snapshot monitoring is not longitudinal monitoring.

Presentations were read as context. Their proposed macroeconomic controls and stronger Monte Carlo validation language are not treated as implemented, reproducible capabilities. No PD, ECL, official ratings or automatic sanction decisions are produced.

## Exports and scenarios

Visible download controls produce UTF-8 CSV files. Exported text is protected against spreadsheet formula injection. Numeric missing cells remain empty in sortable UI tables and are labeled “Not available” in CSV exports. Project summary exports include available evidence and status fields. User-saved stress/allocation scenarios go only to `output/dashboard_scenarios/`, paired with JSON settings, UTC time and source hashes. Reference datasets and frozen artifacts are not modified.

## Verification

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

The 13 automated tests cover authoritative counts, exact P95 joins, filtering, missing sources, duplicate/null IDs, bad schemas, incomplete records, missing percentile preservation, deterministic reproduction and bounds, archived MC reconstruction, all saved allocation policies and infeasible limits, CSV decoding, separate scenario storage, cache invalidation, all eight pages, project selection/comparison, scenario reset and budget changes. See `tests/test_intelligence.py`.

Local HTTP health returned 200. Browser inspection verified initial loading, the Tata search filter, stress scenario selection and a CSV download. Desktop and smaller viewport review is recorded in `output/dashboard_qa/verification.md`.
