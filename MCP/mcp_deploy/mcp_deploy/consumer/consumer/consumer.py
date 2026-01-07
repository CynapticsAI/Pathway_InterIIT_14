import pathway as pw
import csv
import os
import sys
from transformers import pipeline

# --- LOAD FINBERT ---
# This will load the model we downloaded in the Dockerfile
print("⏳ Loading FinBERT model... (this may take a moment)")
classifier = pipeline("sentiment-analysis", model="ProsusAI/finbert")
print("✅ Model Loaded!")

# --- Configuration ---
KAFKA_TOPIC = "news_data"
KAFKA_BROKER = os.getenv("KAFKA_BROKER", "localhost:9092")
KEYWORDS = ["TSLA", "TESLA"]
ALPHA = 0.05 

# --- Output Setup ---
OUTPUT_DIR = "output"
os.makedirs(OUTPUT_DIR, exist_ok=True) 
CSV_FILE = os.path.join(OUTPUT_DIR, "kafka_sentiment_output.csv")

if not os.path.exists(CSV_FILE):
    with open(CSV_FILE, mode="w", newline="", encoding="utf-8") as f:
        csv.writer(f).writerow(["timestamp", "ticker", "source", "title", "sentiment_label", "compound_score", "ewma_score"])

# --- Global State ---
current_raw_score = 0.0

def get_finbert_score(text):
    """
    Converts FinBERT output to a -1 to 1 score.
    """
    try:
        # Truncate text to 512 tokens to prevent crash
        result = classifier(text[:512])[0] 
        label = result['label']
        score = result['score'] # Confidence (0.0 to 1.0)

        # Map Logic
        if label == 'positive':
            return score        # 0.9 positive -> 0.9
        elif label == 'negative':
            return -score       # 0.9 negative -> -0.9
        else: # neutral
            return 0.0
    except Exception as e:
        print(f"Model Error: {e}")
        return 0.0

def calculate_sentiment_and_print(key, row, time, is_addition):
    global current_raw_score
    
    if not is_addition: return

    title = row["title"]
    ticker = row["ticker"]
    source = row["source"]
    dt_utc = row["dt_utc"]

    if not any(k.lower() in title.lower() for k in KEYWORDS):
        return

    # 1. Get FinBERT Score
    compound = get_finbert_score(title)
    
    # 2. Update EWMA
    current_raw_score = ALPHA * compound + (1 - ALPHA) * current_raw_score

    # 3. Scale to 0-100
    display_score = (current_raw_score + 1) / 2 * 100

    print(f"📥 [FINBERT] {source}: \"{title[:40]}...\"")
    print(f"   Raw: {compound:.3f} | 📈 EWMA: {display_score:.2f}")
    sys.stdout.flush()

    with open(CSV_FILE, mode="a", newline="", encoding="utf-8") as f:
        csv.writer(f).writerow([dt_utc, ticker, source, title, "FinBERT", compound, display_score])

# --- Pathway Definitions ---
class IncomingNewsSchema(pw.Schema):
    dt_utc: str
    title: str
    url: str
    ticker: str
    source: str

rdkafka_settings = {
    "bootstrap.servers": KAFKA_BROKER,
    "group.id": "finbert_consumer_group", # New group ID for new logic
    "auto.offset.reset": "earliest" 
}

# Note: using 'topic' based on your fix!
kafka_table = pw.io.kafka.read(
    rdkafka_settings,
    topic="news_data", 
    schema=IncomingNewsSchema,
    format="json",
    autocommit_duration_ms=100
)

pw.io.subscribe(kafka_table, calculate_sentiment_and_print)
print(f"👀 FinBERT Consumer started...")
pw.run()