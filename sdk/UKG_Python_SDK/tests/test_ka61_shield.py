"""Safety KAs must execute only in the backend canonical orchestrator."""

from ukg_sdk.overlay import UKGOverlay


def test_overlay_does_not_own_ka61_or_any_local_execution_hook():
    overlay = UKGOverlay()

    assert not hasattr(overlay, "_ka_61_handler")
    assert not hasattr(overlay, "_run_ka_pipeline")
    assert not hasattr(overlay, "_dsqp_orchestrator_cls")
