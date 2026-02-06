import streamlit as st
import pandas as pd
import numpy as np
import re
from datetime import date, timedelta

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
        "pattern": r"\b(today\s*only|right\s*now|immediately|asap|many\s+people|lots\s+of\s+interest|someone\s+else|last\s+chance|hold\s+it\s+for\s+you)\b",
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
def inject_css():
    st.markdown(
        """
        <style>
        .block-container { padding-top: 1.4rem; padding-bottom: 2.2rem; }
        [data-testid="stSidebar"] { padding-top: 1.1rem; }
        .badge{display:inline-block;padding:0.18rem 0.55rem;border-radius:999px;font-size:0.85rem;font-weight:650;border:1px solid rgba(0,0,0,.10);background:rgba(0,0,0,.03);}
        .g{background:rgba(46,204,113,.14);}
        .y{background:rgba(241,196,15,.18);}
        .r{background:rgba(231,76,60,.14);}
        .muted{opacity:.72;font-size:.92rem;}
        .interrupt{border:1px solid rgba(231,76,60,.38);background:rgba(231,76,60,.09);padding:0.9rem;border-radius:14px;}
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

# ---------- DATA ----------
@st.cache_data
def load_listings(csv_path: str):
    df = pd.read_csv(csv_path)

    # Normalize column names to expected ones if your CSV differs
    cols = {c.lower(): c for c in df.columns}

    # Required logical columns: id, title, area, price, beds, landlord, verified_at
    # We try best-effort mapping.
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

    # If missing, create safe defaults
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
        # seed a variety of ages
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

    # Fill any NaT with some recent timestamp
    out["verified_at"] = out["verified_at"].fillna(pd.Timestamp.now().normalize() - pd.Timedelta(days=2))
    return out

def ensure_selected_listing(df):
    if st.session_state.selected_listing_id is None and not df.empty:
        st.session_state.selected_listing_id = int(df.iloc[0]["id"])

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

# ---------- SIDEBAR TIMELINE ----------
def render_risk_timeline_sidebar(df):
    st.sidebar.markdown("### 🧾 Risk Timeline")
    if not st.session_state.risk_timeline:
        st.sidebar.caption("No risk events yet.")
        return
    for e in reversed(st.session_state.risk_timeline[-7:]):
        st.sidebar.markdown(f"**{e['event']}**  \nScore: **{e['score']}**  \n_{e['excerpt']}_  \n{e['time']}")
        st.sidebar.divider()


    # Landlord profile (demo persistence in session)
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

    # Listings in-session override (so landlord can reconfirm availability)
    st.session_state.setdefault("listings_override", None)

def get_listings():
    """Return listings dataframe, using in-session override if present."""
    if st.session_state.get("listings_override") is not None:
        return st.session_state["listings_override"].copy()
    return load_listings("data/listings.csv")

def set_listings(df: pd.DataFrame):
    """Persist listings changes for this demo session."""
    st.session_state["listings_override"] = df.copy()