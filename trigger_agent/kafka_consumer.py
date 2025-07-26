import json
from kafka import KafkaConsumer
from models import SupportEvent, Trigger
from datetime import datetime, timedelta, timezone


# Kafka setup
consumer = KafkaConsumer(
    'support-events',
    bootstrap_servers=['kafka:9092'],
    group_id='trigger-agent-group', 
    value_deserializer=lambda m: json.loads(m.decode('utf-8'))
)

# In-memory store for event history (for prototype)
event_history: dict[int, list[SupportEvent]] = {}

# Detection logic: example rule
CALL_THRESHOLD = 3
WINDOW_MINUTES = 60 * 24  # last 24 hours


def detect_triggers(event: SupportEvent) -> Trigger | None:
    # Add event to history
    history = event_history.setdefault(event.customer_id, [])
    history.append(event)

    # Filter for calls in the window
    window_start = datetime.now(timezone.utc) - timedelta(minutes=WINDOW_MINUTES)
    recent_calls = [e for e in history if e.type == 'call' and e.timestamp >= window_start]

    if len(recent_calls) >= CALL_THRESHOLD:
        return Trigger(
            customer_id=event.customer_id,
            trigger_type='multiple_calls',
            detected_at=datetime.utcnow()
        )
    return None


def consume_events():
    print("[CONSUMER] Started consume_events()")
    for msg in consumer:
        raw = msg.value
        print(f"[DEBUG] Raw message received: {raw}") 
        try:
            event = SupportEvent(**raw)
        except Exception as e:
            print(f"Invalid event format: {e}")
            continue
        print(f"[DEBUG] Parsed event: {event}")  
        trigger = detect_triggers(event)
        if trigger:
            # Here you might publish to another Kafka topic or call another service
            print(f"Trigger detected: {trigger.dict()}")