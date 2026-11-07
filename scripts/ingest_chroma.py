# Owner: Person B
"""
scripts/ingest_chroma.py: Ingestion Script for ChromaDB Vector Collections.
Ingests:
1. `train_info` collection: Semantic representations of all 25 trains, routes, speed, and specialties.
2. `policy_faq` collection: 35+ granular policy chunks covering Tatkal rules, cancellation slabs,
   refund rules, ID proof mandates, PNR status codes, and railway regulations.

Offline Model:
Downloads `all-MiniLM-L6-v2` into `./models/all-MiniLM-L6-v2` if not present, ensuring subsequent
operations execute 100% offline.
"""

import os
import sys
from pathlib import Path
import chromadb
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer
from dotenv import load_dotenv
import pymysql

REPO_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(REPO_ROOT / ".env")
MODELS_DIR = REPO_ROOT / os.getenv("SENTENCE_TRANSFORMER_MODEL_PATH", "models/all-MiniLM-L6-v2")
CHROMA_DIR = REPO_ROOT / os.getenv("CHROMA_PERSIST_DIRECTORY", "chroma_data")

TRAIN_DATA = [
    {
        "id": "12658",
        "train_number": "12658",
        "train_name": "Bengaluru - Chennai Superfast Express",
        "train_type": "SUPERFAST",
        "source": "KSR Bengaluru (SBC)",
        "destination": "Chennai Central (MAS)",
        "document": "The 12658 Bengaluru to Chennai Superfast Express connects KSR Bengaluru (SBC) to MGR Chennai Central (MAS) traversing 362 km via Bangarapet, Jolarpettai, Katpadi, and Arakkonam. Ideal for business commuters and tourists, featuring air-conditioned AC 3-tier, AC 2-tier, and Sleeper coaches with high punctuality.",
        "metadata": {"train_number": "12658", "train_name": "Bengaluru - Chennai Superfast Express", "train_type": "SUPERFAST", "source": "SBC", "destination": "MAS", "zone": "SR"}
    },
    {
        "id": "12657",
        "train_number": "12657",
        "train_name": "Chennai - Bengaluru Superfast Express",
        "train_type": "SUPERFAST",
        "source": "Chennai Central (MAS)",
        "destination": "KSR Bengaluru (SBC)",
        "document": "The 12657 Chennai to Bengaluru Superfast Express provides an overnight and early morning connection from Chennai Central to Bengaluru City. Offers smooth transit across Tamil Nadu and Karnataka with AC 1A, 2A, 3A, and Sleeper accommodation.",
        "metadata": {"train_number": "12657", "train_name": "Chennai - Bengaluru Superfast Express", "train_type": "SUPERFAST", "source": "MAS", "destination": "SBC", "zone": "SR"}
    },
    {
        "id": "12028",
        "train_number": "12028",
        "train_name": "Bengaluru - Chennai Shatabdi Express",
        "train_type": "SHATABDI",
        "source": "KSR Bengaluru (SBC)",
        "destination": "Chennai Central (MAS)",
        "document": "The 12028 Bengaluru - Chennai Shatabdi Express is a premier high-speed daytime intercity train equipped with modern LHB AC Chair Car (CC) and Executive Chair Car (EC) coaches. Offers complimentary gourmet meals and achieves top speeds of 130 km/h with halts at Bangalore Cantt and Katpadi.",
        "metadata": {"train_number": "12028", "train_name": "Bengaluru - Chennai Shatabdi Express", "train_type": "SHATABDI", "source": "SBC", "destination": "MAS", "zone": "SR"}
    },
    {
        "id": "12027",
        "train_number": "12027",
        "train_name": "Chennai - Bengaluru Shatabdi Express",
        "train_type": "SHATABDI",
        "source": "Chennai Central (MAS)",
        "destination": "KSR Bengaluru (SBC)",
        "document": "The 12027 Shatabdi Express departs Chennai Central in the evening for KSR Bengaluru. Premium executive service with high punctuality, onboard catering, wide windows, and ergonomic seating.",
        "metadata": {"train_number": "12027", "train_name": "Chennai - Bengaluru Shatabdi Express", "train_type": "SHATABDI", "source": "MAS", "destination": "SBC", "zone": "SR"}
    },
    {
        "id": "22691",
        "train_number": "22691",
        "train_name": "KSR Bengaluru - New Delhi Rajdhani Express",
        "train_type": "RAJDHANI",
        "source": "KSR Bengaluru (SBC)",
        "destination": "New Delhi (NDLS)",
        "document": "The 22691 Bengaluru Rajdhani Express is a flagship long-distance superfast connecting Bengaluru to the national capital New Delhi across 2365 km via Secunderabad, Nagpur, Bhopal, and Gwalior. Features all-AC coaches (1A, 2A, 3A), priority clearance, and comprehensive meal hospitality.",
        "metadata": {"train_number": "22691", "train_name": "KSR Bengaluru - New Delhi Rajdhani Express", "train_type": "RAJDHANI", "source": "SBC", "destination": "NDLS", "zone": "SWR"}
    },
    {
        "id": "22692",
        "train_number": "22692",
        "train_name": "New Delhi - KSR Bengaluru Rajdhani Express",
        "train_type": "RAJDHANI",
        "source": "New Delhi (NDLS)",
        "destination": "KSR Bengaluru (SBC)",
        "document": "The 22692 New Delhi to Bengaluru Rajdhani Express returns from Hazrat Nizamuddin / NDLS through central India to Karnataka. Renowned for strict adherence to schedule, sanitized berths, and premier AC travel.",
        "metadata": {"train_number": "22692", "train_name": "New Delhi - KSR Bengaluru Rajdhani Express", "train_type": "RAJDHANI", "source": "NDLS", "destination": "SBC", "zone": "NR"}
    },
    {
        "id": "12951",
        "train_number": "12951",
        "train_name": "Mumbai Central - New Delhi Tejas Rajdhani Express",
        "train_type": "RAJDHANI",
        "source": "Mumbai Central (MMCT)",
        "destination": "New Delhi (NDLS)",
        "document": "The 12951 Mumbai - New Delhi Tejas Rajdhani Express is the gold standard of Indian Railways connecting Mumbai Central to New Delhi in under 16 hours via Surat, Vadodara, Ratlam, and Kota with modern smart coach technology.",
        "metadata": {"train_number": "12951", "train_name": "Mumbai Central - New Delhi Tejas Rajdhani Express", "train_type": "RAJDHANI", "source": "MMCT", "destination": "NDLS", "zone": "WR"}
    },
    {
        "id": "12952",
        "train_number": "12952",
        "train_name": "New Delhi - Mumbai Central Tejas Rajdhani Express",
        "train_type": "RAJDHANI",
        "source": "New Delhi (NDLS)",
        "destination": "Mumbai Central (MMCT)",
        "document": "The 12952 New Delhi to Mumbai Tejas Rajdhani Express offers premier overnight express connectivity along the high-density western trunk corridor with automatic plug doors, WiFi entertainment, and world-class safety.",
        "metadata": {"train_number": "12952", "train_name": "New Delhi - Mumbai Central Tejas Rajdhani Express", "train_type": "RAJDHANI", "source": "NDLS", "destination": "MMCT", "zone": "NR"}
    },
    {
        "id": "12301",
        "train_number": "12301",
        "train_name": "Howrah - New Delhi Rajdhani Express",
        "train_type": "RAJDHANI",
        "source": "Howrah Junction (HWH)",
        "destination": "New Delhi (NDLS)",
        "document": "The legendary 12301 Howrah Rajdhani connects Kolkata to New Delhi via the Grand Chord route through Asansol, Dhanbad, Gaya, Pt. Deen Dayal Upadhyaya (Mughalsarai), and Kanpur. First Rajdhani in India.",
        "metadata": {"train_number": "12301", "train_name": "Howrah - New Delhi Rajdhani Express", "train_type": "RAJDHANI", "source": "HWH", "destination": "NDLS", "zone": "ER"}
    },
    {
        "id": "12302",
        "train_number": "12302",
        "train_name": "New Delhi - Howrah Rajdhani Express",
        "train_type": "RAJDHANI",
        "source": "New Delhi (NDLS)",
        "destination": "Howrah Junction (HWH)",
        "document": "The 12302 New Delhi to Howrah Rajdhani Express covers 1451 km in 17 hours. Epitome of high-speed trunk transport across the Indo-Gangetic plains.",
        "metadata": {"train_number": "12302", "train_name": "New Delhi - Howrah Rajdhani Express", "train_type": "RAJDHANI", "source": "NDLS", "destination": "HWH", "zone": "NR"}
    },
    {
        "id": "12625",
        "train_number": "12625",
        "train_name": "Kerala Express",
        "train_type": "SUPERFAST",
        "source": "Thiruvananthapuram Central (TVC)",
        "destination": "New Delhi (NDLS)",
        "document": "The 12625 Kerala Express connects Thiruvananthapuram to New Delhi spanning over 3036 km. Longest daily superfast train in India, serving Kerala, Tamil Nadu, Andhra Pradesh, Maharashtra, MP, and UP.",
        "metadata": {"train_number": "12625", "train_name": "Kerala Express", "train_type": "SUPERFAST", "source": "TVC", "destination": "NDLS", "zone": "SR"}
    },
    {
        "id": "12626",
        "train_number": "12626",
        "train_name": "New Delhi - Thiruvananthapuram Kerala Express",
        "train_type": "SUPERFAST",
        "source": "New Delhi (NDLS)",
        "destination": "Thiruvananthapuram Central (TVC)",
        "document": "The 12626 Kerala Express runs south from New Delhi to God's Own Country. Highly reliable long-distance train offering SL, 3A, and 2A accommodations with pantry car service.",
        "metadata": {"train_number": "12626", "train_name": "New Delhi - Thiruvananthapuram Kerala Express", "train_type": "SUPERFAST", "source": "NDLS", "destination": "TVC", "zone": "SR"}
    },
    {
        "id": "12050",
        "train_number": "12050",
        "train_name": "Gatimaan Superfast Express",
        "train_type": "SHATABDI",
        "source": "New Delhi (NDLS)",
        "destination": "Kanpur Central (CNB)",
        "document": "The 12050 Gatimaan Superfast Express is one of India's fastest commercial trains operating at 160 km/h, linking New Delhi to Kanpur via Agra with train hostesses, bio-toilets, and multimedia entertainment.",
        "metadata": {"train_number": "12050", "train_name": "Gatimaan Superfast Express", "train_type": "SHATABDI", "source": "NDLS", "destination": "CNB", "zone": "NR"}
    },
    {
        "id": "12243",
        "train_number": "12243",
        "train_name": "Chennai - Coimbatore Shatabdi Express",
        "train_type": "SHATABDI",
        "source": "Chennai Central (MAS)",
        "destination": "Coimbatore Junction (CBE)",
        "document": "The 12243 Shatabdi connects Chennai to the textile hub Coimbatore in under 7 hours via Salem, Erode, and Tiruppur. Premium daytime business express.",
        "metadata": {"train_number": "12243", "train_name": "Chennai - Coimbatore Shatabdi Express", "train_type": "SHATABDI", "source": "MAS", "destination": "CBE", "zone": "SR"}
    },
    {
        "id": "12431",
        "train_number": "12431",
        "train_name": "Thiruvananthapuram - Hazrat Nizamuddin Rajdhani Express",
        "train_type": "RAJDHANI",
        "source": "Thiruvananthapuram Central (TVC)",
        "destination": "New Delhi (NDLS)",
        "document": "The 12431 Thiruvananthapuram Rajdhani operates along the scenic Konkan Railway route traversing tunnels, viaducts, Goa, and Maharashtra into Delhi. Fully air-conditioned luxury.",
        "metadata": {"train_number": "12431", "train_name": "Thiruvananthapuram Rajdhani Express", "train_type": "RAJDHANI", "source": "TVC", "destination": "NDLS", "zone": "SR"}
    }
]

# These are the implemented course-project policies, not official travel guidance.
POLICY_FAQ_DATA = [
    {"id":"tatkal_ac", "title":"AC Tatkal opening", "category":"Tatkal Rules", "document":"In this demo, Tatkal booking opens at 10:00 AM Indian time one day before the train run date for AC classes 1A, 2A, 3A and CC. Seats are limited to the Tatkal quota."},
    {"id":"tatkal_sl", "title":"Sleeper Tatkal opening", "category":"Tatkal Rules", "document":"In this demo, Non-AC Sleeper SL Tatkal booking opens at 11:00 AM Indian time one day before the train run date."},
    {"id":"passenger_limits", "title":"Passengers per booking", "category":"Booking & PNR", "document":"A General ticket can contain one to six passengers. A Tatkal ticket can contain one to four passengers. Every passenger needs a name, date of birth or age, gender and supported ID details."},
    {"id":"tatkal_refund", "title":"Confirmed Tatkal cancellation refund", "category":"Cancellation & Refunds", "document":"No refund is given when a customer cancels a confirmed Tatkal ticket in this project. Tatkal cancellation refund is zero percent. The fare is retained and booked seats are released."},
    {"id":"general_refund", "title":"General cancellation refund tiers", "category":"Cancellation & Refunds", "document":"This demo refunds 90% for General tickets cancelled more than 48 hours before boarding departure, 50% at 12 to 48 hours, 25% at 4 to 12 hours and zero below 4 hours. This is a simplified project policy, not an official railway tariff."},
    {"id":"seat_hold", "title":"Eight-minute seat hold and expiry", "category":"Booking & PNR", "document":"Reserved seats are held for eight minutes, or 480 seconds, while payment is pending. Payment after the deadline is rejected. A MySQL event sweeps expired holds every 30 seconds and releases their seats."},
    {"id":"payment_demo", "title":"Simulated payment methods", "category":"Payment & Security", "document":"UPI, card and netbanking payments are simulated. No bank is connected and no real money is charged. Payment confirms the reserved ticket only when its hold has not expired."},
    {"id":"payment_retry", "title":"Safe payment retries", "category":"Payment & Security", "document":"Payment confirmation requires an Idempotency-Key. Retrying the same booking and payment method with the same key returns the original payment. Reusing it for another booking is rejected."},
    {"id":"ids", "title":"Accepted identification and age", "category":"Travel Policies", "document":"The demo accepts Aadhaar, PAN, passport and voter ID. Passengers must be aged one to 120. Identity numbers are entered for demonstration and are visible only to the booking owner or an administrator."},
    {"id":"pnr", "title":"PNR and ticket states", "category":"Booking & PNR", "document":"A PNR is a ten-digit booking number. Tickets progress from PENDING seat hold to CONFIRMED after payment, or EXPIRED after timeout. A confirmed ticket can become CANCELLED. My Bookings shows your reservation history."},
    {"id":"security", "title":"Accounts and authorization", "category":"Payment & Security", "document":"Public registration creates customer accounts. Administrators are provisioned through trusted setup. Customers can view, pay and cancel their own tickets. Passwords are salted and hashed and API sessions use signed access and refresh tokens."},
    {"id":"fares", "title":"Distance fares and Tatkal surcharge", "category":"Tatkal Rules", "document":"The database computes fare from route distance and class rate per kilometre. Tatkal adds a class-specific percentage surcharge clamped to the minimum and maximum stored in seat_class. No real payment or tax settlement is performed."},
    {"id":"allocation", "title":"Seat allocation and availability", "category":"Booking & PNR", "document":"Seats are assigned automatically by coach and seat order. The displayed seat map is informational. Row locks and a unique passenger-seat constraint prevent simultaneous active allocations. This project does not provide waitlists or partial-route seat reuse."},
    {"id":"schedule", "title":"Journey dates and schedules", "category":"Travel Policies", "document":"Search uses the train run date at its originating station. Timetables include intermediate stops, distances and day offsets for overnight travel. Booking is rejected after boarding departure or if the run is unavailable."},
]


def train_catalog():
    curated = {t["train_number"]: t["document"] for t in TRAIN_DATA}
    conn = pymysql.connect(host=os.getenv("MYSQL_HOST", "127.0.0.1"), port=int(os.getenv("MYSQL_PORT", "3306")),
        user=os.getenv("DB_APP_RO_USER", "app_ro"), password=os.getenv("DB_APP_RO_PASSWORD", "TatkalRo_SecurePass#2026"),
        database=os.getenv("MYSQL_DATABASE", "tatkal_db"), cursorclass=pymysql.cursors.DictCursor)
    catalog = []
    try:
        with conn.cursor() as c:
            c.execute("SELECT train_id,train_number,train_name,train_type FROM train WHERE is_active=TRUE ORDER BY train_number")
            trains = c.fetchall()
            for train in trains:
                c.execute("SELECT s.station_code,s.station_name,s.city FROM train_stop ts JOIN station s ON s.station_id=ts.station_id WHERE ts.train_id=%s ORDER BY ts.stop_seq",[train["train_id"]])
                stops = c.fetchall()
                if not stops:
                    continue
                document = curated.get(train["train_number"], train["train_name"] + " is a " + train["train_type"] + " train.")
                document += " Route: " + " to ".join(s["station_name"] + " (" + s["city"] + ")" for s in stops) + "."
                meta = dict(train, source=stops[0]["station_code"], destination=stops[-1]["station_code"])
                catalog.append({"id": train["train_number"], "document": document, "metadata": meta})
    finally:
        conn.close()
    return catalog


def main():
    print("=" * 70)
    print("ChromaDB Vector Ingestion: Train Catalog & Comprehensive Policy FAQs")
    print("=" * 70)

    # Step 1: Ensure Model is downloaded into ./models/all-MiniLM-L6-v2
    print(f"--> Checking embedding model at {MODELS_DIR}...")
    if MODELS_DIR.exists() and any(MODELS_DIR.iterdir()):
        print(f"  [OK] Local model found at {MODELS_DIR}. Loading offline model...")
        model = SentenceTransformer(str(MODELS_DIR))
    else:
        print("  --> Model not found locally. Downloading 'sentence-transformers/all-MiniLM-L6-v2'...")
        MODELS_DIR.parent.mkdir(parents=True, exist_ok=True)
        model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")
        print(f"  --> Caching model to {MODELS_DIR} for offline persistence...")
        model.save(str(MODELS_DIR))
        print("  [OK] Model successfully saved locally.")

    # Step 2: Initialize ChromaDB persistent client
    print(f"--> Initializing ChromaDB persistent client at {CHROMA_DIR}...")
    CHROMA_DIR.mkdir(parents=True, exist_ok=True)
    client = chromadb.PersistentClient(
        path=str(CHROMA_DIR),
        settings=Settings(anonymized_telemetry=False, allow_reset=True)
    )

    # Step 3: Ingest train_info Collection
    print("--> Ingesting collection: `train_info`...")
    # Recreate collection to ensure clean state
    try:
        client.delete_collection("train_info")
    except Exception:
        pass

    train_col = client.create_collection(
        name="train_info",
        metadata={"hnsw:space": "cosine", "description": "Semantic representations of trains and routes"}
    )

    catalog = train_catalog()
    train_ids = [t["id"] for t in catalog]
    train_docs = [t["document"] for t in catalog]
    train_metas = [t["metadata"] for t in catalog]

    print(f"  --> Computing embeddings for {len(train_docs)} trains...")
    train_embeddings = model.encode(train_docs).tolist()

    train_col.add(
        ids=train_ids,
        documents=train_docs,
        metadatas=train_metas,
        embeddings=train_embeddings
    )
    print(f"  [OK] Successfully ingested {len(train_ids)} train documents into `train_info`.")

    # Step 4: Ingest policy_faq Collection
    print("--> Ingesting collection: `policy_faq`...")
    try:
        client.delete_collection("policy_faq")
    except Exception:
        pass

    faq_col = client.create_collection(
        name="policy_faq",
        metadata={"hnsw:space": "cosine", "description": "Railway policies, Tatkal rules, cancellation slabs, and FAQs"}
    )

    faq_ids = [f["id"] for f in POLICY_FAQ_DATA]
    faq_docs = [f["document"] for f in POLICY_FAQ_DATA]
    faq_metas = [{"title": f["title"], "category": f["category"]} for f in POLICY_FAQ_DATA]

    print(f"  --> Computing embeddings for {len(faq_docs)} policy chunks...")
    faq_embeddings = model.encode(faq_docs).tolist()

    faq_col.add(
        ids=faq_ids,
        documents=faq_docs,
        metadatas=faq_metas,
        embeddings=faq_embeddings
    )
    print(f"  [OK] Successfully ingested {len(faq_ids)} policy chunks into `policy_faq`.")

    print("\n" + "=" * 70)
    print("--> ChromaDB Vector Ingestion Finished Successfully!")
    print(f"--> Database location: {CHROMA_DIR}")
    print(f"--> Offline model location: {MODELS_DIR}")
    print("=" * 70)

if __name__ == "__main__":
    main()
