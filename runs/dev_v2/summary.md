# Summary of dev_v2

100 cases
by domain: {'acs': 100}

### All cases

| method | n | correct | type_correct | regret | unnecessary_retrain | missed_defect | false_blame | cost_s |
|---|---|---|---|---|---|---|---|---|
| bisect | 100 | 0.640 | 0.640 | 0.002 | 0.120 | 0.270 | 0.000 | 2.71 |
| bugdoc_shortcut | 100 | 0.640 | 0.640 | 0.002 | 0.120 | 0.270 | 0.000 | 13.19 |
| full_rollback | 100 | 0.640 | 0.640 | 0.002 | 0.120 | 0.270 | 0.000 | 0.95 |
| observational_attribution | 100 | 0.170 | 0.210 | 0.014 | 0.000 | 0.150 | 0.680 | 0.00 |
| retrain_on_alarm | 100 | 0.640 | 0.640 | 0.002 | 0.120 | 0.270 | 0.000 | 0.00 |
| validation_first | 100 | 0.490 | 0.380 | 0.009 | 0.060 | 0.150 | 0.060 | 0.00 |
| dod | 100 | 0.630 | 0.520 | 0.008 | 0.070 | 0.100 | 0.000 | 50.45 |
| dod_no_boundary | 100 | 0.350 | 0.300 | 0.001 | 0.240 | 0.100 | 0.500 | 5.52 |
| dod_no_prior | 100 | 0.630 | 0.520 | 0.008 | 0.070 | 0.100 | 0.000 | 42.61 |
| dod_uniform_cost | 100 | 0.630 | 0.520 | 0.008 | 0.070 | 0.100 | 0.000 | 42.85 |

### Cases with a consequential defect

| method | n | correct | type_correct | regret | unnecessary_retrain | missed_defect | false_blame | cost_s |
|---|---|---|---|---|---|---|---|---|
| bisect | 27 | 0.000 | 0.000 | 0.003 | 0.111 | 1.000 | 0.000 | 3.02 |
| bugdoc_shortcut | 27 | 0.000 | 0.000 | 0.003 | 0.111 | 1.000 | 0.000 | 13.10 |
| full_rollback | 27 | 0.000 | 0.000 | 0.003 | 0.111 | 1.000 | 0.000 | 1.15 |
| observational_attribution | 27 | 0.185 | 0.556 | 0.013 | 0.000 | 0.556 | 0.407 | 0.00 |
| retrain_on_alarm | 27 | 0.000 | 0.000 | 0.003 | 0.111 | 1.000 | 0.000 | 0.00 |
| validation_first | 27 | 0.148 | 0.370 | 0.012 | 0.037 | 0.556 | 0.074 | 0.00 |
| dod | 27 | 0.370 | 0.370 | 0.012 | 0.037 | 0.370 | 0.000 | 43.03 |
| dod_no_boundary | 27 | 0.444 | 0.556 | 0.002 | 0.222 | 0.370 | 0.111 | 6.14 |
| dod_no_prior | 27 | 0.370 | 0.370 | 0.012 | 0.037 | 0.370 | 0.000 | 37.03 |
| dod_uniform_cost | 27 | 0.370 | 0.370 | 0.012 | 0.037 | 0.370 | 0.000 | 37.21 |

### Silent consequential defects (pass validation)

| method | n | correct | type_correct | regret | unnecessary_retrain | missed_defect | false_blame | cost_s |
|---|---|---|---|---|---|---|---|---|
| bisect | 9 | 0.000 | 0.000 | 0.003 | 0.111 | 1.000 | 0.000 | 3.32 |
| bugdoc_shortcut | 9 | 0.000 | 0.000 | 0.003 | 0.111 | 1.000 | 0.000 | 9.59 |
| full_rollback | 9 | 0.000 | 0.000 | 0.003 | 0.111 | 1.000 | 0.000 | 1.60 |
| observational_attribution | 9 | 0.000 | 0.556 | 0.008 | 0.000 | 1.000 | 0.778 | 0.00 |
| retrain_on_alarm | 9 | 0.000 | 0.000 | 0.003 | 0.111 | 1.000 | 0.000 | 0.00 |
| validation_first | 9 | 0.000 | 0.000 | 0.003 | 0.111 | 1.000 | 0.000 | 0.00 |
| dod | 9 | 0.333 | 0.333 | 0.003 | 0.111 | 0.667 | 0.000 | 18.44 |
| dod_no_boundary | 9 | 0.333 | 0.556 | 0.003 | 0.111 | 0.667 | 0.333 | 5.97 |
| dod_no_prior | 9 | 0.333 | 0.333 | 0.003 | 0.111 | 0.667 | 0.000 | 17.84 |
| dod_uniform_cost | 9 | 0.333 | 0.333 | 0.003 | 0.111 | 0.667 | 0.000 | 18.13 |

### Loud consequential defects (fail validation)

| method | n | correct | type_correct | regret | unnecessary_retrain | missed_defect | false_blame | cost_s |
|---|---|---|---|---|---|---|---|---|
| bisect | 18 | 0.000 | 0.000 | 0.003 | 0.111 | 1.000 | 0.000 | 2.88 |
| bugdoc_shortcut | 18 | 0.000 | 0.000 | 0.003 | 0.111 | 1.000 | 0.000 | 14.86 |
| full_rollback | 18 | 0.000 | 0.000 | 0.003 | 0.111 | 1.000 | 0.000 | 0.92 |
| observational_attribution | 18 | 0.278 | 0.556 | 0.016 | 0.000 | 0.333 | 0.222 | 0.00 |
| retrain_on_alarm | 18 | 0.000 | 0.000 | 0.003 | 0.111 | 1.000 | 0.000 | 0.00 |
| validation_first | 18 | 0.222 | 0.556 | 0.016 | 0.000 | 0.333 | 0.111 | 0.00 |
| dod | 18 | 0.389 | 0.389 | 0.016 | 0.000 | 0.222 | 0.000 | 55.32 |
| dod_no_boundary | 18 | 0.500 | 0.556 | 0.001 | 0.278 | 0.222 | 0.000 | 6.22 |
| dod_no_prior | 18 | 0.389 | 0.389 | 0.016 | 0.000 | 0.222 | 0.000 | 46.62 |
| dod_uniform_cost | 18 | 0.389 | 0.389 | 0.016 | 0.000 | 0.222 | 0.000 | 46.75 |

### No consequential defect (drift, benign changes, nothing)

| method | n | correct | type_correct | regret | unnecessary_retrain | missed_defect | false_blame | cost_s |
|---|---|---|---|---|---|---|---|---|
| bisect | 73 | 0.877 | 0.877 | 0.001 | 0.123 | 0.000 | 0.000 | 2.60 |
| bugdoc_shortcut | 73 | 0.877 | 0.877 | 0.001 | 0.123 | 0.000 | 0.000 | 13.23 |
| full_rollback | 73 | 0.877 | 0.877 | 0.001 | 0.123 | 0.000 | 0.000 | 0.88 |
| observational_attribution | 73 | 0.164 | 0.082 | 0.015 | 0.000 | 0.000 | 0.781 | 0.00 |
| retrain_on_alarm | 73 | 0.877 | 0.877 | 0.001 | 0.123 | 0.000 | 0.000 | 0.00 |
| validation_first | 73 | 0.616 | 0.384 | 0.008 | 0.068 | 0.000 | 0.055 | 0.00 |
| dod | 73 | 0.726 | 0.575 | 0.006 | 0.082 | 0.000 | 0.000 | 53.19 |
| dod_no_boundary | 73 | 0.315 | 0.205 | 0.001 | 0.247 | 0.000 | 0.644 | 5.30 |
| dod_no_prior | 73 | 0.726 | 0.575 | 0.006 | 0.082 | 0.000 | 0.000 | 44.68 |
| dod_uniform_cost | 73 | 0.726 | 0.575 | 0.006 | 0.082 | 0.000 | 0.000 | 44.94 |

### Cases where the performance alarm fires (drop >= 0.01)

| method | n | correct | type_correct | regret | unnecessary_retrain | missed_defect | false_blame | cost_s |
|---|---|---|---|---|---|---|---|---|
| bisect | 58 | 0.621 | 0.621 | 0.001 | 0.207 | 0.224 | 0.000 | 2.42 |
| bugdoc_shortcut | 58 | 0.621 | 0.621 | 0.001 | 0.207 | 0.224 | 0.000 | 16.42 |
| full_rollback | 58 | 0.621 | 0.621 | 0.001 | 0.207 | 0.224 | 0.000 | 0.64 |
| observational_attribution | 58 | 0.052 | 0.052 | 0.023 | 0.000 | 0.069 | 0.741 | 0.00 |
| retrain_on_alarm | 58 | 0.621 | 0.621 | 0.001 | 0.207 | 0.224 | 0.000 | 0.00 |
| validation_first | 58 | 0.345 | 0.276 | 0.014 | 0.103 | 0.069 | 0.069 | 0.00 |
| dod | 58 | 0.466 | 0.414 | 0.011 | 0.121 | 0.069 | 0.000 | 72.08 |
| dod_no_boundary | 58 | 0.190 | 0.172 | 0.001 | 0.207 | 0.069 | 0.707 | 6.28 |
| dod_no_prior | 58 | 0.466 | 0.414 | 0.011 | 0.121 | 0.069 | 0.000 | 59.89 |
| dod_uniform_cost | 58 | 0.466 | 0.414 | 0.011 | 0.121 | 0.069 | 0.000 | 60.22 |

### Tier T1

| method | n | correct | type_correct | regret | unnecessary_retrain | missed_defect | false_blame | cost_s |
|---|---|---|---|---|---|---|---|---|
| bisect | 28 | 0.500 | 0.500 | 0.001 | 0.179 | 0.357 | 0.000 | 2.58 |
| bugdoc_shortcut | 28 | 0.500 | 0.500 | 0.001 | 0.179 | 0.357 | 0.000 | 13.46 |
| full_rollback | 28 | 0.500 | 0.500 | 0.001 | 0.179 | 0.357 | 0.000 | 0.75 |
| observational_attribution | 28 | 0.179 | 0.143 | 0.019 | 0.000 | 0.000 | 0.500 | 0.00 |
| retrain_on_alarm | 28 | 0.500 | 0.500 | 0.001 | 0.179 | 0.357 | 0.000 | 0.00 |
| validation_first | 28 | 0.393 | 0.357 | 0.014 | 0.107 | 0.000 | 0.071 | 0.00 |
| dod | 28 | 0.571 | 0.536 | 0.010 | 0.107 | 0.000 | 0.000 | 56.90 |
| dod_no_boundary | 28 | 0.357 | 0.250 | 0.000 | 0.357 | 0.000 | 0.429 | 5.55 |
| dod_no_prior | 28 | 0.571 | 0.536 | 0.010 | 0.107 | 0.000 | 0.000 | 46.72 |
| dod_uniform_cost | 28 | 0.571 | 0.536 | 0.010 | 0.107 | 0.000 | 0.000 | 46.94 |

### Tier T1+T2

| method | n | correct | type_correct | regret | unnecessary_retrain | missed_defect | false_blame | cost_s |
|---|---|---|---|---|---|---|---|---|
| bisect | 4 | 0.500 | 0.500 | 0.000 | 0.250 | 0.500 | 0.000 | 2.49 |
| bugdoc_shortcut | 4 | 0.500 | 0.500 | 0.000 | 0.250 | 0.500 | 0.000 | 28.04 |
| full_rollback | 4 | 0.500 | 0.500 | 0.000 | 0.250 | 0.500 | 0.000 | 0.65 |
| observational_attribution | 4 | 0.250 | 0.250 | 0.015 | 0.000 | 0.000 | 0.500 | 0.00 |
| retrain_on_alarm | 4 | 0.500 | 0.500 | 0.000 | 0.250 | 0.500 | 0.000 | 0.00 |
| validation_first | 4 | 0.250 | 0.250 | 0.015 | 0.000 | 0.000 | 0.000 | 0.00 |
| dod | 4 | 0.250 | 0.250 | 0.015 | 0.000 | 0.000 | 0.000 | 139.59 |
| dod_no_boundary | 4 | 0.250 | 0.250 | 0.000 | 0.250 | 0.000 | 0.500 | 7.46 |
| dod_no_prior | 4 | 0.250 | 0.250 | 0.015 | 0.000 | 0.000 | 0.000 | 105.46 |
| dod_uniform_cost | 4 | 0.250 | 0.250 | 0.015 | 0.000 | 0.000 | 0.000 | 105.28 |

### Tier T1+T3

| method | n | correct | type_correct | regret | unnecessary_retrain | missed_defect | false_blame | cost_s |
|---|---|---|---|---|---|---|---|---|
| bisect | 6 | 0.667 | 0.667 | 0.002 | 0.167 | 0.333 | 0.000 | 2.54 |
| bugdoc_shortcut | 6 | 0.667 | 0.667 | 0.002 | 0.167 | 0.333 | 0.000 | 9.36 |
| full_rollback | 6 | 0.667 | 0.667 | 0.002 | 0.167 | 0.333 | 0.000 | 0.69 |
| observational_attribution | 6 | 0.000 | 0.167 | 0.025 | 0.000 | 0.333 | 0.667 | 0.00 |
| retrain_on_alarm | 6 | 0.667 | 0.667 | 0.002 | 0.167 | 0.333 | 0.000 | 0.00 |
| validation_first | 6 | 0.333 | 0.333 | 0.018 | 0.167 | 0.333 | 0.000 | 0.00 |
| dod | 6 | 0.500 | 0.333 | 0.013 | 0.167 | 0.333 | 0.000 | 52.61 |
| dod_no_boundary | 6 | 0.333 | 0.167 | 0.002 | 0.167 | 0.333 | 0.500 | 7.27 |
| dod_no_prior | 6 | 0.500 | 0.333 | 0.013 | 0.167 | 0.333 | 0.000 | 46.16 |
| dod_uniform_cost | 6 | 0.500 | 0.333 | 0.013 | 0.167 | 0.333 | 0.000 | 47.12 |

### Tier T2

| method | n | correct | type_correct | regret | unnecessary_retrain | missed_defect | false_blame | cost_s |
|---|---|---|---|---|---|---|---|---|
| bisect | 20 | 0.850 | 0.850 | 0.001 | 0.150 | 0.000 | 0.000 | 2.82 |
| bugdoc_shortcut | 20 | 0.850 | 0.850 | 0.001 | 0.150 | 0.000 | 0.000 | 16.22 |
| full_rollback | 20 | 0.850 | 0.850 | 0.001 | 0.150 | 0.000 | 0.000 | 1.15 |
| observational_attribution | 20 | 0.150 | 0.000 | 0.013 | 0.000 | 0.000 | 0.850 | 0.00 |
| retrain_on_alarm | 20 | 0.850 | 0.850 | 0.001 | 0.150 | 0.000 | 0.000 | 0.00 |
| validation_first | 20 | 0.550 | 0.000 | 0.013 | 0.000 | 0.000 | 0.100 | 0.00 |
| dod | 20 | 0.550 | 0.350 | 0.013 | 0.050 | 0.000 | 0.000 | 66.84 |
| dod_no_boundary | 20 | 0.350 | 0.350 | 0.001 | 0.250 | 0.000 | 0.600 | 5.54 |
| dod_no_prior | 20 | 0.550 | 0.350 | 0.013 | 0.050 | 0.000 | 0.000 | 55.39 |
| dod_uniform_cost | 20 | 0.550 | 0.350 | 0.013 | 0.050 | 0.000 | 0.000 | 55.56 |

### Tier T2+T3

| method | n | correct | type_correct | regret | unnecessary_retrain | missed_defect | false_blame | cost_s |
|---|---|---|---|---|---|---|---|---|
| bisect | 8 | 0.375 | 0.375 | 0.003 | 0.000 | 0.625 | 0.000 | 3.32 |
| bugdoc_shortcut | 8 | 0.375 | 0.375 | 0.003 | 0.000 | 0.625 | 0.000 | 9.40 |
| full_rollback | 8 | 0.375 | 0.375 | 0.003 | 0.000 | 0.625 | 0.000 | 1.59 |
| observational_attribution | 8 | 0.250 | 0.625 | 0.003 | 0.000 | 0.625 | 0.625 | 0.00 |
| retrain_on_alarm | 8 | 0.375 | 0.375 | 0.003 | 0.000 | 0.625 | 0.000 | 0.00 |
| validation_first | 8 | 0.375 | 0.625 | 0.003 | 0.000 | 0.625 | 0.000 | 0.00 |
| dod | 8 | 0.625 | 0.250 | 0.003 | 0.000 | 0.375 | 0.000 | 21.33 |
| dod_no_boundary | 8 | 0.500 | 0.250 | 0.002 | 0.125 | 0.375 | 0.125 | 5.79 |
| dod_no_prior | 8 | 0.625 | 0.250 | 0.003 | 0.000 | 0.375 | 0.000 | 20.29 |
| dod_uniform_cost | 8 | 0.625 | 0.250 | 0.003 | 0.000 | 0.375 | 0.000 | 20.53 |

### Tier T3

| method | n | correct | type_correct | regret | unnecessary_retrain | missed_defect | false_blame | cost_s |
|---|---|---|---|---|---|---|---|---|
| bisect | 20 | 0.500 | 0.500 | 0.002 | 0.100 | 0.400 | 0.000 | 2.81 |
| bugdoc_shortcut | 20 | 0.500 | 0.500 | 0.002 | 0.100 | 0.400 | 0.000 | 11.13 |
| full_rollback | 20 | 0.500 | 0.500 | 0.002 | 0.100 | 0.400 | 0.000 | 1.09 |
| observational_attribution | 20 | 0.100 | 0.300 | 0.013 | 0.000 | 0.400 | 0.800 | 0.00 |
| retrain_on_alarm | 20 | 0.500 | 0.500 | 0.002 | 0.100 | 0.400 | 0.000 | 0.00 |
| validation_first | 20 | 0.450 | 0.400 | 0.003 | 0.100 | 0.400 | 0.000 | 0.00 |
| dod | 20 | 0.650 | 0.550 | 0.002 | 0.100 | 0.250 | 0.000 | 34.08 |
| dod_no_boundary | 20 | 0.250 | 0.300 | 0.002 | 0.200 | 0.250 | 0.600 | 6.03 |
| dod_no_prior | 20 | 0.650 | 0.550 | 0.002 | 0.100 | 0.250 | 0.000 | 31.88 |
| dod_uniform_cost | 20 | 0.650 | 0.550 | 0.002 | 0.100 | 0.250 | 0.000 | 32.15 |

### Tier none

| method | n | correct | type_correct | regret | unnecessary_retrain | missed_defect | false_blame | cost_s |
|---|---|---|---|---|---|---|---|---|
| bisect | 14 | 1.000 | 1.000 | 0.001 | 0.000 | 0.000 | 0.000 | 2.50 |
| bugdoc_shortcut | 14 | 1.000 | 1.000 | 0.001 | 0.000 | 0.000 | 0.000 | 10.85 |
| full_rollback | 14 | 1.000 | 1.000 | 0.001 | 0.000 | 0.000 | 0.000 | 0.71 |
| observational_attribution | 14 | 0.286 | 0.286 | 0.010 | 0.000 | 0.000 | 0.714 | 0.00 |
| retrain_on_alarm | 14 | 1.000 | 1.000 | 0.001 | 0.000 | 0.000 | 0.000 | 0.00 |
| validation_first | 14 | 0.857 | 0.857 | 0.002 | 0.000 | 0.000 | 0.143 | 0.00 |
| dod | 14 | 1.000 | 1.000 | 0.001 | 0.000 | 0.000 | 0.000 | 27.75 |
| dod_no_boundary | 14 | 0.429 | 0.429 | 0.000 | 0.143 | 0.000 | 0.571 | 3.25 |
| dod_no_prior | 14 | 1.000 | 1.000 | 0.001 | 0.000 | 0.000 | 0.000 | 24.75 |
| dod_uniform_cost | 14 | 1.000 | 1.000 | 0.001 | 0.000 | 0.000 | 0.000 | 24.90 |

### Domain acs

| method | n | correct | type_correct | regret | unnecessary_retrain | missed_defect | false_blame | cost_s |
|---|---|---|---|---|---|---|---|---|
| bisect | 100 | 0.640 | 0.640 | 0.002 | 0.120 | 0.270 | 0.000 | 2.71 |
| bugdoc_shortcut | 100 | 0.640 | 0.640 | 0.002 | 0.120 | 0.270 | 0.000 | 13.19 |
| full_rollback | 100 | 0.640 | 0.640 | 0.002 | 0.120 | 0.270 | 0.000 | 0.95 |
| observational_attribution | 100 | 0.170 | 0.210 | 0.014 | 0.000 | 0.150 | 0.680 | 0.00 |
| retrain_on_alarm | 100 | 0.640 | 0.640 | 0.002 | 0.120 | 0.270 | 0.000 | 0.00 |
| validation_first | 100 | 0.490 | 0.380 | 0.009 | 0.060 | 0.150 | 0.060 | 0.00 |
| dod | 100 | 0.630 | 0.520 | 0.008 | 0.070 | 0.100 | 0.000 | 50.45 |
| dod_no_boundary | 100 | 0.350 | 0.300 | 0.001 | 0.240 | 0.100 | 0.500 | 5.52 |
| dod_no_prior | 100 | 0.630 | 0.520 | 0.008 | 0.070 | 0.100 | 0.000 | 42.61 |
| dod_uniform_cost | 100 | 0.630 | 0.520 | 0.008 | 0.070 | 0.100 | 0.000 | 42.85 |

### 95% cluster-bootstrap CI of 'correct' (clusters = domain x tier x scenario)

- bisect: 0.640 [0.512, 0.818]
- bugdoc_shortcut: 0.640 [0.512, 0.818]
- full_rollback: 0.640 [0.512, 0.818]
- observational_attribution: 0.170 [0.127, 0.240]
- retrain_on_alarm: 0.640 [0.512, 0.818]
- validation_first: 0.490 [0.400, 0.621]
- dod: 0.630 [0.547, 0.750]
- dod_no_boundary: 0.350 [0.305, 0.411]
- dod_no_prior: 0.630 [0.547, 0.750]
- dod_uniform_cost: 0.630 [0.547, 0.750]

### Case composition

- ('acs', 'fix', 'loud'): 10
- ('acs', 'fix', 'silent'): 7
- ('acs', 'fix+retrain', 'loud'): 8
- ('acs', 'fix+retrain', 'silent'): 2
- ('acs', 'nothing', '-'): 37
- ('acs', 'retrain', '-'): 36
