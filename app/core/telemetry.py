import logging
import os

from opentelemetry import _logs
from opentelemetry.sdk._logs import LoggerProvider, LoggingHandler
from opentelemetry.sdk._logs.export import BatchLogRecordProcessor
from opentelemetry.exporter.otlp.proto.grpc._log_exporter import OTLPLogExporter
from opentelemetry.sdk.resources import Resource


def setup_logging():
    endpoint = os.getenv(
        "OTEL_EXPORTER_OTLP_ENDPOINT",
        "http://signoz-ingester-1:4317",
    )

    service_name = os.getenv(
        "OTEL_SERVICE_NAME",
        "fresh-training-api",
    )

    resource = Resource.create({
        "service.name": service_name,
    })

    logger_provider = LoggerProvider(resource=resource)

    exporter = OTLPLogExporter(
        endpoint=endpoint,
        insecure=True,
    )

    logger_provider.add_log_record_processor(
        BatchLogRecordProcessor(exporter)
    )

    _logs.set_logger_provider(logger_provider)

    handler = LoggingHandler(
        level=logging.INFO,
        logger_provider=logger_provider,
    )

    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    root_logger.addHandler(handler)