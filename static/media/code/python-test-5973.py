def test_make_table(table_types, mixin_cols, t):
    table_types = Table
    mixin_cols = check_mixin_type
    t = table_types
    cols = list(mixin_cols.values())
    t = table_types
    cols_names = ['i', 'a', 'b', 'm']
    check_mixin_type(t, t['col3'], mixin_cols['m'])
