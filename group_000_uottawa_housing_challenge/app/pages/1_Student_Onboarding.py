import streamlit as st
from app.utils import init_state, inject_css, get_listings

# ----------------------------
# Init
# ----------------------------
inject_css()   # keep if your app uses it globally (ok)
init_state()

df = get_listings()

# ----------------------------
# Page theme: clean white + deep red
# ----------------------------
st.markdown(
    """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

:root{
  --bg: #ffffff;
  --text: #111827;
  --muted: #6b7280;
  --card: #f8fafc;
  --border: #e5e7eb;
  --accent: #8B1E3F;      /* deep red */
  --accentHover: #741835;
}

.stApp{
  background: var(--bg);
  color: var(--text);
  font-family: Inter, sans-serif;
}

/* Tighten overall spacing a bit */
.block-container{
  padding-top: 2rem;
  max-width: 1100px;
}

/* Headings */
h1,h2,h3,h4{
  color: var(--text) !important;
  font-weight: 800;
  letter-spacing: -0.02em;
}

/* Hero */
.hero{
  background: linear-gradient(135deg, rgba(139,30,63,0.10), rgba(139,30,63,0.03));
  border: 1px solid var(--border);
  border-radius: 18px;
  padding: 18px 20px;
  margin-bottom: 16px;
}
.hero-title{
  font-size: 34px;
  font-weight: 900;
  letter-spacing: -0.03em;
  color: var(--text);
}
.hero-sub{
  margin-top: 6px;
  color: var(--muted);
  font-weight: 500;
}

/* Card look for each column */
[data-testid="column"] > div{
  background: var(--card);
  border: 1px solid var(--border);
  padding: 18px;
  border-radius: 18px;
}

/* Labels + captions */
label, .stMarkdown, .stCaption{
  color: var(--text) !important;
}
small, .stCaption{
  color: var(--muted) !important;
}

/* Inputs */
input, textarea, select{
  background: #ffffff !important;
  color: var(--text) !important;
  border-radius: 12px !important;
  border: 1px solid var(--border) !important;
}

/* Disabled input */
input:disabled{
  background: #f3f4f6 !important;
  color: #6b7280 !important;
  opacity: 1 !important;
}

/* Buttons */
.stButton > button{
  background: var(--accent) !important;
  color: #fff !important;
  border: none !important;
  border-radius: 12px !important;
  font-weight: 700 !important;
  padding: 0.65rem 1rem !important;
}
.stButton > button:hover{
  background: var(--accentHover) !important;
}
.stButton > button:focus{
  box-shadow: 0 0 0 4px rgba(139,30,63,0.20) !important;
}

/* Slider (BaseWeb) */
div[data-baseweb="slider"] *{
  color: var(--text) !important;
}
div[data-baseweb="slider"] div[role="slider"]{
  background: var(--accent) !important;
}
div[data-baseweb="slider"] div[aria-hidden="true"]{
  background: rgba(139,30,63,0.25) !important;
}

/* Progress */
.stProgress > div > div{
  background: var(--accent) !important;
  border-radius: 999px !important;
}
</style>
""",
    unsafe_allow_html=True
)

# ----------------------------
# Areas
# ----------------------------
AREA_GROUPS = {
    "uOttawa / Residences": [
        "Annex", "45 Mann", "Friel", "Leblanc", "Thompson", "Rideau",
        "Hyman Soloway", "90 University", "Stanton", "Marchand", "Henderson",
    ],
    "Nearby / Central Ottawa": [
        "Sandy Hill", "ByWard Market / Lowertown", "Centretown", "Golden Triangle",
        "Old Ottawa East", "The Glebe", "Vanier", "Overbrook",
    ],
    "West / Other": [
        "Hintonburg", "Little Italy", "Westboro", "Alta Vista",
        "Nepean", "Kanata", "Barrhaven",
    ],
}

static_areas = [a for group in AREA_GROUPS.values() for a in group]
df_areas = []
if "area" in df.columns:
    df_areas = [x for x in df["area"].dropna().astype(str).unique().tolist() if x.strip()]

ALL_AREAS = sorted(set(static_areas + df_areas))

# ----------------------------
# Header
# ----------------------------
st.markdown(
    """
    <div class="hero">
      <div class="hero-title">Onboarding → Squad</div>
      <div class="hero-sub">Set shared constraints and invite your squad.</div>
    </div>
    """,
    unsafe_allow_html=True
)

# ----------------------------
# Guard
# ----------------------------
if st.session_state.role != "student":
    st.info("Switch to Student role from Home (log out and log in as Student).")
    st.stop()

# ----------------------------
# Layout
# ----------------------------
left, right = st.columns([1.25, 1])

with left:
    st.markdown("### Your constraints")

    budget = st.slider(
        "Monthly budget (CAD)",
        500, 2500,
        int(st.session_state.profile["budget"]),
        25
    )

    move_in = st.date_input(
        "Move-in date",
        st.session_state.profile["move_in"]
    )

    areas = st.multiselect(
        "Preferred areas",
        options=ALL_AREAS,
        default=st.session_state.profile.get("areas") or []
    )

    commute = st.slider(
        "Max commute (minutes)",
        5, 90,
        int(st.session_state.profile["commute_max"]),
        5
    )

    roommate_options = [1, 2, 3, 4]
    roommates = st.selectbox(
        "Roommate count",
        roommate_options,
        index=roommate_options.index(st.session_state.profile["roommates"])
    )

    st.session_state.profile.update({
        "budget": budget,
        "move_in": move_in,
        "areas": areas,
        "commute_max": commute,
        "roommates": roommates,
    })

    st.session_state.squad["checklist"]["Set budget + move-in date"] = True
    st.session_state.squad["checklist"]["Pick areas"] = bool(areas)

with right:
    st.markdown("### Squad")

    st.session_state.squad["name"] = st.text_input(
        "Squad name",
        st.session_state.squad["name"]
    )

    st.text_input(
        "Invite link (demo)",
        f"https://scamproof.app/invite/{st.session_state.squad['invite_code']}",
        disabled=True
    )

    # Make add-member feel cleaner (input + button row)
    c1, c2 = st.columns([1.2, 1])
    with c1:
        nm = st.text_input("Add teammate name", label_visibility="collapsed", placeholder="Add teammate name")
    with c2:
        add = st.button("Add member", type="primary", use_container_width=True)

    if add and nm.strip():
        st.session_state.squad["members"].append(nm.strip())
        st.success(f"Added {nm.strip()}")

    st.markdown("**Members**")
    st.write(", ".join(st.session_state.squad["members"]) if st.session_state.squad["members"] else "—")

    st.markdown("### Decision readiness")
    for k in list(st.session_state.squad["checklist"].keys()):
        st.session_state.squad["checklist"][k] = st.checkbox(k, st.session_state.squad["checklist"][k])

    done = sum(st.session_state.squad["checklist"].values())
    total = len(st.session_state.squad["checklist"])
    st.progress(done / max(total, 1))
    st.caption(f"{done}/{total} complete")