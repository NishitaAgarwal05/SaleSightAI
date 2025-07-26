import json
import redis
from kafka import KafkaConsumer
from models import PlanChange, UsageUpdate, DeviceEvent
from threading import Thread

from fastapi import FastAPI
app = FastAPI()


r = redis.Redis(host='redis', port=6379, decode_responses=True)

def consume_context(topic, model_cls, handler):
    consumer = KafkaConsumer(
        topic,
        bootstrap_servers=['kafka:9092'],
        value_deserializer=lambda m: json.loads(m.decode('utf-8')),
        group_id=f"context-{topic}"
    )
    print(f"[CONSUMER] Started consuming from {topic}")
    for msg in consumer:
        obj = model_cls(**msg.value)
        print(f"[DEBUG] Received {topic} message: {obj}")
        handler(obj)

def handle_plan(change: PlanChange):
    print(f"[DEBUG] Handling plan change: {change}")
    r.hset(f"cust:{change.customer_id}", "plan_id", change.plan_id)

def handle_usage(usage: UsageUpdate):
    print(f"[DEBUG] Handling usage update: {usage}")
    r.hset(f"cust:{usage.customer_id}", "usage_hours", usage.usage_hours)

def handle_device(evt: DeviceEvent):
    print(f"[DEBUG] Handling device event: {evt}")
    r.hset(f"cust:{evt.customer_id}", "device", evt.device_type)

@app.on_event("startup")
def start():
    print("[BOOT] Starting context agent consumers...")
    topics = [
        ('plan-changes', PlanChange, handle_plan),
        ('usage-updates', UsageUpdate, handle_usage),
        ('device-events', DeviceEvent, handle_device),
    ]
    for topic, model, fn in topics:
        Thread(target=consume_context, args=(topic, model, fn), daemon=True).start()

@app.get("/health")
async def health_check():
    return {"status": "context_agent is up"}

