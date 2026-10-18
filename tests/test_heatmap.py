import pytest

from app.heatmap import FINGER_OF, LAYOUT, analyze, key_for, shift_key_for


def test_every_layout_key_has_a_finger():
    for row in LAYOUT:
        for key_id, _, _, _ in row:
            assert key_id in FINGER_OF


@pytest.mark.parametrize("char, expected", [
    ("a", ("a", False)),
    ("A", ("a", True)),
    ("!", ("1", True)),
    ("?", ("/", True)),
    (";", (";", False)),
    (" ", ("Space", False)),
    ("\n", ("Enter", False)),
    ("\t", ("Tab", False)),
    ("é", None),
    ("😀", None),
])
def test_key_for(char, expected):
    assert key_for(char) == expected


def test_shift_uses_opposite_hand():
    assert shift_key_for("a") == "ShiftRight"
    assert shift_key_for("p") == "ShiftLeft"


def test_empty_text_returns_zeros():
    result = analyze("")
    assert result["keystrokes"] == 0
    assert result["counts"] == {}
    assert result["top_keys"] == []
    assert result["hands"] == {"left": 0.0, "right": 0.0}
    assert result["home_row"] == 0.0


def test_capital_letter_counts_shift_press():
    result = analyze("Hello")
    assert result["characters"] == 5
    assert result["keystrokes"] == 6
    assert result["shift_presses"] == 1
    assert result["counts"]["ShiftLeft"] == 1
    assert result["counts"]["l"] == 2


def test_intensity_is_relative_to_busiest_key():
    result = analyze("aab")
    assert result["intensity"]["a"] == 1.0
    assert result["intensity"]["b"] == 0.5


def test_space_does_not_wash_out_other_keys():
    result = analyze("a a a b")
    assert result["intensity"]["a"] == 1.0
    assert result["intensity"]["Space"] == 1.0


def test_only_spaces_still_has_intensity():
    assert analyze("   ")["intensity"] == {"Space": 1.0}


def test_top_keys_are_sorted_by_count():
    result = analyze("ccc bb a")
    assert [k["key"] for k in result["top_keys"]][:3] == ["c", "Space", "b"]
    assert result["top_keys"][0] == {"key": "c", "label": "C", "count": 3}


def test_top_keys_capped_at_five():
    assert len(analyze("abcdefgh")["top_keys"]) == 5


def test_hand_split_ignores_space():
    result = analyze("a j")
    assert result["hands"] == {"left": 50.0, "right": 50.0}
    assert result["fingers"]["thumbs"] == 1


def test_home_row_percentage():
    result = analyze("asdq")
    assert result["home_row"] == 75.0


def test_unmapped_characters_are_counted_not_pressed():
    result = analyze("café")
    assert result["unmapped"] == 1
    assert result["keystrokes"] == 3


def test_windows_line_endings_count_once():
    result = analyze("a\r\nb")
    assert result["counts"]["Enter"] == 1
    assert result["characters"] == 3
