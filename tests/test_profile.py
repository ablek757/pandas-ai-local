import pandas as pd

from nlda.loaders.profile import profile_dataframe, render_profile_text


def test_profile_shape_and_columns():
    df = pd.DataFrame(
        {"x": [1, 2, 3, None], "y": ["a", "a", "b", "c"]}
    )
    p = profile_dataframe(df)
    assert p["shape"] == {"rows": 4, "cols": 2}
    by_name = {c["name"]: c for c in p["columns"]}
    assert by_name["x"]["nulls"] == 1
    assert by_name["x"]["min"] == 1
    assert by_name["x"]["max"] == 3
    assert by_name["y"]["top_values"][0]["value"] == "a"


def test_render_text_smoke():
    df = pd.DataFrame({"a": [1, 2, 3]})
    text = render_profile_text(profile_dataframe(df))
    assert "shape:" in text
    assert "a" in text
