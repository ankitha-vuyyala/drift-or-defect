"""Pipeline idioms whose behaviour may differ across pandas versions. Run under each environment; the outputs
are compared by code/t2/setup_envs.py. Only behaviours that differ in practice are used as T2 defects.

usage: <env python> code/t2/probe_snippets.py OUT.json
"""
import json
import sys
import warnings

import numpy as np
import pandas as pd

warnings.simplefilter("ignore")
R = {"pandas": pd.__version__, "numpy": np.__version__}


def rec(name, fn):
    try:
        R[name] = repr(fn())[:600]
    except Exception as e:
        R[name] = f"EXCEPTION {type(e).__name__}: {str(e)[:300]}"


def chained_assignment():
    df = pd.DataFrame({"a": [1.0, 7.0, 9.0], "b": ["x", "y", "z"]})
    df["a"][df["a"] > 5] = 5.0
    return df["a"].tolist()


def chained_assignment_loc_copy():
    df = pd.DataFrame({"a": [1.0, 7.0, 9.0]})
    sub = df[df["a"] > 0]
    sub["a"] = 0.0
    return df["a"].tolist()


def select_object_after_parquet():
    import io
    buf = io.BytesIO()
    pd.DataFrame({"s": ["a", "b", None], "n": [1, 2, 3]}).to_parquet(buf)
    df = pd.read_parquet(io.BytesIO(buf.getvalue()))
    return list(df.select_dtypes(include="object").columns), str(df["s"].dtype)


def select_object_from_constructor():
    df = pd.DataFrame({"s": ["a", "b", "c"], "n": [1, 2, 3]})
    return list(df.select_dtypes(include="object").columns)


def to_datetime_dayfirst_inference():
    return [str(x) for x in pd.to_datetime(pd.Series(["13-01-2000", "12-01-2000", "01-02-2000"]))]


def to_datetime_mixed():
    return [str(x) for x in pd.to_datetime(pd.Series(["2000-01-13", "01/12/2000 10:00"]))]


def to_datetime_strings_int64():
    s = pd.to_datetime(pd.Series(["2016-01-01 00:00:00", "2016-01-01 00:10:00"]))
    return str(s.dtype), s.astype("int64").tolist()


def parquet_timestamp_int64():
    import io
    buf = io.BytesIO()
    import pyarrow as pa
    import pyarrow.parquet as pq
    t = pa.table({"t": pa.array([1_451_606_400_000_000, 1_451_607_000_000_000], type=pa.timestamp("us"))})
    pq.write_table(t, buf)
    df = pd.read_parquet(io.BytesIO(buf.getvalue()))
    return str(df["t"].dtype), df["t"].astype("int64").tolist()


def astype_str_missing():
    return pd.Series([1.0, None, 3.0]).astype(str).tolist(), pd.Series(["a", None]).astype(str).tolist()


def groupby_categorical_default():
    df = pd.DataFrame({"g": pd.Categorical(["a", "a", "b"], categories=["a", "b", "c"]), "v": [1, 2, 3]})
    return df.groupby("g")["v"].sum().to_dict()


def groupby_apply_group_column():
    df = pd.DataFrame({"g": ["a", "a", "b"], "v": [1, 2, 3]})
    return df.groupby("g").apply(lambda x: list(x.columns)).to_dict()


def replace_downcast():
    s = pd.Series([1.0, 2.0, 3.0]).replace(2.0, 4)
    return str(s.dtype), pd.Series(["1", "2"], dtype=object).replace({"1": 1, "2": 2}).dtype.name


def value_counts_name():
    return pd.Series(["a", "b", "a"], name="c").value_counts().name


def mean_mixed_frame():
    return pd.DataFrame({"a": [1, 2], "b": ["x", "y"]}).mean().tolist()


def fillna_method():
    return pd.Series([1.0, None, 3.0]).fillna(method="ffill").tolist()


def applymap_exists():
    return pd.DataFrame({"a": [1]}).applymap(lambda x: x + 1).values.tolist()


def concat_empty_dtype():
    a = pd.DataFrame({"x": pd.Series([], dtype="float64")})
    b = pd.DataFrame({"x": [1, 2]})
    return str(pd.concat([a, b])["x"].dtype)


def str_contains_nan():
    return pd.Series(["ab", None, "cd"]).str.contains("a").tolist()


def series_str_len_after_parquet_null():
    return pd.Series(["ab", None]).str.len().tolist()


def where_object_upcast():
    s = pd.Series([1, 2, 3])
    return str(s.where(s > 1, "x").dtype)


def int_with_nan_parquet():
    import io
    buf = io.BytesIO()
    import pyarrow as pa
    import pyarrow.parquet as pq
    pq.write_table(pa.table({"i": pa.array([1, None, 3], type=pa.int64())}), buf)
    return str(pd.read_parquet(io.BytesIO(buf.getvalue()))["i"].dtype)


def isin_str_vs_int():
    return pd.Series(["1", "2"]).isin([1]).tolist()


def factorize_order():
    return pd.factorize(pd.Series(["b", "a", "b", None]))[0].tolist()


def get_dummies_dtype():
    return str(pd.get_dummies(pd.Series(["a", "b"])).dtypes.iloc[0])


def resample_month_alias():
    s = pd.Series(range(3), index=pd.date_range("2020-01-01", periods=3, freq="D"))
    return s.resample("M").sum().tolist()


def sum_bool_object():
    return pd.Series([True, False, None]).sum()


def round_half():
    return pd.Series([0.5, 1.5, 2.5]).round().tolist()


def dt_hour_after_tz_localize():
    s = pd.to_datetime(pd.Series(["2016-03-13 01:30", "2016-03-13 03:30"])).dt.tz_localize("America/New_York")
    return s.dt.hour.tolist()


for name, fn in list(globals().items()):
    if callable(fn) and not name.startswith(("rec", "_")) and fn.__module__ == "__main__" \
            and name not in ("json", "sys"):
        rec(name, fn)

if __name__ == "__main__":
    with open(sys.argv[1], "w", encoding="utf-8") as f:
        json.dump(R, f, indent=1)
    print(json.dumps(R, indent=1))
