import json
import redis
from kafka import KafkaConsumer, KafkaProducer
from models import SupportEvent, Trigger, TriggerType
from datetime import datetime, timedelta, timezone
from typing import Optional

r = redis.Redis(host='redis', port=6379, decode_responses=True)

# Kafka setup
consumer = KafkaConsumer(
    'support-events',
    bootstrap_servers=['kafka:9092'],
    group_id='trigger-agent-group', 
    value_deserializer=lambda m: json.loads(m.decode('utf-8'))
)
# thresholds for dynamic triggers
CALL_THRESHOLD = 3
WINDOW_MINUTES = 60 * 24  # 24 hours
USAGE_THRESHOLD_HOURS = 100  # e.g. nearing cap
INACTIVITY_HOURS = 72        # no events for 3 days

# in-memory history store
event_history: dict[int, list[SupportEvent]] = {}
last_event_time: dict[int, datetime] = {}

def detect_triggers(event: SupportEvent) -> Optional[Trigger]:
    now = datetime.now(timezone.utc)
    cust_id = event.customer_id
    
    # update last seen time for inactivity detection
    last_event_time[cust_id] = event.timestamp

    # save event into history
    history = event_history.setdefault(cust_id, [])
    history.append(event)

    # normalize and keep history size bounded
    cutoff = now - timedelta(days=7)
    event_history[cust_id] = [e for e in history if e.timestamp >= cutoff]

    # 1. Multiple calls within window
    calls = [
        e for e in event_history[cust_id]
        if e.type == "call" and e.timestamp >= (now - timedelta(minutes=WINDOW_MINUTES))
    ]
    if len(calls) >= CALL_THRESHOLD:
        return Trigger(
            customer_id=cust_id,
            trigger_type=TriggerType.MULTIPLE_CALLS.value,
            detected_at=now
        )

    # 2. Subscription cancelled
    if event.type == "subscription_canceled":
        return Trigger(
            customer_id=cust_id,
            trigger_type=TriggerType.SUBSCRIPTION_CANCELLED.value,
            detected_at=now
        )

    # 3. Usage nearing cap (context updated externally)
    if event.type == "usage_update" and getattr(event, "usage_hours", 0) >= USAGE_THRESHOLD_HOURS:
        return Trigger(
            customer_id=cust_id,
            trigger_type=TriggerType.USAGE_NEARING_CAP.value,
            detected_at=now
        )

    # 4. Inactivity (if no events for threshold hours)
    last_ts = last_event_time.get(cust_id)
    if last_ts and (now - last_ts) > timedelta(hours=INACTIVITY_HOURS):
        return Trigger(
            customer_id=cust_id,
            trigger_type=TriggerType.INACTIVITY.value,
            detected_at=now
        )

    return None

producer = KafkaProducer(
    bootstrap_servers=['kafka:9092'],
    value_serializer=lambda v: json.dumps(v).encode('utf-8')
)

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
            ctx = r.hgetall(f"cust:{event.customer_id}")
            print(f"[DEBUG] Context for customer {event.customer_id}: {ctx}")
            enriched_trigger = {**json.loads(trigger.model_dump_json()), **ctx}
            producer.send("sales-triggers", enriched_trigger)
            producer.flush()
            print(f"Published enriched trigger: {enriched_trigger}")