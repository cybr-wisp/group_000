import streamlit as st
import pandas as pd
import numpy as np
import re
from datetime import date, timedelta
from datetime import datetime as dt

# ---------- CONFIG ----------
TRUST_STALE_DAYS = 7
TRUST_UNVERIFIED_DAYS = 14

RISK_RULES = [
    {
        "name": "Deposit before viewing",
        "pattern": r"\b(deposit|down\s*payment|first\s*month)\b.*\b(before|prior)\b.*\b(viewing|tour|see)\b|\bbefore\s*(you\s*)?(see|view)\b.*\bdeposit\b",
        "score": 45,
        "why": "Asking for money before you view is a common scam pattern."
    },
    {
        "name": "Urgency language",
        "pattern": r"\b(today\s*only|right\s*now|immediately|asap|many\s+people|lots\s+of\s+interest|someone\s+else|last\s+chance|hold\s*it\s*for\s*you)\b",
        "score": 25,
        "why": "Artificial urgency pressures students into irreversible mistakes."
    },
    {
        "name": "Off-platform payment",
        "pattern": r"\b(whatsapp|telegram|wire\s*transfer|gift\s*card|western\s*union|crypto|bitcoin|pay\s*outside|cash\s*only)\b",
        "score": 40,
        "why": "Off-platform payment is harder to dispute and often used in scams."
    }
]

LEASE_FLAG_RULES = [
    {
        "name": "Deposit wording risk",
        "pattern": r"\b(non\s*refundable|nonrefundable|security\s*deposit|key\s*deposit)\b",
        "tip": "If it says 'non-refundable' or 'security deposit', double-check local rules and ask for a written receipt/terms."
    },
    {
        "name": "Sublet clause unclear",
        "pattern": r"\b(sublet|sublease)\b",
        "tip": "If subletting is forbidden or vague, you may be stuck if plans change."
    },
    {
        "name": "Notice / termination mentioned",
        "pattern": r"\b(notice|termination)\b",
        "tip": "Make sure notice period matches local rules and your expected stay."
    },
    {
        "name": "Missing identifiers risk",
        "pattern": r"\b(landlord\s*name|owner|address|unit)\b",
        "tip": "A valid lease should clearly identify the unit + landlord/owner."
    },
]

# ---------- UI STYLE ----------
# ---------- UI STYLE ----------
def inject_css():
    st.markdown(
        """
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;600;800&display=swap');

        :root{
          --plum:#4b0f2f;
          --plum2:#6b143f;
          --soft:#fff7fb;
          --card:rgba(255,255,255,.78);
          --border:rgba(0,0,0,.10);
          --text:#14121a;
        }

        html, body, [class*="css"]{
          font-family: "Plus Jakarta Sans", ui-sans-serif, system-ui, -apple-system, Segoe UI, Roboto, Arial;
          color: var(--text);
        }

        .block-container { padding-top: 1.2rem; padding-bottom: 2.2rem; max-width: 1180px; }
        [data-testid="stSidebar"] { padding-top: 1.0rem; }

        /* Background (plum glow) */
        [data-testid="stAppViewContainer"]{
          background:
            radial-gradient(1100px 600px at 15% 8%, rgba(75,15,47,.18), transparent 60%),
            radial-gradient(900px 520px at 85% 0%, rgba(107,20,63,.12), transparent 55%),
            linear-gradient(180deg, rgba(255,252,254,1), rgba(250,246,249,1));
        }

        /* Brand */
        .brand-title { font-size: 1.55rem; font-weight: 900; letter-spacing: -0.03em; }
        .brand-sub { opacity: .78; margin-top: .25rem; }

        /* Cards */
        .card{
          border: 1px solid var(--border);
          background: var(--card);
          border-radius: 20px;
          padding: 1rem;
          box-shadow: 0 12px 30px rgba(0,0,0,.06);
        }
        .muted{opacity:.72;font-size:.92rem;}

        /* Badges */
        .badge{display:inline-block;padding:0.20rem 0.60rem;border-radius:999px;font-size:0.85rem;font-weight:800;border:1px solid rgba(0,0,0,.10);}
        .g{background:rgba(46,204,113,.14);}
        .y{background:rgba(241,196,15,.18);}
        .r{background:rgba(231,76,60,.14);}
        .p{background:rgba(75,15,47,.12);} /* pending */

        /* Buttons */
        div.stButton > button{
          border-radius: 16px !important;
          font-weight: 800 !important;
          border: 1px solid rgba(0,0,0,.10) !important;
        }
        /* Make primary button plum */
        div.stButton > button[kind="primary"]{
          background: linear-gradient(135deg, var(--plum), var(--plum2)) !important;
          color: white !important;
          border: none !important;
        }

        /* Inputs */
        [data-baseweb="input"] input, [data-baseweb="textarea"] textarea {
          border-radius: 14px !important;
        }

        /* Hero */
        .hero{
          padding: 1.2rem 1.2rem;
          border: 1px solid var(--border);
          border-radius: 22px;
          background: rgba(255,255,255,.72);
          backdrop-filter: blur(8px);
          box-shadow: 0 12px 30px rgba(0,0,0,.06);
        }
        .hero-title { font-size: 2.10rem; font-weight: 900; letter-spacing: -0.04em; margin: 0; }
        .hero-sub { opacity: .78; margin-top: .35rem; font-size: 1.03rem; }

        /* Carousel */
        .feature-card{
          border: 1px solid var(--border);
          border-radius: 20px;
          padding: 1rem 1rem;
          background: rgba(255,255,255,.80);
          box-shadow: 0 12px 30px rgba(0,0,0,.06);
        }
        .pill{
          display:inline-block;
          padding: .22rem .62rem;
          border-radius: 999px;
          font-weight: 900;
          font-size: .85rem;
          border: 1px solid rgba(0,0,0,.10);
          background: rgba(75,15,47,.08);
        }
        .dots{opacity:.6; letter-spacing: 2px; text-align:center;}

        /* Scam interrupt */
        .interrupt{
          border:1px solid rgba(107,20,63,.35);
          background:rgba(107,20,63,.09);
          padding:0.95rem;border-radius:16px;
        }

        /* Phone frame */
        .phone{
          border-radius: 28px;
          border: 1px solid rgba(0,0,0,.14);
          background: rgba(255,255,255,.86);
          padding: .95rem;
          box-shadow: 0 18px 46px rgba(0,0,0,.10);
          max-width: 360px;
          margin-left: auto;
        }
        .phone-notch{
          width: 120px; height: 18px; border-radius: 999px;
          background: rgba(0,0,0,.08);
          margin: 0 auto .8rem auto;
        }
        </style>
        """,
        unsafe_allow_html=True
    )
# ---------- STATE ----------
def init_state():
    st.session_state.setdefault("auth", False)
    st.session_state.setdefault("role", "student")  # student | landlord

    st.session_state.setdefault("profile", {
        "budget": 900,
        "move_in": date.today() + timedelta(days=30),
        "areas": [],
        "commute_max": 25,
        "roommates": 1,
    })

    st.session_state.setdefault("squad", {
        "name": "My Squad",
        "invite_code": f"SQD-{np.random.randint(1000,9999)}",
        "members": ["You"],
        "checklist": {
            "Set budget + move-in date": False,
            "Pick areas": False,
            "Shortlist 3 listings": False,
            "Book at least 1 viewing": False,
            "Upload lease draft (optional)": False,
        }
    })

    st.session_state.setdefault("selected_listing_id", None)
    st.session_state.setdefault("risk_timeline", [])  # list of dicts
    st.session_state.setdefault("chat", [])           # list of dicts

    # One-click incident pack generator (demo)
    st.session_state.setdefault("incident_pack", {
        "ready": False,
        "items": {
            "Proof of payment (receipt/screenshot)": False,
            "All communication records": False,
            "Original listing screenshots": False,
            "Evidence of non-delivery / address mismatch": False,
        }
    })

    st.session_state.setdefault("viewing_checklist", {
        "Address matches listing": False,
        "Utilities confirmed": False,
        "Lease length confirmed": False,
        "Landlord identity confirmed": False,
    })

    # ✅ Landlord profile (demo persistence in session)
    st.session_state.setdefault("landlord_profile", {
        "company_name": "",
        "contact_name": "",
        "email": "",
        "phone": "",
        "email_verified": False,
        "phone_verified": False,
        "card_on_file": False,
        "id_on_file": False,
        "created_at": None,
    })

    # ✅ Listings in-session override (so landlord can reconfirm availability)
    st.session_state.setdefault("listings_override", None)

    # ✅ Funnel metadata for listings (fills "Unknown" + enforces photo-required)
    st.session_state.setdefault("listing_details", {})
    st.session_state.setdefault("pending_listing_ids", set())

    # Seed details for your 6 sample listings (only once)
    if not st.session_state["listing_details"]:
        st.session_state["listing_details"] = {
            1: {"address":"Downtown (near uOttawa) • 123 King Edward Ave", "available_date":"2026-03-01", "lease_length":"12 months", "photos_ok": True, "lease_uploaded": False, "status":"Verified"},
            2: {"address":"Downtown • 250 Laurier Ave E", "available_date":"2026-03-01", "lease_length":"12 months", "photos_ok": True, "lease_uploaded": False, "status":"Verified"},
            3: {"address":"Sandy Hill • 45 Wilbrod St", "available_date":"2026-03-01", "lease_length":"8 months",  "photos_ok": True, "lease_uploaded": False, "status":"Verified"},
            4: {"address":"Sandy Hill • 88 Chapel St", "available_date":"2026-03-15", "lease_length":"12 months", "photos_ok": True, "lease_uploaded": False, "status":"Verified"},
            5: {"address":"Glebe • 12 Bank St", "available_date":"2026-03-01", "lease_length":"12 months", "photos_ok": True, "lease_uploaded": False, "status":"Verified"},
            6: {"address":"Glebe • 19 Fifth Ave", "available_date":"2026-03-01", "lease_length":"8 months",  "photos_ok": True, "lease_uploaded": False, "status":"Verified"},
        }

# ---------- DATA ----------
@st.cache_data
def load_listings(csv_path: str):
    df = pd.read_csv(csv_path)

    cols = {c.lower(): c for c in df.columns}

    def get_col(*names):
        for n in names:
            if n in cols:
                return cols[n]
        return None

    idc = get_col("id", "listing_id")
    titlec = get_col("title", "name", "listing_title")
    areac = get_col("area", "neighborhood", "location")
    pricec = get_col("price", "rent", "monthly_rent")
    bedsc = get_col("beds", "bedrooms", "bedroom")
    landlordc = get_col("landlord", "owner", "company")
    verifiedc = get_col("verified_at", "last_verified", "verified")

    if idc is None:
        df["id"] = np.arange(1, len(df) + 1)
        idc = "id"
    if titlec is None:
        df["title"] = "Listing"
        titlec = "title"
    if areac is None:
        df["area"] = "Unknown"
        areac = "area"
    if pricec is None:
        df["price"] = 999
        pricec = "price"
    if bedsc is None:
        df["beds"] = 1
        bedsc = "beds"
    if landlordc is None:
        df["landlord"] = "Private Landlord"
        landlordc = "landlord"
    if verifiedc is None:
        now = pd.Timestamp.now().normalize()
        ages = np.random.choice([1, 2, 5, 8, 12, 16], size=len(df))
        df["verified_at"] = [now - pd.Timedelta(days=int(a)) for a in ages]
        verifiedc = "verified_at"

    out = pd.DataFrame({
        "id": df[idc].astype(int),
        "title": df[titlec].astype(str),
        "area": df[areac].astype(str),
        "price": pd.to_numeric(df[pricec], errors="coerce").fillna(999).astype(int),
        "beds": pd.to_numeric(df[bedsc], errors="coerce").fillna(1).astype(int),
        "landlord": df[landlordc].astype(str),
        "verified_at": pd.to_datetime(df[verifiedc], errors="coerce"),
    })

    out["verified_at"] = out["verified_at"].fillna(pd.Timestamp.now().normalize() - pd.Timedelta(days=2))
    return out

@st.cache_data
def load_roommates(csv_path: str):
    df = pd.read_csv(csv_path)
    df.columns = [c.strip().lower() for c in df.columns]

    if "id" in df.columns:
        df["id"] = pd.to_numeric(df["id"], errors="coerce").fillna(0).astype(int)
    if "cleanliness" in df.columns:
        df["cleanliness"] = pd.to_numeric(df["cleanliness"], errors="coerce").fillna(5).astype(int)
    if "noise" in df.columns:
        df["noise"] = pd.to_numeric(df["noise"], errors="coerce").fillna(5).astype(int)
    if "budget" in df.columns:
        df["budget"] = pd.to_numeric(df["budget"], errors="coerce").fillna(900).astype(int)

    for col in ["name","sleep_schedule","smoking","pets","notes"]:
        if col not in df.columns:
            df[col] = ""

    return df

def get_listings():
    if st.session_state.get("listings_override") is not None:
        return st.session_state["listings_override"].copy()
    return load_listings("data/listings.csv")

def set_listings(df: pd.DataFrame):
    st.session_state["listings_override"] = df.copy()

def ensure_selected_listing(df):
    if st.session_state.selected_listing_id is None and not df.empty:
        st.session_state.selected_listing_id = int(df.iloc[0]["id"])

# ---------- LISTING FUNNEL META ----------
def listing_meta(listing_id: int) -> dict:
    return st.session_state.get("listing_details", {}).get(int(listing_id), {
        "address": "—",
        "available_date": "—",
        "lease_length": "—",
        "photos_ok": False,
        "lease_uploaded": False,
        "status": "Pending",
    })

def set_listing_meta(listing_id: int, updates: dict):
    st.session_state.setdefault("listing_details", {})
    base = st.session_state["listing_details"].get(int(listing_id), {})
    base.update(updates)
    st.session_state["listing_details"][int(listing_id)] = base

def mark_pending(listing_id: int):
    st.session_state.setdefault("pending_listing_ids", set())
    st.session_state["pending_listing_ids"].add(int(listing_id))
    set_listing_meta(int(listing_id), {"status": "Pending"})

def mark_verified(listing_id: int):
    st.session_state.setdefault("pending_listing_ids", set())
    if int(listing_id) in st.session_state["pending_listing_ids"]:
        st.session_state["pending_listing_ids"].remove(int(listing_id))
    set_listing_meta(int(listing_id), {"status": "Verified"})

def pending_badge():
    return '<span class="badge p">Pending verification</span>'

# ---------- TRUST / BADGES ----------
def days_since(ts: pd.Timestamp) -> int:
    return int((pd.Timestamp.now().normalize() - ts.normalize()).days)

def trust_status(ts: pd.Timestamp):
    d = days_since(ts)
    if d <= TRUST_STALE_DAYS:
        return "Verified", "g"
    if d <= TRUST_UNVERIFIED_DAYS:
        return "Stale", "y"
    return "Unverified", "r"

def trust_badge(ts: pd.Timestamp):
    status, cls = trust_status(ts)
    d = days_since(ts)
    when = "today" if d <= 0 else f"{d}d ago"
    return f'<span class="badge {cls}">{status} • {when}</span>'

def compute_price_band(df: pd.DataFrame, area: str):
    area_df = df[df["area"] == area]
    if len(area_df) < 3:
        return 800, 950
    lo = int(np.percentile(area_df["price"], 25))
    hi = int(np.percentile(area_df["price"], 75))
    return lo, hi

def is_visible_to_students(row) -> bool:
    """
    Visibility:
    - Trust is Verified or Stale
    - Not Pending
    - Photos mandatory (photos_ok True)
    - Auto-hide if Unverified (15+ days)
    """
    lid = int(row["id"])
    meta = listing_meta(lid)

    if meta.get("status") == "Pending":
        return False
    if not meta.get("photos_ok", False):
        return False

    status, _ = trust_status(row["verified_at"])
    return status in ("Verified", "Stale")

# ---------- RISK / LEASE SCAN ----------
def risk_detect(message: str):
    txt = message.lower()
    hits = []
    total = 0
    for rule in RISK_RULES:
        if re.search(rule["pattern"], txt):
            hits.append(rule)
            total += rule["score"]
    return min(total, 100), hits

def lease_scan(text: str):
    t = text.lower()
    flags = []
    for rule in LEASE_FLAG_RULES:
        if re.search(rule["pattern"], t):
            flags.append(rule)
    return flags

def add_risk_event(event_name: str, score: int, excerpt: str):
    st.session_state.setdefault("risk_timeline", [])
    st.session_state["risk_timeline"].append({
        "event": event_name,
        "score": int(score),
        "excerpt": excerpt[:80],
        "time": dt.now().strftime("%H:%M"),
    })

# ---------- INCIDENT PACK ----------
def generate_incident_pack():
    st.session_state["incident_pack"]["ready"] = True
    for k in st.session_state["incident_pack"]["items"].keys():
        st.session_state["incident_pack"]["items"][k] = True

# ---------- SIDEBAR TIMELINE ----------
def render_risk_timeline_sidebar(df):
    st.sidebar.markdown("### 🧾 Risk Timeline")
    if not st.session_state.risk_timeline:
        st.sidebar.caption("No risk events yet.")
        return
    for e in reversed(st.session_state.risk_timeline[-7:]):
        st.sidebar.markdown(
            f"**{e['event']}**  \nScore: **{e['score']}**  \n_{e['excerpt']}_  \n{e['time']}"
        )
        st.sidebar.divider()