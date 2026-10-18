# 08 — v2 held-out domains (benchmark expansion)

Built 2026-10-06, before any diagnosis method was run on them (see v2/PROTOCOL_V2.md).

## Sources (all public, no login; data/raw_v2/MANIFEST.json has URL, size, SHA-256)

| domain | records | periods | sample per period | task |
|---|---|---|---|---|
| divvy | Divvy (Chicago bike share) trip files, divvy-tripdata.s3.amazonaws.com | quarters 2014-Q1..2026-Q3 (51) | 100,000 trips | member vs casual rider |
| hmda | HMDA loan/application records: CFPB historic national files 2012-2017; FFIEC Data Browser API 2018-2025 (CO, OR, TN) | years 2012-2025 (14) | 150,000 applications with action 1 or 3 | denied vs originated |
| bts | BTS Reporting Carrier On-Time Performance, transtats.bts.gov PREZIP | months 1/4/7/10, 2015-2026 (47) | 150,000 flights | arrival delay >= 15 min |

## Dated published changes (found from the bronze profiles, data/bronze/<domain>/_profile.json)

**Divvy:** 2016-Q3 timestamps gain seconds; 2017-Q1 start/stop columns renamed; 2017-Q4 seconds dropped again;
2018-Q1 long-form headers, ISO timestamps, durations with thousands separators; 2018-Q2 short headers; 2019-Q2
long headers; 2019-Q3 short headers; 2020-Q1 new layout (member/casual recode, coordinates, duration/gender/birth
year removed; same quarter as the pandemic); 2020-Q3 blank station ids (dockless e-bikes); 2020-Q4 alphanumeric
station ids; 2024-Q2 fractional-second timestamps.

**HMDA:** 2018 record format rebuilt under amended Regulation C: amount in dollars (was thousands), purpose,
occupancy and property recoded, state as postal code, county as 5-digit FIPS, tract fields renamed, new product
flags (open-end, reverse mortgage, business purpose).

**BTS:** none — history is republished in the current layout. Real-world changes only (carrier mergers, the
2020 pandemic), which makes it a control domain for false blame without schema events.

## Defect catalogs

Tiers: T1 source-coupled (a stale or wrongly maintained adapter at a dated change), T2 library upgrade with an
effect, T3 incident class, T3r replay of a documented real incident; benign: B (refactor), T2b (upgrade without
effect).

| domain | T1 | T2 | T3 / T3r |
|---|---|---|---|
| divvy | positional column mapping (2020+), user-type rule not updated, coordinates still from the 2017 station table, blank ids compared as equal, thousands separators not stripped, timestamps parsed with the previous format | pandas 3: epoch via astype(int64) (duration, 2020+); chained assignment no-op | month/day swap (T3r, nyc-taxi-data #3), end-station key bug, encoder refit, unseen categories as reference (T3r, scikit-learn #34549) |
| hmda | amount kept in dollars, purpose codes not recoded (T1, cf. folktables #22), occupancy alias, county key built the old way, new product flags ignored | pandas 3 chained-assignment sentinel no-op | np.nan_to_num(x, -1) (T3r, folktables #39), inverted loan-to-income, encoder refit, unseen as reference (T3r) |
| bts | — | pandas 3: day of year via astype(int64); chained assignment no-op | hhmm read as minutes, label boundary (> vs >=), diverted flights kept, destination key bug, distance in km, encoder refit, unseen as reference (T3r) |

Incident sources (verified by an independent search, links in the scouting notes): folktables issues #22 and #39;
toddwschneider/nyc-taxi-data issues #3 and #8; pandas-dev/pandas issue #65308 and the pandas 3.0 release notes
(copy-on-write, datetime resolution inference); scikit-learn issue #34549.

## Construction checks (no diagnosis method run)

`v2/code/check_domains.py` runs the correct pipeline on every period and reports rows, label rate, missing
rates, and the reference models' holdout accuracy under the correct pipeline (world drift alone). Divvy example
(reference 2016-Q3, holdout accuracy 0.871): 2019-Q3 0.829, 2020-Q3 0.684, 2024-Q2 0.695 — large real drift.
