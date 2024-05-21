# -*- coding: utf-8 -*-
from iconclass import *

### These tests are failing with the latest version, need to be updated

# https://nose.readthedocs.org/en/latest/usage.html

test_notations = ["0", "1", "25FF"]


def test_bogosity():
    x = get(
        "41D211(CHEMISE À LA REINE)(+1)"
    )  # The unicode part of this notation was causing problems with the keys
    assert x is not None


def test_keywords():
    x = get("0")
    assert x["kw"]["en"] == ["abstract art", "art", "non-representational art"]
    x = get("31AA25")
    assert x["kw"]["de"] == ["Arm", "Geste", "Haltung", "Hand"]


def test_keys():
    x = get("11(+1)")
    assert x["txt"]["en"] == "Christian religion (+ Holy Trinity)"
    assert x["c"] == ["11(+11)", "11(+12)", "11(+13)"]
    # handle a bogus key gracefully...
    x = get("25FF1(+8)")
    assert x is None


def test_withnames():
    o = get("11H(FOO)")
    assert o["txt"]["en"] == "male saints (FOO)"
    assert (
        get("11H(FOO)0")["txt"]["en"]
        == "male saints (FOO) - male saint represented in a group"
    )


def test_basic():
    results = get_list(test_notations)
    assert len(list(filter(None, results))) == len(test_notations)

    assert results[1]["n"] == "1"
    assert results[1]["p"] == ["1"]
    assert results[2]["p"] == ["2", "25", "25F", "25FF"]
    assert results[0]["txt"]["de"] == "abstrakte, ungegenständliche Kunst"
    c = [
        "25FF1",
        "25FF2",
        "25FF3",
        "25FF4",
        "25FF5",
        "25FF6",
        "25FF7",
        "25FF8",
        "25FF9",
        "25FF(+0)",
        "25FF(+1)",
        "25FF(+2)",
        "25FF(+3)",
        "25FF(+4)",
        "25FF(+5)",
        "25FF(+6)",
        "25FF(+7)",
    ]
    assert results[2]["c"] == c


def test_spaces():
    assert add_space("11H1") == "11 H 1"
    assert add_space("25F(+0)") == "25 F (+0)"
    assert add_space("25F1(+123)") == "25 F 1 (+12 3)"
    assert add_space("1") == "1"
    assert add_space("11") == "11"
    assert add_space("11H") == "11 H"
    assert add_space("11H(...)") == "11 H (...)"
    assert add_space("11H(JOHN)") == "11 H (JOHN)"
    assert add_space("25FF") == "25 FF"
    assert add_space("25F(+123)") == "25 F (+12 3)"
    assert add_space("11H(JOHN)(+12345)") == "11 H (JOHN) (+12 34 5)"
    assert add_space("7(+5)") == "7 (+5)"
    assert add_space("31AA") == "31 AA"
    assert add_space("31AA2(+0)") == "31 AA 2 (+0)"
    assert add_space("31AA25(+0)") == "31 AA 25 (+0)"
    assert add_space("11HH") == "11 HH"
    assert add_space("11HH(AGNES)") == "11 HH (AGNES)"
    assert add_space("11HH(AGNES)(+1)") == "11 HH (AGNES) (+1)"
    assert add_space("11HH(AGNES)3(+1)") == "11 HH (AGNES) 3 (+1)"
    assert add_space("11HH(AGNES)31(+31)") == "11 HH (AGNES) 31 (+31)"
    assert add_space("43C1(+411)") == "43 C 1 (+41 1)"
    assert add_space("43C78611(+3111)") == "43 C 78 61 1 (+31 11)"
    assert add_space("61B2(...)2(+5)") == "61 B 2 (...) 2 (+5)"
    assert add_space("34(+91)") == "34 (+91)"
    assert add_space("83(BOCCACCIO, Decamerone)") == "83 (BOCCACCIO, Decamerone)"
    assert add_space("11H(ALOYSIUS GONZAGA)") == "11 H (ALOYSIUS GONZAGA)"


if __name__ == "__main__":
    test_bogosity()
    test_commented_lines()
    test_keywords()
    test_keys()
    test_withnames()
    test_basic()
    test_spaces()
