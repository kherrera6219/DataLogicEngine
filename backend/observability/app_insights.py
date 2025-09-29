"""Azure Application Insights integration helpers."""
from __future__ import annotations

import logging
from typing import Optional

from opencensus.ext.azure.log_exporter import AzureLogHandler
from opencensus.ext.azure.trace_exporter import AzureExporter
from opencensus.trace import config_integration
from opencensus.trace.samplers import ProbabilitySampler
from opencensus.trace.tracer import Tracer

_logger = logging.getLogger(__name__)


class _ApplicationInsightsTracer:
    """Hold a reference to the tracer to avoid garbage collection."""

    def __init__(self, connection_string: str) -> None:
        config_integration.trace_integrations(["logging", "requests"])
        self.tracer = Tracer(
            exporter=AzureExporter(connection_string=connection_string),
            sampler=ProbabilitySampler(1.0),
        )


def configure_application_insights(
    connection_string: str,
    logger: logging.Logger,
) -> tuple[AzureLogHandler, _ApplicationInsightsTracer] | None:
    """Attach Application Insights exporters when configuration is present."""

    if not connection_string:
        _logger.debug("Application Insights connection string not provided; skipping integration.")
        return None

    handler = AzureLogHandler(connection_string=connection_string)
    handler.setLevel(logger.level)
    handler.setFormatter(
        logging.Formatter(
            fmt="%(asctime)sZ | %(levelname)s | %(name)s | %(message)s | correlation_id=%(correlation_id)s",
            datefmt="%Y-%m-%dT%H:%M:%S",
        )
    )
    logger.addHandler(handler)
    tracer_holder = _ApplicationInsightsTracer(connection_string)
    _logger.info("Azure Application Insights logging enabled")
    return handler, tracer_holder
