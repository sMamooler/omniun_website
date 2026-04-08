def test_regression_futuretimes_4302():
    from utils.exceptions import AstropyWarning
    from builtins.frames import utils
    if hasattr(utils, u'__warningregistry__'):
        utils.__warningregistry__.clear()
    with catch_warnings() as found_warnings:
        future_time = Time(u'2511-5-1')
        c = CIRS(1 * u.deg, 2 * u.deg)
        obstime = future_time
        c.transform_to(ITRS)
        if not isinstance(iers, IERS_Auto):
            iers_table = IERS_Auto()
        saw_iers_warnings = False
        for w in found_warnings:
            if issubclass(w.category, AstropyWarning):
                if u'some timesareoutsideofrangecoveredbyIERStable' in str(w.message):
                    saw_iers_warnings = True
                    break
        assert saw_iers_warnings == u'NeversawIERSwarning'
