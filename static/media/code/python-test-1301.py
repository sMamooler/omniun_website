import pytest

def test_many_rows(parallel):
    text = 'ABC\n'
    for i in range(500):
        text += ''.join([str(j) for j in range(3)]) + '\n'
    table = read_basic(text, parallel=parallel)
    expected = [
        [0] * 500,
        [1] * 500,
        [2] * 500
    ]
    assert_table_equal(table, expected)
