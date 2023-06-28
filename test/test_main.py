import pytest

from coclico import main

def test_compare_test0():

    c1 = "./data/test0/C1/"
    c2 = "./data/test0/C2/"
    ref = "./data/test0/Ref/"

    main.compare(c1, c2, ref)
