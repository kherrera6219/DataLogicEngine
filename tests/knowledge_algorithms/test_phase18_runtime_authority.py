from scripts.verify_ka_runtime_authority import verify


def test_phase18_runtime_has_one_deduplicated_authority():
    evidence = verify()

    assert evidence["status"] == "pass", evidence["errors"]
    assert evidence["canonical_capabilities"] == 213
    assert evidence["existing_implementations"] == 132
    assert evidence["implementation_gaps"] == 81
    assert evidence["reviewed_duplicate_aliases"] == 1
    assert evidence["duplicate_canonical_collisions"] == 0
    assert evidence["private_sdk_handler_runtime_present"] is False
