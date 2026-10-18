# Post-hoc analyses (not pre-registered)

## P1 Primary endpoint by domain (test split, cases with a consequential defect)

| method | news | tlc |
|---|---|---|
| retrain_on_alarm | 0.000 [0.00, 0.00] (n=49) | 0.000 [0.00, 0.00] (n=48) |
| validation_first | 0.102 [0.03, 0.16] (n=49) | 0.104 [0.00, 0.26] (n=48) |
| observational_attribution | 0.122 [0.00, 0.29] (n=49) | 0.188 [0.00, 0.25] (n=48) |
| full_rollback | 0.041 [0.00, 0.11] (n=49) | 0.021 [0.00, 0.05] (n=48) |
| bisect | 0.204 [0.08, 0.34] (n=49) | 0.667 [0.48, 0.83] (n=48) |
| bugdoc_shortcut | 0.388 [0.10, 0.68] (n=49) | 0.667 [0.48, 0.83] (n=48) |
| llm_report@luna | 0.469 [0.18, 0.76] (n=49) | 0.146 [0.00, 0.23] (n=48) |
| llm_tools@luna | 0.612 [0.45, 0.74] (n=49) | 0.375 [0.23, 0.55] (n=48) |
| llm_report@terra | 0.327 [0.08, 0.65] (n=49) | 0.167 [0.00, 0.28] (n=48) |
| llm_tools@terra | 0.796 [0.67, 0.87] (n=49) | 0.396 [0.24, 0.58] (n=48) |
| dod | 1.000 [1.00, 1.00] (n=49) | 0.479 [0.32, 0.75] (n=48) |
| dod_no_boundary | 0.184 [0.08, 0.27] (n=49) | 0.792 [0.69, 0.95] (n=48) |
| dod_b1 | 0.837 [0.62, 0.95] (n=49) | 0.354 [0.18, 0.67] (n=48) |
| dod_b1_uniform | 0.735 [0.51, 0.96] (n=49) | 0.250 [0.10, 0.52] (n=48) |
| blame_all_changes | 0.041 [0.00, 0.11] (n=49) | 0.062 [0.00, 0.09] (n=48) |

- news: dod - bugdoc_shortcut: {'n': 49, 'diff': 0.6122448979591837, 'ci': [0.3180976430976431, 0.9], 'p': 0.0005}
- news: dod - llm_tools@luna: {'n': 49, 'diff': 0.3877551020408163, 'ci': [0.2558139534883721, 0.5490441176470587], 'p': 0.0005}
- news: dod - dod_no_boundary: {'n': 49, 'diff': 0.8163265306122449, 'ci': [0.7272727272727273, 0.9215686274509803], 'p': 0.0005}
- tlc: dod - bugdoc_shortcut: {'n': 48, 'diff': -0.1875, 'ci': [-0.42424242424242425, 0.18524305555555523], 'p': 0.205}
- tlc: dod - llm_tools@luna: {'n': 48, 'diff': 0.10416666666666667, 'ci': [-0.020855978260869563, 0.3333333333333333], 'p': 0.134}
- tlc: dod - dod_no_boundary: {'n': 48, 'diff': -0.3125, 'ci': [-0.5227272727272727, -0.10344827586206896], 'p': 0.014}

## P2 TLC test cases not spanning the 2023-04 airport-fee event

88 TLC test cases (23 with a consequential defect)

- retrain_on_alarm: consequential 0.000 (n=23), false blame 0.000
- validation_first: consequential 0.174 (n=23), false blame 0.341
- observational_attribution: consequential 0.391 (n=23), false blame 0.455
- full_rollback: consequential 0.043 (n=23), false blame 0.159
- bisect: consequential 0.652 (n=23), false blame 0.000
- bugdoc_shortcut: consequential 0.652 (n=23), false blame 0.000
- llm_report@luna: consequential 0.304 (n=23), false blame 0.534
- llm_tools@luna: consequential 0.522 (n=23), false blame 0.057
- llm_report@terra: consequential 0.304 (n=23), false blame 0.391
- llm_tools@terra: consequential 0.565 (n=23), false blame 0.087
- dod: consequential 0.913 (n=23), false blame 0.000
- dod_no_boundary: consequential 0.913 (n=23), false blame 0.000
- dod_b1: consequential 0.522 (n=23), false blame 0.000
- dod_b1_uniform: consequential 0.435 (n=23), false blame 0.000
- blame_all_changes: consequential 0.130 (n=23), false blame 0.818

- pooled news + TLC (no 2023-04): dod - llm_tools@terra: {'n': 72, 'diff': 0.25, 'ci': [0.17777258566978194, 0.3800238095238094], 'p': 0.0005}
- pooled news + TLC (no 2023-04): dod - bugdoc_shortcut: {'n': 72, 'diff': 0.5, 'ci': [0.2615217391304348, 0.753090428090428], 'p': 0.0005}
- pooled news + TLC (no 2023-04): dod - llm_tools@luna: {'n': 72, 'diff': 0.3888888888888889, 'ci': [0.2840909090909091, 0.5272777222777222], 'p': 0.0005}
- pooled news + TLC (no 2023-04): dod - dod_no_boundary: {'n': 72, 'diff': 0.5555555555555556, 'ci': [0.27109692050608736, 0.767463131026659], 'p': 0.0005}

## P4 Sources of DoD false blame on TLC test cases

93 cases; boundary flags behind them: {'2023-04:airport_fee': 90, 'cases spanning 2023-04': 93, 'effect test:trip_adapter': 3, 'cases without a boundary flag': 3}

## P5 Source-coupled (T1) vs internal (T2/T3) consequential defects, test split

- news T1 dod: 1.000 (n=18)
- news T1 dod_no_boundary: 0.056 (n=18)
- news T1 bugdoc_shortcut: 0.056 (n=18)
- news T1 llm_tools@luna: 0.500 (n=18)
- news internal dod: 1.000 (n=31)
- news internal dod_no_boundary: 0.258 (n=31)
- news internal bugdoc_shortcut: 0.581 (n=31)
- news internal llm_tools@luna: 0.677 (n=31)
- tlc T1 dod: 0.667 (n=3)
- tlc T1 dod_no_boundary: 0.667 (n=3)
- tlc T1 bugdoc_shortcut: 0.667 (n=3)
- tlc T1 llm_tools@luna: 1.000 (n=3)
- tlc internal dod: 0.467 (n=45)
- tlc internal dod_no_boundary: 0.800 (n=45)
- tlc internal bugdoc_shortcut: 0.667 (n=45)
- tlc internal llm_tools@luna: 0.333 (n=45)

