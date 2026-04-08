def test_angle_format_roundtripping():
    a1 = Angle(0, unit='radian')
    a2 = Angle(10, unit='degree')
    a3 = Angle(0.543, unit='degree')
    a4 = Angle('1d2m3 4s', unit='degree')
    assert Angle(str(a1)) == a1
    assert Angle(str(a2)) == a2
    assert Angle(str(a3)) == a3
    assert Angle(str(a4)) == a4
    ra = Longitude('1h2m3 4s')
    dec = Latitude('1d2m3 4s')
    assert_allclose(Angle(str(ra)), ra)
    assert_allclose(Angle(str(dec)), dec)
