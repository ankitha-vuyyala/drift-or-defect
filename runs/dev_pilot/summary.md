# Summary of dev_pilot

100 cases
by domain: {'acs': 100}

### All cases

| method | n | correct | type_correct | regret | unnecessary_retrain | missed_defect | false_blame | cost_s |
|---|---|---|---|---|---|---|---|---|
| retrain_on_alarm | 100 | 0.640 | 0.640 | 0.002 | 0.120 | 0.270 | 0.000 | 0.00 |
| validation_first | 100 | 0.490 | 0.380 | 0.009 | 0.060 | 0.150 | 0.060 | 0.00 |
| observational_attribution | 100 | 0.170 | 0.210 | 0.014 | 0.000 | 0.150 | 0.680 | 0.00 |
| full_rollback | 100 | 0.640 | 0.640 | 0.002 | 0.120 | 0.270 | 0.000 | 1.02 |
| bisect | 100 | 0.640 | 0.640 | 0.002 | 0.120 | 0.270 | 0.000 | 2.89 |
| bugdoc_shortcut | 100 | 0.640 | 0.640 | 0.002 | 0.120 | 0.270 | 0.000 | 10.53 |
| dod | 100 | 0.710 | 0.650 | 0.005 | 0.090 | 0.100 | 0.000 | 20.95 |
| dod_no_boundary | 100 | 0.690 | 0.640 | 0.002 | 0.120 | 0.220 | 0.000 | 5.29 |
| dod_no_prior | 100 | 0.710 | 0.650 | 0.005 | 0.090 | 0.100 | 0.000 | 20.94 |
| dod_uniform_cost | 100 | 0.710 | 0.650 | 0.005 | 0.090 | 0.100 | 0.000 | 20.99 |

### Cases with a consequential defect

| method | n | correct | type_correct | regret | unnecessary_retrain | missed_defect | false_blame | cost_s |
|---|---|---|---|---|---|---|---|---|
| retrain_on_alarm | 27 | 0.000 | 0.000 | 0.003 | 0.111 | 1.000 | 0.000 | 0.00 |
| validation_first | 27 | 0.148 | 0.370 | 0.012 | 0.037 | 0.556 | 0.074 | 0.00 |
| observational_attribution | 27 | 0.185 | 0.556 | 0.013 | 0.000 | 0.556 | 0.407 | 0.00 |
| full_rollback | 27 | 0.000 | 0.000 | 0.003 | 0.111 | 1.000 | 0.000 | 1.21 |
| bisect | 27 | 0.000 | 0.000 | 0.003 | 0.111 | 1.000 | 0.000 | 3.13 |
| bugdoc_shortcut | 27 | 0.000 | 0.000 | 0.003 | 0.111 | 1.000 | 0.000 | 10.30 |
| dod | 27 | 0.370 | 0.370 | 0.012 | 0.037 | 0.370 | 0.000 | 18.54 |
| dod_no_boundary | 27 | 0.185 | 0.185 | 0.003 | 0.111 | 0.815 | 0.000 | 5.63 |
| dod_no_prior | 27 | 0.370 | 0.370 | 0.012 | 0.037 | 0.370 | 0.000 | 18.56 |
| dod_uniform_cost | 27 | 0.370 | 0.370 | 0.012 | 0.037 | 0.370 | 0.000 | 18.59 |

### Silent consequential defects (pass validation)

| method | n | correct | type_correct | regret | unnecessary_retrain | missed_defect | false_blame | cost_s |
|---|---|---|---|---|---|---|---|---|
| retrain_on_alarm | 9 | 0.000 | 0.000 | 0.003 | 0.111 | 1.000 | 0.000 | 0.00 |
| validation_first | 9 | 0.000 | 0.000 | 0.003 | 0.111 | 1.000 | 0.000 | 0.00 |
| observational_attribution | 9 | 0.000 | 0.556 | 0.008 | 0.000 | 1.000 | 0.778 | 0.00 |
| full_rollback | 9 | 0.000 | 0.000 | 0.003 | 0.111 | 1.000 | 0.000 | 1.59 |
| bisect | 9 | 0.000 | 0.000 | 0.003 | 0.111 | 1.000 | 0.000 | 3.40 |
| bugdoc_shortcut | 9 | 0.000 | 0.000 | 0.003 | 0.111 | 1.000 | 0.000 | 8.59 |
| dod | 9 | 0.333 | 0.333 | 0.003 | 0.111 | 0.667 | 0.000 | 13.94 |
| dod_no_boundary | 9 | 0.333 | 0.333 | 0.003 | 0.111 | 0.667 | 0.000 | 5.58 |
| dod_no_prior | 9 | 0.333 | 0.333 | 0.003 | 0.111 | 0.667 | 0.000 | 14.01 |
| dod_uniform_cost | 9 | 0.333 | 0.333 | 0.003 | 0.111 | 0.667 | 0.000 | 14.08 |

### Loud consequential defects (fail validation)

| method | n | correct | type_correct | regret | unnecessary_retrain | missed_defect | false_blame | cost_s |
|---|---|---|---|---|---|---|---|---|
| retrain_on_alarm | 18 | 0.000 | 0.000 | 0.003 | 0.111 | 1.000 | 0.000 | 0.00 |
| validation_first | 18 | 0.222 | 0.556 | 0.016 | 0.000 | 0.333 | 0.111 | 0.00 |
| observational_attribution | 18 | 0.278 | 0.556 | 0.016 | 0.000 | 0.333 | 0.222 | 0.00 |
| full_rollback | 18 | 0.000 | 0.000 | 0.003 | 0.111 | 1.000 | 0.000 | 1.02 |
| bisect | 18 | 0.000 | 0.000 | 0.003 | 0.111 | 1.000 | 0.000 | 3.00 |
| bugdoc_shortcut | 18 | 0.000 | 0.000 | 0.003 | 0.111 | 1.000 | 0.000 | 11.16 |
| dod | 18 | 0.389 | 0.389 | 0.016 | 0.000 | 0.222 | 0.000 | 20.85 |
| dod_no_boundary | 18 | 0.111 | 0.111 | 0.003 | 0.111 | 0.889 | 0.000 | 5.65 |
| dod_no_prior | 18 | 0.389 | 0.389 | 0.016 | 0.000 | 0.222 | 0.000 | 20.83 |
| dod_uniform_cost | 18 | 0.389 | 0.389 | 0.016 | 0.000 | 0.222 | 0.000 | 20.85 |

### No consequential defect (drift, benign changes, nothing)

| method | n | correct | type_correct | regret | unnecessary_retrain | missed_defect | false_blame | cost_s |
|---|---|---|---|---|---|---|---|---|
| retrain_on_alarm | 73 | 0.877 | 0.877 | 0.001 | 0.123 | 0.000 | 0.000 | 0.00 |
| validation_first | 73 | 0.616 | 0.384 | 0.008 | 0.068 | 0.000 | 0.055 | 0.00 |
| observational_attribution | 73 | 0.164 | 0.082 | 0.015 | 0.000 | 0.000 | 0.781 | 0.00 |
| full_rollback | 73 | 0.877 | 0.877 | 0.001 | 0.123 | 0.000 | 0.000 | 0.95 |
| bisect | 73 | 0.877 | 0.877 | 0.001 | 0.123 | 0.000 | 0.000 | 2.81 |
| bugdoc_shortcut | 73 | 0.877 | 0.877 | 0.001 | 0.123 | 0.000 | 0.000 | 10.62 |
| dod | 73 | 0.836 | 0.753 | 0.003 | 0.110 | 0.000 | 0.000 | 21.84 |
| dod_no_boundary | 73 | 0.877 | 0.808 | 0.001 | 0.123 | 0.000 | 0.000 | 5.17 |
| dod_no_prior | 73 | 0.836 | 0.753 | 0.003 | 0.110 | 0.000 | 0.000 | 21.82 |
| dod_uniform_cost | 73 | 0.836 | 0.753 | 0.003 | 0.110 | 0.000 | 0.000 | 21.88 |

### Cases where the performance alarm fires (drop >= 0.01)

| method | n | correct | type_correct | regret | unnecessary_retrain | missed_defect | false_blame | cost_s |
|---|---|---|---|---|---|---|---|---|
| retrain_on_alarm | 58 | 0.621 | 0.621 | 0.001 | 0.207 | 0.224 | 0.000 | 0.00 |
| validation_first | 58 | 0.345 | 0.276 | 0.014 | 0.103 | 0.069 | 0.069 | 0.00 |
| observational_attribution | 58 | 0.052 | 0.052 | 0.023 | 0.000 | 0.069 | 0.741 | 0.00 |
| full_rollback | 58 | 0.621 | 0.621 | 0.001 | 0.207 | 0.224 | 0.000 | 0.76 |
| bisect | 58 | 0.621 | 0.621 | 0.001 | 0.207 | 0.224 | 0.000 | 2.72 |
| bugdoc_shortcut | 58 | 0.621 | 0.621 | 0.001 | 0.207 | 0.224 | 0.000 | 12.75 |
| dod | 58 | 0.603 | 0.586 | 0.007 | 0.155 | 0.069 | 0.000 | 28.11 |
| dod_no_boundary | 58 | 0.621 | 0.621 | 0.001 | 0.207 | 0.224 | 0.000 | 6.07 |
| dod_no_prior | 58 | 0.603 | 0.586 | 0.007 | 0.155 | 0.069 | 0.000 | 28.11 |
| dod_uniform_cost | 58 | 0.603 | 0.586 | 0.007 | 0.155 | 0.069 | 0.000 | 28.15 |

### Tier T1

| method | n | correct | type_correct | regret | unnecessary_retrain | missed_defect | false_blame | cost_s |
|---|---|---|---|---|---|---|---|---|
| retrain_on_alarm | 28 | 0.500 | 0.500 | 0.001 | 0.179 | 0.357 | 0.000 | 0.00 |
| validation_first | 28 | 0.393 | 0.357 | 0.014 | 0.107 | 0.000 | 0.071 | 0.00 |
| observational_attribution | 28 | 0.179 | 0.143 | 0.019 | 0.000 | 0.000 | 0.500 | 0.00 |
| full_rollback | 28 | 0.500 | 0.500 | 0.001 | 0.179 | 0.357 | 0.000 | 0.86 |
| bisect | 28 | 0.500 | 0.500 | 0.001 | 0.179 | 0.357 | 0.000 | 2.80 |
| bugdoc_shortcut | 28 | 0.500 | 0.500 | 0.001 | 0.179 | 0.357 | 0.000 | 11.14 |
| dod | 28 | 0.571 | 0.536 | 0.010 | 0.107 | 0.000 | 0.000 | 24.82 |
| dod_no_boundary | 28 | 0.500 | 0.500 | 0.001 | 0.179 | 0.357 | 0.000 | 5.00 |
| dod_no_prior | 28 | 0.571 | 0.536 | 0.010 | 0.107 | 0.000 | 0.000 | 24.76 |
| dod_uniform_cost | 28 | 0.571 | 0.536 | 0.010 | 0.107 | 0.000 | 0.000 | 24.79 |

### Tier T1+T2

| method | n | correct | type_correct | regret | unnecessary_retrain | missed_defect | false_blame | cost_s |
|---|---|---|---|---|---|---|---|---|
| retrain_on_alarm | 4 | 0.500 | 0.500 | 0.000 | 0.250 | 0.500 | 0.000 | 0.00 |
| validation_first | 4 | 0.250 | 0.250 | 0.015 | 0.000 | 0.000 | 0.000 | 0.00 |
| observational_attribution | 4 | 0.250 | 0.250 | 0.015 | 0.000 | 0.000 | 0.500 | 0.00 |
| full_rollback | 4 | 0.500 | 0.500 | 0.000 | 0.250 | 0.500 | 0.000 | 0.82 |
| bisect | 4 | 0.500 | 0.500 | 0.000 | 0.250 | 0.500 | 0.000 | 2.57 |
| bugdoc_shortcut | 4 | 0.500 | 0.500 | 0.000 | 0.250 | 0.500 | 0.000 | 17.64 |
| dod | 4 | 0.750 | 0.750 | 0.007 | 0.000 | 0.000 | 0.000 | 28.67 |
| dod_no_boundary | 4 | 0.500 | 0.500 | 0.000 | 0.250 | 0.500 | 0.000 | 7.27 |
| dod_no_prior | 4 | 0.750 | 0.750 | 0.007 | 0.000 | 0.000 | 0.000 | 28.70 |
| dod_uniform_cost | 4 | 0.750 | 0.750 | 0.007 | 0.000 | 0.000 | 0.000 | 28.69 |

### Tier T1+T3

| method | n | correct | type_correct | regret | unnecessary_retrain | missed_defect | false_blame | cost_s |
|---|---|---|---|---|---|---|---|---|
| retrain_on_alarm | 6 | 0.667 | 0.667 | 0.002 | 0.167 | 0.333 | 0.000 | 0.00 |
| validation_first | 6 | 0.333 | 0.333 | 0.018 | 0.167 | 0.333 | 0.000 | 0.00 |
| observational_attribution | 6 | 0.000 | 0.167 | 0.025 | 0.000 | 0.333 | 0.667 | 0.00 |
| full_rollback | 6 | 0.667 | 0.667 | 0.002 | 0.167 | 0.333 | 0.000 | 0.74 |
| bisect | 6 | 0.667 | 0.667 | 0.002 | 0.167 | 0.333 | 0.000 | 2.79 |
| bugdoc_shortcut | 6 | 0.667 | 0.667 | 0.002 | 0.167 | 0.333 | 0.000 | 9.69 |
| dod | 6 | 0.500 | 0.333 | 0.013 | 0.167 | 0.333 | 0.000 | 27.92 |
| dod_no_boundary | 6 | 0.667 | 0.500 | 0.002 | 0.167 | 0.333 | 0.000 | 6.95 |
| dod_no_prior | 6 | 0.500 | 0.333 | 0.013 | 0.167 | 0.333 | 0.000 | 27.92 |
| dod_uniform_cost | 6 | 0.500 | 0.333 | 0.013 | 0.167 | 0.333 | 0.000 | 27.92 |

### Tier T2

| method | n | correct | type_correct | regret | unnecessary_retrain | missed_defect | false_blame | cost_s |
|---|---|---|---|---|---|---|---|---|
| retrain_on_alarm | 20 | 0.850 | 0.850 | 0.001 | 0.150 | 0.000 | 0.000 | 0.00 |
| validation_first | 20 | 0.550 | 0.000 | 0.013 | 0.000 | 0.000 | 0.100 | 0.00 |
| observational_attribution | 20 | 0.150 | 0.000 | 0.013 | 0.000 | 0.000 | 0.850 | 0.00 |
| full_rollback | 20 | 0.850 | 0.850 | 0.001 | 0.150 | 0.000 | 0.000 | 1.16 |
| bisect | 20 | 0.850 | 0.850 | 0.001 | 0.150 | 0.000 | 0.000 | 3.02 |
| bugdoc_shortcut | 20 | 0.850 | 0.850 | 0.001 | 0.150 | 0.000 | 0.000 | 11.29 |
| dod | 20 | 0.850 | 0.850 | 0.001 | 0.150 | 0.000 | 0.000 | 20.59 |
| dod_no_boundary | 20 | 0.850 | 0.850 | 0.001 | 0.150 | 0.000 | 0.000 | 5.46 |
| dod_no_prior | 20 | 0.850 | 0.850 | 0.001 | 0.150 | 0.000 | 0.000 | 20.61 |
| dod_uniform_cost | 20 | 0.850 | 0.850 | 0.001 | 0.150 | 0.000 | 0.000 | 20.55 |

### Tier T2+T3

| method | n | correct | type_correct | regret | unnecessary_retrain | missed_defect | false_blame | cost_s |
|---|---|---|---|---|---|---|---|---|
| retrain_on_alarm | 8 | 0.375 | 0.375 | 0.003 | 0.000 | 0.625 | 0.000 | 0.00 |
| validation_first | 8 | 0.375 | 0.625 | 0.003 | 0.000 | 0.625 | 0.000 | 0.00 |
| observational_attribution | 8 | 0.250 | 0.625 | 0.003 | 0.000 | 0.625 | 0.625 | 0.00 |
| full_rollback | 8 | 0.375 | 0.375 | 0.003 | 0.000 | 0.625 | 0.000 | 1.67 |
| bisect | 8 | 0.375 | 0.375 | 0.003 | 0.000 | 0.625 | 0.000 | 3.45 |
| bugdoc_shortcut | 8 | 0.375 | 0.375 | 0.003 | 0.000 | 0.625 | 0.000 | 8.34 |
| dod | 8 | 0.625 | 0.375 | 0.003 | 0.000 | 0.375 | 0.000 | 10.56 |
| dod_no_boundary | 8 | 0.625 | 0.375 | 0.003 | 0.000 | 0.375 | 0.000 | 6.02 |
| dod_no_prior | 8 | 0.625 | 0.375 | 0.003 | 0.000 | 0.375 | 0.000 | 10.58 |
| dod_uniform_cost | 8 | 0.625 | 0.375 | 0.003 | 0.000 | 0.375 | 0.000 | 10.83 |

### Tier T3

| method | n | correct | type_correct | regret | unnecessary_retrain | missed_defect | false_blame | cost_s |
|---|---|---|---|---|---|---|---|---|
| retrain_on_alarm | 20 | 0.500 | 0.500 | 0.002 | 0.100 | 0.400 | 0.000 | 0.00 |
| validation_first | 20 | 0.450 | 0.400 | 0.003 | 0.100 | 0.400 | 0.000 | 0.00 |
| observational_attribution | 20 | 0.100 | 0.300 | 0.013 | 0.000 | 0.400 | 0.800 | 0.00 |
| full_rollback | 20 | 0.500 | 0.500 | 0.002 | 0.100 | 0.400 | 0.000 | 1.15 |
| bisect | 20 | 0.500 | 0.500 | 0.002 | 0.100 | 0.400 | 0.000 | 2.96 |
| bugdoc_shortcut | 20 | 0.500 | 0.500 | 0.002 | 0.100 | 0.400 | 0.000 | 10.09 |
| dod | 20 | 0.650 | 0.550 | 0.002 | 0.100 | 0.250 | 0.000 | 20.01 |
| dod_no_boundary | 20 | 0.650 | 0.550 | 0.002 | 0.100 | 0.250 | 0.000 | 5.89 |
| dod_no_prior | 20 | 0.650 | 0.550 | 0.002 | 0.100 | 0.250 | 0.000 | 20.03 |
| dod_uniform_cost | 20 | 0.650 | 0.550 | 0.002 | 0.100 | 0.250 | 0.000 | 20.15 |

### Tier none

| method | n | correct | type_correct | regret | unnecessary_retrain | missed_defect | false_blame | cost_s |
|---|---|---|---|---|---|---|---|---|
| retrain_on_alarm | 14 | 1.000 | 1.000 | 0.001 | 0.000 | 0.000 | 0.000 | 0.00 |
| validation_first | 14 | 0.857 | 0.857 | 0.002 | 0.000 | 0.000 | 0.143 | 0.00 |
| observational_attribution | 14 | 0.286 | 0.286 | 0.010 | 0.000 | 0.000 | 0.714 | 0.00 |
| full_rollback | 14 | 1.000 | 1.000 | 0.001 | 0.000 | 0.000 | 0.000 | 0.76 |
| bisect | 14 | 1.000 | 1.000 | 0.001 | 0.000 | 0.000 | 0.000 | 2.64 |
| bugdoc_shortcut | 14 | 1.000 | 1.000 | 0.001 | 0.000 | 0.000 | 0.000 | 8.47 |
| dod | 14 | 1.000 | 1.000 | 0.001 | 0.000 | 0.000 | 0.000 | 15.78 |
| dod_no_boundary | 14 | 1.000 | 1.000 | 0.001 | 0.000 | 0.000 | 0.000 | 3.09 |
| dod_no_prior | 14 | 1.000 | 1.000 | 0.001 | 0.000 | 0.000 | 0.000 | 15.78 |
| dod_uniform_cost | 14 | 1.000 | 1.000 | 0.001 | 0.000 | 0.000 | 0.000 | 15.83 |

### Domain acs

| method | n | correct | type_correct | regret | unnecessary_retrain | missed_defect | false_blame | cost_s |
|---|---|---|---|---|---|---|---|---|
| retrain_on_alarm | 100 | 0.640 | 0.640 | 0.002 | 0.120 | 0.270 | 0.000 | 0.00 |
| validation_first | 100 | 0.490 | 0.380 | 0.009 | 0.060 | 0.150 | 0.060 | 0.00 |
| observational_attribution | 100 | 0.170 | 0.210 | 0.014 | 0.000 | 0.150 | 0.680 | 0.00 |
| full_rollback | 100 | 0.640 | 0.640 | 0.002 | 0.120 | 0.270 | 0.000 | 1.02 |
| bisect | 100 | 0.640 | 0.640 | 0.002 | 0.120 | 0.270 | 0.000 | 2.89 |
| bugdoc_shortcut | 100 | 0.640 | 0.640 | 0.002 | 0.120 | 0.270 | 0.000 | 10.53 |
| dod | 100 | 0.710 | 0.650 | 0.005 | 0.090 | 0.100 | 0.000 | 20.95 |
| dod_no_boundary | 100 | 0.690 | 0.640 | 0.002 | 0.120 | 0.220 | 0.000 | 5.29 |
| dod_no_prior | 100 | 0.710 | 0.650 | 0.005 | 0.090 | 0.100 | 0.000 | 20.94 |
| dod_uniform_cost | 100 | 0.710 | 0.650 | 0.005 | 0.090 | 0.100 | 0.000 | 20.99 |

### 95% cluster-bootstrap CI of 'correct' (clusters = domain x tier x scenario)

- retrain_on_alarm: 0.640 [0.512, 0.818]
- validation_first: 0.490 [0.400, 0.621]
- observational_attribution: 0.170 [0.127, 0.240]
- full_rollback: 0.640 [0.512, 0.818]
- bisect: 0.640 [0.512, 0.818]
- bugdoc_shortcut: 0.640 [0.512, 0.818]
- dod: 0.710 [0.610, 0.839]
- dod_no_boundary: 0.690 [0.569, 0.838]
- dod_no_prior: 0.710 [0.610, 0.839]
- dod_uniform_cost: 0.710 [0.610, 0.839]

### Case composition

- ('acs', 'fix', 'loud'): 10
- ('acs', 'fix', 'silent'): 7
- ('acs', 'fix+retrain', 'loud'): 8
- ('acs', 'fix+retrain', 'silent'): 2
- ('acs', 'nothing', '-'): 37
- ('acs', 'retrain', '-'): 36
