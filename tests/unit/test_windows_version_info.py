from scripts.generate_windows_version_info import render_version_info


def test_version_info_uses_product_authority():
    text = render_version_info(
        {
            "product": {
                "name": "DataLogicEngine Desktop",
                "version": "4.4.0",
                "windows_file_version": "4.4.0.0",
            }
        }
    )

    assert "filevers=(4, 4, 0, 0)" in text
    assert "StringStruct('ProductVersion', '4.4.0')" in text
    assert "StringStruct('CompanyName', 'Kevin Herrera')" in text
