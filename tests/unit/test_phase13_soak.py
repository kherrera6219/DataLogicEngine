from __future__ import annotations

from backend.observability.soak import SOAK_PROFILES, evaluate_soak


def _sample(**overrides: object) -> dict[str, object]:
    sample: dict[str, object] = {
        "rss_bytes": 100,
        "thread_count": 5,
        "handle_count": 20,
        "child_process_count": 0,
        "log_bytes": 1000,
        "support_archive_count": 1,
        "sample_error": None,
    }
    sample.update(overrides)
    return sample


def test_short_engineering_run_cannot_qualify_cp13_e():
    profile = SOAK_PROFILES["stress24"]

    report = evaluate_soak(
        profile,
        [_sample(), _sample(rss_bytes=200, log_bytes=1100)],
        observed_duration_seconds=60,
        installed_application=True,
    )

    assert report["resource_checks_passed"] is True
    assert report["qualifies_cp13_e"] is False
    assert report["status"] == "engineering_observation_only"


def test_full_installed_run_qualifies_only_when_every_bound_passes():
    profile = SOAK_PROFILES["idle72"]

    report = evaluate_soak(
        profile,
        [_sample(), _sample(rss_bytes=200, thread_count=6, log_bytes=1100)],
        observed_duration_seconds=profile.required_duration_seconds,
        installed_application=True,
    )

    assert report["qualifies_cp13_e"] is True
    assert report["status"] == "qualified"


def test_growth_or_observation_failure_blocks_qualification():
    profile = SOAK_PROFILES["stress24"]

    report = evaluate_soak(
        profile,
        [
            _sample(),
            _sample(
                rss_bytes=profile.max_rss_growth_bytes + 101,
                sample_error="process_resource_observation_failed",
            ),
        ],
        observed_duration_seconds=profile.required_duration_seconds,
        installed_application=True,
    )

    assert report["resource_checks_passed"] is False
    assert report["qualifies_cp13_e"] is False
    assert report["checks"]["rss_bytes_growth"]["passed"] is False
    assert report["checks"]["sample_integrity"]["passed"] is False


def test_support_archive_retention_is_a_soak_bound():
    profile = SOAK_PROFILES["idle72"]

    report = evaluate_soak(
        profile,
        [_sample(), _sample(support_archive_count=6)],
        observed_duration_seconds=profile.required_duration_seconds,
        installed_application=True,
    )

    assert report["checks"]["support_archive_count"]["passed"] is False
    assert report["qualifies_cp13_e"] is False
