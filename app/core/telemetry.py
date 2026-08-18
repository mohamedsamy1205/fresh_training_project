import logging

from fastapi import FastAPI

from opentelemetry import _logs, trace

from opentelemetry.sdk.resources import Resource

from opentelemetry.sdk._logs import (
    LoggerProvider,
    LoggingHandler,
)

from opentelemetry.sdk._logs.export import (
    BatchLogRecordProcessor,
)

from opentelemetry.exporter.otlp.proto.grpc._log_exporter import (
    OTLPLogExporter,
)

from opentelemetry.sdk.trace import (
    TracerProvider,
    SpanProcessor,
)

from opentelemetry.sdk.trace.export import (
    BatchSpanProcessor,
)

from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import (
    OTLPSpanExporter,
)

from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor
from opentelemetry.instrumentation.redis import RedisInstrumentor
from app.core.config import settings
from app.core.database import get_engine


# أسماء الـ spans اللي عايزين نستبعدها من الـ export خالص.
# دي بتتقارن بالاسم *بالظبط* (case-sensitive) زي ما بتظهر في SigNoz.
EXCLUDED_SPAN_NAMES = {
    "connect",
    "SETEX",
    "GET",
}


class FilteringSpanProcessor(SpanProcessor):
    """
    بيلف حوالين أي SpanProcessor تاني (زي BatchSpanProcessor) ويمنع
    أي span اسمه موجود في EXCLUDED_SPAN_NAMES من إنه يتبعت للـ exporter.
    باقي الـ spans (SELECT, GET, endpoints...) بتعدي عادي زي ما هي.
    """

    def __init__(self, wrapped_processor: SpanProcessor):
        self._wrapped = wrapped_processor

    def on_start(self, span, parent_context=None):
        self._wrapped.on_start(span, parent_context)

    def on_end(self, span):
        if span.name in EXCLUDED_SPAN_NAMES:
            return
        self._wrapped.on_end(span)

    def shutdown(self):
        self._wrapped.shutdown()

    def force_flush(self, timeout_millis=30000):
        return self._wrapped.force_flush(timeout_millis)


def setup_telemetry(app: FastAPI) -> None:

    endpoint = settings.OTEL_EXPORTER_OTLP_ENDPOINT

    service_name = settings.OTEL_SERVICE_NAME

    resource = Resource.create(
        {
            "service.name": service_name,
        }
    )

    # =========================================================
    # TRACES
    # =========================================================

    tracer_provider = TracerProvider(
        resource=resource
    )

    trace_exporter = OTLPSpanExporter(
        endpoint=endpoint,
        insecure=True,
    )

    tracer_provider.add_span_processor(
        FilteringSpanProcessor(
            BatchSpanProcessor(
                trace_exporter
            )
        )
    )

    trace.set_tracer_provider(
        tracer_provider
    )

    # =========================================================
    # LOGS
    # =========================================================

    logger_provider = LoggerProvider(
        resource=resource
    )

    log_exporter = OTLPLogExporter(
        endpoint=endpoint,
        insecure=True,
    )

    logger_provider.add_log_record_processor(
        BatchLogRecordProcessor(
            log_exporter
        )
    )

    _logs.set_logger_provider(
        logger_provider
    )

    # =========================================================
    # PYTHON LOGGING → OTEL
    # =========================================================

    handler = LoggingHandler(
        level=logging.INFO,
        logger_provider=logger_provider,
    )

    root_logger = logging.getLogger()

    root_logger.setLevel(
        logging.INFO
    )

    root_logger.addHandler(
        handler
    )

    # =========================================================
    # INSTRUMENTATION
    # =========================================================
    # الهدف: نسيب SELECT / Redis commands / exceptions ظاهرة جوا
    # الـ trace لما تدوس عليه، ونشيل بس الـ noise spans (send/receive,
    # connect, SETEX, GET) اللي بتظهر كصفوف منفصلة في الـ list.

    # FastAPI: بيعمل الـ root span (الـ endpoint) + بيستبعد الـ
    # sub-spans الصغيرة بتاعة send/receive
    FastAPIInstrumentor.instrument_app(
        app,
        exclude_spans=["send", "receive"],
    )

    # SQLAlchemy: بيسجل كل SELECT/INSERT/UPDATE كـ child span
    # تحت الـ endpoint. لازم نبعتله الـ engine صراحة (engine=...)
    # مش نسيبه يعتمد على الـ patching التلقائي، لأن get_engine()
    # عندنا lazy (singleton بيتعمل أول مرة حد يستخدم get_db())،
    # ولو الـ engine اتعمل قبل استدعاء الـ instrument() هنا،
    # هيفضل من غير tracing نهائيا وأي query جواه مش هيتسجل.
    SQLAlchemyInstrumentor().instrument(
        engine=get_engine(),
        tracer_provider=tracer_provider,
    )

    # Redis: بيسجل كل أمر (GET, SET, INCRBY...) كـ child span
    # برضو تحت الـ endpoint - سايبينه شغال عشان تشوفه وقت
    # الدخول على تفاصيل الـ trace (وبنستبعد GET/SETEX بالاسم فوق)
    RedisInstrumentor().instrument(
        tracer_provider=tracer_provider,
    )