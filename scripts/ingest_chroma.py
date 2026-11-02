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

REPO_ROOT = Path(__file__).resolve().parent.parent
MODELS_DIR = REPO_ROOT / "models" / "all-MiniLM-L6-v2"
CHROMA_DIR = REPO_ROOT / "chroma_data"

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

POLICY_FAQ_DATA = [
    {
        "id": "tatkal_timing_ac",
        "title": "Tatkal Booking Opening Time for AC Classes",
        "category": "Tatkal Rules",
        "document": "Tatkal booking window opens at 10:00 AM IST on the day prior to the train journey date for all Air-Conditioned (AC) classes including AC First Class (1A), AC 2-Tier (2A), AC 3-Tier (3A), AC 3 Economy (3E), Executive Chair Car (EC), and AC Chair Car (CC). Online booking requires rapid submission due to heavy concurrency."
    },
    {
        "id": "tatkal_timing_non_ac",
        "title": "Tatkal Booking Opening Time for Non-AC Classes",
        "category": "Tatkal Rules",
        "document": "Tatkal booking window opens at 11:00 AM IST on the day prior to the train journey date for Non-AC classes including Sleeper Class (SL) and Second Sitting (2S). Travel dates are calculated from the train's originating station."
    },
    {
        "id": "tatkal_charges_slab",
        "title": "Tatkal Surcharge and Pricing Formula",
        "category": "Tatkal Rules",
        "document": "Tatkal charges are pegged at a percentage of the base fare: 10% of base fare for Sleeper class and 30% of base fare for all AC classes, subject to statutory minimum and maximum limits. For Sleeper: Min Rs 100, Max Rs 200. For AC 3 Tier: Min Rs 300, Max Rs 400. For AC 2 Tier and 1A: Min Rs 400, Max Rs 500. This Tatkal fee is added per passenger to the base fare and GST."
    },
    {
        "id": "tatkal_passenger_limit",
        "title": "Maximum Passengers on Tatkal Booking",
        "category": "Tatkal Rules",
        "document": "A maximum of four (4) passengers can be booked per PNR ticket under Tatkal quota on IRCTC web and PRS counters. Only confirmed or waitlisted tickets are issued; no RAC (Reservation Against Cancellation) is permitted under Tatkal quota in most train types."
    },
    {
        "id": "tatkal_cancellation_refund",
        "title": "Refund on Cancellation of Confirmed Tatkal Ticket",
        "category": "Cancellation & Refunds",
        "document": "No refund of fare is granted on cancellation of confirmed Tatkal tickets. If a confirmed Tatkal ticket is cancelled by the passenger, zero refund (0%) is issued, and the entire fare is forfeited as cancellation charge. Full refund is only permissible if the train is cancelled by railways or delayed by more than 3 hours at originating station."
    },
    {
        "id": "contingent_tatkal_refund",
        "title": "Full Refund Conditions for Tatkal Tickets",
        "category": "Cancellation & Refunds",
        "document": "A 100% full refund on Tatkal tickets is granted only in the following railway-fault scenarios: (1) If the train is delayed by more than 3 hours at passenger's boarding station and passenger chooses not to travel; (2) If train route is diverted and passenger does not want to travel via diverted route; (3) If train is completely cancelled by Railways; (4) If passenger is accommodated in a lower class coach and declines the downgrade."
    },
    {
        "id": "general_cancellation_slab_48h",
        "title": "Cancellation Fee More than 48 Hours Before Departure",
        "category": "Cancellation & Refunds",
        "document": "If a confirmed ticket is cancelled more than 48 hours before scheduled departure of the train, flat cancellation clerkage charges apply per passenger: Rs 240 for AC First Class / Executive Class; Rs 200 for AC 2-Tier / First Class; Rs 180 for AC 3-Tier / AC Chair Car / 3 Economy; Rs 120 for Sleeper Class; and Rs 60 for Second Class (2S)."
    },
    {
        "id": "general_cancellation_slab_12h_48h",
        "title": "Cancellation Fee Between 48 Hours and 12 Hours",
        "category": "Cancellation & Refunds",
        "document": "If a confirmed ticket is cancelled between 48 hours and up to 12 hours before the scheduled train departure, the cancellation fee is 25% of the fare subject to the minimum flat clerkage charge for the respective travel class. The remaining 75% of fare is credited back to the original payment source."
    },
    {
        "id": "general_cancellation_slab_4h_12h",
        "title": "Cancellation Fee Between 12 Hours and 4 Hours",
        "category": "Cancellation & Refunds",
        "document": "If a confirmed ticket is cancelled between 12 hours and up to 4 hours before the scheduled departure of the train (or before chart preparation, whichever is earlier), 50% of the total ticket fare is deducted as cancellation charge. Remaining 50% is refunded."
    },
    {
        "id": "general_cancellation_after_chart",
        "title": "Cancellation After Chart Preparation / Less than 4 Hours",
        "category": "Cancellation & Refunds",
        "document": "No refund is admissible on confirmed tickets if cancelled less than 4 hours before scheduled departure or after chart preparation. In such cases, passengers must file an online Ticket Deposit Receipt (TDR) claiming refund under specific exceptional grounds (e.g. AC failure, medical emergency) within prescribed time limits."
    },
    {
        "id": "id_proof_requirements",
        "title": "Mandatory ID Proof for Train Travel",
        "category": "Travel Policies",
        "document": "At least one passenger on a PNR must produce an original, valid government-issued photo identity proof during train journey to the Ticket Examiner (TTE). Authorized ID proofs include: Aadhaar Card (physical or m-Aadhaar), Voter Identity Card, Passport, Driving License, PAN Card, Central/State Govt Employee Photo ID, Nationalized Bank Passbook with photo, and Student Photo ID card issued by recognized institutions."
    },
    {
        "id": "pnr_status_codes",
        "title": "Understanding PNR Status Codes (CNF, RAC, WL, CAN)",
        "category": "Booking & PNR",
        "document": "PNR (Passenger Name Record) statuses: CNF / CONFIRMED means passenger has an allocated coach and seat/berth. RAC (Reservation Against Cancellation) means passenger has guaranteed boarding permission and shares a side-lower berth with another RAC passenger; seat may get upgraded to full berth upon chart preparation. WL (Waitlist) means passenger is not permitted to board reserved coaches; if unconfirmed after chart preparation, online e-ticket auto-cancels with full refund. CAN means ticket has been cancelled."
    },
    {
        "id": "seat_hold_reservation",
        "title": "Seat Hold Mechanism and Expiry Window",
        "category": "Booking & PNR",
        "document": "During high-concurrency booking, the PRS engine places selected seats into a temporary 'HOLD' state for exactly 8 minutes (480 seconds). This lock guarantees that no other concurrent customer can steal the allocated seat while the passenger completes online payment. If payment confirmation is not received within 8 minutes, the hold expires automatically, and the seats are released back to the general inventory pool."
    },
    {
        "id": "payment_idempotency_security",
        "title": "Payment Idempotency and Duplicate Charge Protection",
        "category": "Payment & Security",
        "document": "All payment confirmation requests require a unique 'Idempotency-Key' HTTP header or parameter. If a network timeout, browser crash, or retry occurs, submitting the same idempotency key prevents double debiting and safely retrieves the existing confirmed transaction record without duplicate billing."
    },
    {
        "id": "senior_citizen_concession",
        "title": "Senior Citizen Concession Rules",
        "category": "Travel Policies",
        "document": "Indian Railways previously offered 40% concession for men aged 60+ and 50% concession for women aged 58+. Senior citizens travelling on reserved berths are automatically prioritized for lower berths during automated seat allocation in SL and 3A classes subject to availability."
    },
    {
        "id": "luggage_allowance_limits",
        "title": "Free Luggage Allowance and Excess Baggage",
        "category": "Travel Policies",
        "document": "Free luggage allowances per passenger: AC First Class: 70 kg free (marginal allowance 15 kg); AC 2-Tier: 50 kg free (marginal allowance 10 kg); AC 3-Tier and Chair Car: 40 kg free (marginal allowance 10 kg); Sleeper Class: 40 kg free (marginal allowance 10 kg). Luggage exceeding limits must be booked in advance in the brake van luggage compartment."
    },
    {
        "id": "child_ticket_rules",
        "title": "Child Fare and Seat Allocation Rules",
        "category": "Travel Policies",
        "document": "Children under 5 years of age travel free of charge without a separate berth. For children aged between 5 and 11 years, full adult fare is charged if a separate berth or seat is opted. If no separate berth is requested for children aged 5-11, half of the adult base fare is charged without seat allocation."
    },
    {
        "id": "tatkal_opening_speed",
        "title": "Tatkal Rush Hours and Concurrency Handling",
        "category": "Tatkal Rules",
        "document": "During the first 15 minutes of Tatkal opening (10:00 to 10:15 AM for AC and 11:00 to 11:15 AM for Non-AC), IRCTC PRS systems experience millions of requests per minute. The system employs row-level locks, skip locked queues, and memory-cached availability to prevent race conditions and eliminate double bookings."
    },
    {
        "id": "berth_types_explanation",
        "title": "Berth Types in Indian Railway Coaches",
        "category": "Travel Policies",
        "document": "Indian railway sleeper and AC coaches contain specific berth configurations: Lower Berth (LB) on the floor level; Middle Berth (MB) folded up during daytime; Upper Berth (UB) at the top; Side Lower (SL) along the corridor; Side Upper (SU) above the side lower; and Side Middle (SM) in select high-density 3E coaches. In daytime chair cars (CC/EC), seats are designated as Window (W), Middle (M), and Aisle (A)."
    },
    {
        "id": "tdr_filing_procedure",
        "title": "Ticket Deposit Receipt (TDR) Filing and Settlement",
        "category": "Cancellation & Refunds",
        "document": "A Ticket Deposit Receipt (TDR) can be filed online for tickets cancelled after chart preparation under recognized scenarios such as train diverted, AC failure in coach, passenger unable to travel due to late running train (>3 hours), or party partially confirmed. TDRs are verified by Chief Commercial Managers (CCM) and refunds are processed within 90 days."
    }
]

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

    train_ids = [t["id"] for t in TRAIN_DATA]
    train_docs = [t["document"] for t in TRAIN_DATA]
    train_metas = [t["metadata"] for t in TRAIN_DATA]

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
