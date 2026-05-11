from nlda.parsing import extract_code


def test_extract_python_fence():
    text = "Sure!\n```python\nresult = 1\n```\nDone."
    assert extract_code(text) == "result = 1"


def test_extract_plain_fence():
    text = "```\nresult = 2\n```"
    assert extract_code(text) == "result = 2"


def test_extract_no_fence_returns_text():
    assert extract_code("result = 3") == "result = 3"
