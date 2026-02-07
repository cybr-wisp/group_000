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
    # NOTE: this expects you already have the plum theme CSS you liked.
    # Keep this minimal in utils; your Home page is already styling nicely.
    st.markdown(
        """
        <style>
        .muted{opacity:.72;font-size:.92rem;}
        .badge{display:inline-block;padding:0.20rem 0.60rem;border-radius:999px;font-size:0.85rem;font-weight:800;border:1px solid rgba(0,0,0,.10);}
        .g{background:rgba(46,204,113,.14);}
        .y{background:rgba(241,196,15,.18);}
        .r{background:rgba(231,76,60,.14);}
        .p{background:rgba(155,89,182,.14);} /* pending */
        .interrupt{border:1px solid rgba(231,76,60,.35);background:rgba(231,76,60,.09);padding:0.95rem;border-radius:16px;}
        </style>
        """,
        unsafe_allow_html=True
    )

# ---------- STATE ----------
def init_state():
    st.session_state.setdefault("auth", False)
    st.session_state.setdefault("role", "student")  # student | landlord

    st.session_state.setdefault("profile", {
        "budget": 1200,
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

    # Landlord profile (verification funnel)
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

    # Listings stored in-session (so landlord can create + verify listings)
    st.session_state.setdefault("listings_override", None)

    # Demo listing metadata stored separately by id (safe for “Unknown” fields)
    st.session_state.setdefault("listing_meta", {})  # {id: {address, available_date, lease_length, photo_count, ...}}

# ---------- DATA ----------
@st.cache_data
def load_listings(csv_path: str) -> pd.DataFrame:
    """
    Loads listings.csv but ALSO guarantees required MVP columns exist:
    id,title,area,price,beds,landlord,verified_at,pending,photo_count
    """
    df = pd.read_csv(csv_path)

    # normalize columns
    df.columns = [c.strip() for c in df.columns]
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

    # REQUIRED fallbacks
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

    # verified_at fallback: seed realistic “Verified 1–16 days ago”
    if verifiedc is None:
        now = pd.Timestamp.now().normalize()
        ages = np.random.choice([1, 2, 5, 8, 12, 16], size=len(df))
        df["verified_at"] = [now - pd.Timedelta(days=int(a)) for a in ages]
        verifiedc = "verified_at"

    out = pd.DataFrame({
        "id": pd.to_numeric(df[idc], errors="coerce").fillna(0).astype(int),
        "title": df[titlec].astype(str),
        "area": df[areac].astype(str),
        "price": pd.to_numeric(df[pricec], errors="coerce").fillna(999).astype(int),
        "beds": pd.to_numeric(df[bedsc], errors="coerce").fillna(1).astype(int),
        "landlord": df[landlordc].astype(str),
        "verified_at": pd.to_datetime(df[verifiedc], errors="coerce"),
    })

    out["verified_at"] = out["verified_at"].fillna(pd.Timestamp.now().normalize() - pd.Timedelta(days=2))

    # ✅ Funnel columns (guaranteed)
    if "pending" not in out.columns:
        out["pending"] = False
    if "photo_count" not in out.columns:
        out["photo_count"] = 3  # seeded sample listings are “complete”
    if "lease_draft_uploaded" not in out.columns:
        out["lease_draft_uploaded"] = False

    # ensure types
    out["pending"] = out["pending"].astype(bool)
    out["photo_count"] = pd.to_numeric(out["photo_count"], errors="coerce").fillna(0).astype(int)
    out["lease_draft_uploaded"] = out["lease_draft_uploaded"].astype(bool)

    return out


def get_listings() -> pd.DataFrame:
    """Return listings dataframe, using in-session override if present."""
    if st.session_state.get("listings_override") is not None:
        return st.session_state["listings_override"].copy()
    return load_listings("data/listings.csv")


def set_listings(df: pd.DataFrame):
    """Persist listings changes for this demo session."""
    st.session_state["listings_override"] = df.copy()


def ensure_selected_listing(df: pd.DataFrame):
    if st.session_state.selected_listing_id is None and not df.empty:
        st.session_state.selected_listing_id = int(df.iloc[0]["id"])


# ---------- LISTING META (fills “Unknown” fields) ----------
def listing_meta(listing_id: int) -> dict:
    """
    Returns rich metadata for the listing card.
    This is where we fill the “Unknown” fields without needing your CSV to change.
    """
    store = st.session_state.get("listing_meta", {})
    if listing_id in store:
        return store[listing_id]

    # seeded defaults (nice pitch-ready)
    areas = ["Downtown", "Sandy Hill", "ByWard Market", "Glebe", "Vanier"]
    streets = ["Laurier Ave E", "Wilbrod St", "King Edward Ave", "Elgin St", "Rideau St"]
    rng = np.random.RandomState(listing_id * 17)

    meta = {
        "address": f"{rng.randint(40, 420)} {rng.choice(streets)}",
        "available_date": str((date.today() + timedelta(days=21)).isoformat()),
        "lease_length": f"{rng.choice([8, 12])} months",
        "photo_count": int(rng.choice([1, 2, 3])),
        "area_detail": rng.choice(areas),
    }

    store[listing_id] = meta
    st.session_state["listing_meta"] = store
    return meta


def set_listing_meta(listing_id: int, meta_updates: dict):
    store = st.session_state.get("listing_meta", {})
    base = store.get(listing_id, listing_meta(listing_id))
    base.update(meta_updates or {})
    store[listing_id] = base
    st.session_state["listing_meta"] = store


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


def pending_badge():
    return '<span class="badge p">Pending verification</span>'


def compute_price_band(df: pd.DataFrame, area: str):
    area_df = df[df["area"] == area]
    if len(area_df) < 3:
        return 800, 950
    lo = int(np.percentile(area_df["price"], 25))
    hi = int(np.percentile(area_df["price"], 75))
    return lo, hi


# ---------- FUNNEL VISIBILITY ----------
def is_visible_to_students(row: pd.Series) -> bool:
    """
    This is the core of your “verification funnel”.
    Students ONLY see:
      - not pending
      - trust status in Verified/Stale
      - photo_count >= 1
    Unverified OR Pending are auto-hidden.
    """
    try:
        if bool(row.get("pending", False)):
            return False

        ts = row.get("verified_at", None)
        if ts is None or pd.isna(ts):
            return False

        status, _ = trust_status(ts)
        if status not in ["Verified", "Stale"]:
            return False

        if int(row.get("photo_count", 0)) < 1:
            return False

        return True
    except Exception:
        return False


def can_landlord_make_visible() -> bool:
    """
    Landlord must:
    verify email + phone
    add card on file
    then confirm availability
    """
    p = st.session_state.get("landlord_profile", {})
    return bool(p.get("email_verified")) and bool(p.get("phone_verified")) and bool(p.get("card_on_file"))


def mark_verified(listing_id: int):
    """
    Call this after landlord confirms availability.
    Sets: pending=False, verified_at=now
    """
    df = get_listings()
    if df.empty:
        return
    df.loc[df["id"] == int(listing_id), "pending"] = False
    df.loc[df["id"] == int(listing_id), "verified_at"] = pd.Timestamp.now().normalize()
    set_listings(df)


# ---------- CREATE LISTING (Request to List form) ----------
def create_pending_listing(
    landlord_name: str,
    title: str,
    area: str,
    price: int,
    beds: int,
    address: str,
    available_date: str,
    lease_length: str,
    photo_count: int,
    lease_draft_uploaded: bool
) -> int:
    """
    Creates a listing in 🟡 Pending verification state.
    It will NOT appear to students until mark_verified() is called.
    """
    df = get_listings()

    new_id = int(df["id"].max() + 1) if not df.empty else 1

    row = {
        "id": new_id,
        "title": title or f"Unit {new_id}",
        "area": area or "Unknown",
        "price": int(price) if price is not None else 999,
        "beds": int(beds) if beds is not None else 1,
        "landlord": landlord_name or "Private Landlord",
        "verified_at": pd.NaT,          # not verified yet
        "pending": True,               # ✅ funnel flag
        "photo_count": int(photo_count),
        "lease_draft_uploaded": bool(lease_draft_uploaded),
    }

    df2 = pd.concat([df, pd.DataFrame([row])], ignore_index=True)
    set_listings(df2)

    # store nice metadata for cards
    set_listing_meta(new_id, {
        "address": address or "Unknown",
        "available_date": available_date or str((date.today() + timedelta(days=30)).isoformat()),
        "lease_length": lease_length or "12 months",
        "photo_count": int(photo_count),
        "area_detail": area or "Unknown",
    })

    return new_id


# ---------- RISK / LEASE SCAN ----------
def risk_detect(message: str):
    txt = (message or "").lower()
    hits = []
    total = 0
    for rule in RISK_RULES:
        if re.search(rule["pattern"], txt):
            hits.append(rule)
            total += rule["score"]
    return min(total, 100), hits


def lease_scan(text: str):
    t = (text or "").lower()
    flags = []
    for rule in LEASE_FLAG_RULES:
        if re.search(rule["pattern"], t):
            flags.append(rule)
    return flags


# ---------- SIDEBAR TIMELINE ----------
def render_risk_timeline_sidebar(df: pd.DataFrame):
    st.sidebar.markdown("### 🧾 Risk Timeline")
    st.sidebar.caption("Explainable events judges can see.")
    if not st.session_state.risk_timeline:
        st.sidebar.caption("No risk events yet.")
        return
    for e in reversed(st.session_state.risk_timeline[-7:]):
        st.sidebar.markdown(
            f"**{e['event']}**  \nScore: **{e['score']}**  \n_{e['excerpt']}_  \n{e['time']}"
        )
        st.sidebar.divider()
