"""Compatibility rejection for the removed SDK sample KA runtime."""

from .executor import KAExecutor


def register_builtin_handlers(executor: KAExecutor) -> None:
    """Reject the removed client-side sample runtime."""

    del executor
    raise TypeError(
        "SDK built-in KA handlers were removed; execute through the installed "
        "DataLogicEngine service"
    )
