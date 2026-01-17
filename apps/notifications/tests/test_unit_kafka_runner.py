import pytest
from types import SimpleNamespace

from app.infrastructure.broker.kafka_consumer import KafkaConsumerRunner
from app.application.services.notifier import NotifierService
from app.infrastructure.repositories.in_memory_event_repo import InMemoryEventRepository


@pytest.mark.asyncio
async def test_kafka_runner_start_noop_when_disabled(monkeypatch):
    from app.infrastructure.broker import kafka_consumer as kc_mod

    monkeypatch.setattr(kc_mod, "settings", SimpleNamespace(kafka_enabled=False))
    svc = NotifierService(InMemoryEventRepository())
    runner = KafkaConsumerRunner(notifier=svc)

    await runner.start()
    assert runner._task is None
    assert runner._consumer is None


@pytest.mark.asyncio
async def test_kafka_runner_stop_safe_when_never_started():
    svc = NotifierService(InMemoryEventRepository())
    runner = KafkaConsumerRunner(notifier=svc)
    await runner.stop()


@pytest.mark.asyncio
async def test_kafka_runner_ensure_consumer_does_not_connect_network(monkeypatch):
    from app.infrastructure.broker import kafka_consumer as kc_mod

    # Patch settings object (frozen dataclass in prod)
    monkeypatch.setattr(
        kc_mod,
        "settings",
        SimpleNamespace(
            kafka_enabled=True,
            kafka_bootstrap="kafka:29092",
            kafka_topic_case_events="cases.events",
            kafka_group_id="notifications-service",
            kafka_auto_offset_reset="latest",
        ),
    )

    # Patch AIOKafkaConsumer to avoid real connection
    class FakeConsumer:
        def __init__(self, *args, **kwargs):
            self.started = False
            self.args = args
            self.kwargs = kwargs

        async def start(self):
            self.started = True

        async def stop(self):
            self.started = False

        def __aiter__(self):
            async def _gen():
                if False:
                    yield None  # pragma: no cover
            return _gen()

    monkeypatch.setattr(kc_mod, "AIOKafkaConsumer", FakeConsumer)

    svc = NotifierService(InMemoryEventRepository())
    runner = KafkaConsumerRunner(notifier=svc)

    consumer = await runner._ensure_consumer()  # noqa: SLF001
    assert consumer is not None
    assert runner._consumer is consumer
    assert consumer.started is True
