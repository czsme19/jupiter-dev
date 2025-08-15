import pandas as pd


def vectorized_mask(f, name_cols, q):
    return f[name_cols].apply(lambda s: s.str.contains(q, case=False, na=False)).any(axis=1)


def loop_mask(f, name_cols, q):
    mask = False
    for c in name_cols:
        mask = mask | f[c].str.contains(q, case=False, na=False)
    return mask


def test_vectorized_mask_matches_loop():
    f = pd.DataFrame({
        "stop_name": ["Alpha", "Beta", "Gamma", None],
        "fullName": ["Alpha Station", "Beta Stop", None, "Delta"],
    })
    name_cols = ["stop_name", "fullName"]
    q = "alpha"

    assert vectorized_mask(f, name_cols, q).equals(loop_mask(f, name_cols, q))


def test_case_insensitivity_and_na_handling():
    f = pd.DataFrame({
        "stop_name": ["ALPHA", None],
        "fullName": [None, "alpha"],
    })
    name_cols = ["stop_name", "fullName"]
    q = "alpha"

    expected = pd.Series([True, True])
    result = vectorized_mask(f, name_cols, q)
    assert result.equals(expected)
