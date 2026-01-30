def test_simple():
    assert 1 + 1 == 2

def test_import_ukg_sdk():
    import ukg_sdk
    assert ukg_sdk is not None
