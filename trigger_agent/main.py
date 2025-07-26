from fastapi import FastAPI, BackgroundTasks
from kafka_consumer import consume_events
import threading

app = FastAPI()

@app.on_event("startup")
def start_consumer():
    # Run Kafka consumer in background
    print("[BOOT] Starting Kafka consumer...")
    thread = threading.Thread(target=consume_events, daemon=True)
    thread.start()

@app.get("/health")
async def health_check():
    return {"status": "trigger_agent is up"}