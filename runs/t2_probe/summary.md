# T2 probe: pandas behaviour by environment

| idiom | p15 (pandas 1.5.3) | main (pandas 2.2.3) | p30 (pandas 3.0.6) |
|---|---|---|---|
| **chained_assignment** | [1.0, 5.0, 5.0] | [1.0, 5.0, 5.0] | [1.0, 7.0, 9.0] |
| chained_assignment_loc_copy | [1.0, 7.0, 9.0] | [1.0, 7.0, 9.0] | [1.0, 7.0, 9.0] |
| **select_object_after_parquet** | (['s'], 'object') | (['s'], 'object') | (['s'], 'str') |
| select_object_from_constructor | ['s'] | ['s'] | ['s'] |
| **to_datetime_dayfirst_inference** | ['2000-01-13 00:00:00', '2000-12-01 00:00:00', '2000-01-02 00:00:00'] | ['2000-01-13 00:00:00', '2000-01-12 00:00:00', '2000-02-01 00:00:00'] | ['2000-01-13 00:00:00', '2000-01-12 00:00:00', '2000-02-01 00:00:00'] |
| **to_datetime_mixed** | ['2000-01-13 00:00:00', '2000-01-12 10:00:00'] | EXCEPTION ValueError: time data "01/12/2000 10:00" doesn't match format "%Y-%m-%d", at position 1. You might want to try | EXCEPTION ValueError: time data "01/12/2000 10:00" doesn't match format "%Y-%m-%d". You might want to try:     - passing |
| **to_datetime_strings_int64** | ('datetime64[ns]', [1451606400000000000, 1451607000000000000]) | ('datetime64[ns]', [1451606400000000000, 1451607000000000000]) | ('datetime64[us]', [1451606400000000, 1451607000000000]) |
| **parquet_timestamp_int64** | ('datetime64[ns]', [1451606400000000000, 1451607000000000000]) | ('datetime64[us]', [1451606400000000, 1451607000000000]) | ('datetime64[us]', [1451606400000000, 1451607000000000]) |
| **astype_str_missing** | (['1.0', 'nan', '3.0'], ['a', 'None']) | (['1.0', 'nan', '3.0'], ['a', 'None']) | (['1.0', nan, '3.0'], ['a', nan]) |
| **groupby_categorical_default** | {'a': 3, 'b': 3, 'c': 0} | {'a': 3, 'b': 3, 'c': 0} | {'a': 3, 'b': 3} |
| **groupby_apply_group_column** | {'a': ['g', 'v'], 'b': ['g', 'v']} | {'a': ['g', 'v'], 'b': ['g', 'v']} | {'a': ['v'], 'b': ['v']} |
| **replace_downcast** | ('float64', 'int64') | ('float64', 'int64') | ('float64', 'object') |
| **value_counts_name** | 'c' | 'count' | 'count' |
| **mean_mixed_frame** | [1.5] | EXCEPTION TypeError: Could not convert ['xy'] to numeric | EXCEPTION TypeError: Cannot perform reduction 'mean' with string dtype |
| **fillna_method** | [1.0, 1.0, 3.0] | [1.0, 1.0, 3.0] | EXCEPTION TypeError: NDFrame.fillna() got an unexpected keyword argument 'method' |
| **applymap_exists** | [[2]] | [[2]] | EXCEPTION AttributeError: 'DataFrame' object has no attribute 'applymap' |
| concat_empty_dtype | 'float64' | 'float64' | 'float64' |
| **str_contains_nan** | [True, None, False] | [True, None, False] | [True, False, False] |
| series_str_len_after_parquet_null | [2.0, nan] | [2.0, nan] | [2.0, nan] |
| where_object_upcast | 'object' | 'object' | 'object' |
| int_with_nan_parquet | 'float64' | 'float64' | 'float64' |
| isin_str_vs_int | [False, False] | [False, False] | [False, False] |
| factorize_order | [0, 1, 0, -1] | [0, 1, 0, -1] | [0, 1, 0, -1] |
| **get_dummies_dtype** | 'uint8' | 'bool' | 'bool' |
| **resample_month_alias** | [3] | [3] | EXCEPTION ValueError: Invalid frequency: M. Failed to parse with error message: ValueError("'M' is no longer supported f |
| sum_bool_object | 1 | 1 | 1 |
| round_half | [0.0, 2.0, 2.0] | [0.0, 2.0, 2.0] | [0.0, 2.0, 2.0] |
| dt_hour_after_tz_localize | [1, 3] | [1, 3] | [1, 3] |

Differing idioms: 17 of 28: chained_assignment, select_object_after_parquet, to_datetime_dayfirst_inference, to_datetime_mixed, to_datetime_strings_int64, parquet_timestamp_int64, astype_str_missing, groupby_categorical_default, groupby_apply_group_column, replace_downcast, value_counts_name, mean_mixed_frame, fillna_method, applymap_exists, str_contains_nan, get_dummies_dtype, resample_month_alias
