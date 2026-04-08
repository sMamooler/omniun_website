import os
import functools

def for_dtypes_combination(types, names, full=None):
    if full is None:
        full = int(os.environ.get('CUPY_TEST_FULL_COMBINATION', '0'))
    if full:
        combination = [dict(zip(names, typs)) for typs in product(*types)]
    else:
        ts = []
        for _ in range(len(names)):
            t = list(types)
            random.shuffle(t)
            ts.append(t)
        combination = [dict(zip(names, typs)) for typs in zip(*ts)]
    
    def decorator(impl):
        @functools.wraps(impl)
        def test_func(self, *args, **kw):
            for dtypes in combination:
                kw_copy = kw.copy()
                kw_copy.update(dtypes)
                try:
                    impl(self, *args, **kw_copy)
                except Exception:
                    print(dtypes)
                    raise
        return test_func
    return decorator
