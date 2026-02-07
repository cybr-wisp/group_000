import streamlit as st
import numpy as np
from utils import inject_css, init_state, load_listings, render_risk_timeline_sidebar

# ✅ MUST be at top-level (before any UI calls)
st.set_page_config(
    page_title="GEEGEELease",
    page_icon="🏠",
    layout="wide"
)

# -------------------------------------------------
# Page-specific CSS: clean white + deep red accents
# -------------------------------------------------
st.markdown(
    """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&display=swap');

:root{
  --bg: #ffffff;
  --text: #111827;
  --muted: #6b7280;
  --card: #f8fafc;
  --border: #e5e7eb;
  --accent: #8B1E3F;      /* deep red */
  --accentHover: #741835;
  --soft: rgba(139,30,63,0.08);
  --soft2: rgba(139,30,63,0.04);
}

.stApp{
  background: var(--bg);
  color: var(--text);
  font-family: Inter, sans-serif;
}

.block-container{
  max-width: 1200px;
  padding-top: 2.2rem;
}

/* Headings */
h1,h2,h3,h4{
  color: var(--text) !important;
  font-weight: 900;
  letter-spacing: -0.02em;
}
p, li, .stMarkdown { color: var(--text) !important; }
.stCaption, small { color: var(--muted) !important; }

/* Hero */
.hero{
  background: linear-gradient(135deg, var(--soft), var(--soft2));
  border: 1px solid var(--border);
  border-radius: 20px;
  padding: 18px 20px;
  margin-bottom: 18px;
}
.hero-title{
  font-size: 36px;
  font-weight: 950;
  letter-spacing: -0.03em;
}
.hero-sub{
  margin-top: 6px;
  color: var(--muted) !important;
  font-weight: 500;
}

/* Column cards */
[data-testid="column"] > div{
  background: var(--card);
  border: 1px solid var(--border);
  border-radius: 20px;
  padding: 18px;
}

/* Inputs */
input, textarea, select{
  background: #ffffff !important;
  color: var(--text) !important;
  border-radius: 12px !important;
  border: 1px solid var(--border) !important;
}

/* Radios (BaseWeb) */
div[data-baseweb="radio"] span{
  color: var(--text) !important;
}
div[data-baseweb="radio"] input:checked + div{
  border-color: var(--accent) !important;
}
div[data-baseweb="radio"] div[role="radio"]{
  border-color: var(--border) !important;
}

/* Buttons */
.stButton > button{
  background: var(--accent) !important;
  color: #fff !important;
  border: none !important;
  border-radius: 12px !important;
  font-weight: 800 !important;
  padding: 0.65rem 1rem !important;
}
.stButton > button:hover{
  background: var(--accentHover) !important;
}
.stButton > button:focus{
  box-shadow: 0 0 0 4px rgba(139,30,63,0.20) !important;
}

/* Make "secondary" (non-primary) buttons subtle */
.stButton > button[kind="secondary"]{
  background: #ffffff !important;
  color: var(--text) !important;
  border: 1px solid var(--border) !important;
}
.stButton > button[kind="secondary"]:hover{
  background: #f3f4f6 !important;
}

/* Feature card */
.feature-card{
  background: #ffffff;
  border: 1px solid var(--border);
  border-radius: 20px;
  padding: 16px 16px 14px 16px;
  box-shadow: 0 1px 0 rgba(0,0,0,0.02);
}
.pill{
  display: inline-block;
  font-size: 12px;
  font-weight: 800;
  color: var(--accent);
  background: rgba(139,30,63,0.10);
  border: 1px solid rgba(139,30,63,0.18);
  padding: 6px 10px;
  border-radius: 999px;
}
.muted{ color: var(--muted) !important; font-weight: 500; }
.dots{ color: rgba(17,24,39,0.35); font-weight: 800; letter-spacing: 2px; }

/* Phone mock */
.phone{
  background: linear-gradient(180deg, #ffffff, #fbfbfc);
  border: 1px solid var(--border);
  border-radius: 26px;
  padding: 16px;
  position: relative;
}
.phone-notch{
  width: 90px;
  height: 6px;
  border-radius: 999px;
  background: rgba(17,24,39,0.10);
  margin: 0 auto 12px auto;
}
.interrupt{
  border: 1px solid rgba(139,30,63,0.25);
  background: rgba(139,30,63,0.08);
  border-radius: 16px;
  padding: 12px;
}

/* Sidebar cleanup */
section[data-testid="stSidebar"]{
  background: #ffffff;
  border-right: 1px solid var(--border);
  st.sidebar.markdown("## 🏠 GEEGEELease")
}
</style>
""",
    unsafe_allow_html=True
)


def login_screen():
    st.markdown(
        """
        <div class="hero">
            <div class="hero-title">🏠 GEEGEELease</div>          <div class="hero-sub">
            Verified listings + real-time scam interruption — built for uOttawa students under pressure.
          </div>
        </div>
        """,
        unsafe_allow_html=True
    )

    left, right = st.columns([1.15, 1])

    with left:
        st.markdown("### Create your demo account")

        role = st.selectbox("I am a…", ["student", "landlord"], format_func=lambda x: x.title())
        username = st.text_input("Username", placeholder="e.g., marie_sindhu")
        email = st.text_input("uOttawa email", placeholder="name@uottawa.ca")

        intent = st.radio(
            "What are you here to do?",
            ["Rent a place", "Find roommates to split rent"],
            horizontal=True
        )

        st.caption("Verification: MVP demo uses an OTP code (can be wired to Outlook later).")

        # init OTP state
        st.session_state.setdefault("otp_sent", False)
        st.session_state.setdefault("otp_code", None)
        st.session_state.setdefault("email_verified", False)

        c1, c2 = st.columns([1, 1])

        with c1:
            if st.button("Send verification code", use_container_width=True):
                if not email.lower().endswith("@uottawa.ca"):
                    st.error("Use a valid uOttawa email (must end with @uottawa.ca).")
                else:
                    st.session_state.otp_code = str(np.random.randint(100000, 999999))
                    st.session_state.otp_sent = True
                    st.info("Code sent via Outlook (demo). Enter the 6-digit code below.")
                    st.caption(f"(Demo code: {st.session_state.otp_code})")

        with c2:
            otp = st.text_input("Enter 6-digit code", placeholder="123456", label_visibility="visible")
            if st.button("Verify email", type="primary", use_container_width=True):
                if not st.session_state.otp_sent:
                    st.error("Click 'Send verification code' first.")
                elif otp.strip() == (st.session_state.otp_code or ""):
                    st.session_state.email_verified = True
                    st.success("Email verified ✅")
                else:
                    st.error("Incorrect code. Try again.")

        st.divider()
        pw = st.text_input("Demo password", type="password", placeholder="demo")

        if st.button("Enter ScamProof", type="primary", use_container_width=True):
            if pw.strip() != "demo":
                st.error("Wrong password. Try: demo")
            elif not username.strip():
                st.error("Please enter a username.")
            elif not email.lower().endswith("@uottawa.ca"):
                st.error("Please enter a uOttawa email (name@uottawa.ca).")
            elif not st.session_state.email_verified:
                st.error("Please verify your email (OTP) to continue.")
            else:
                st.session_state.auth = True
                st.session_state.role = role
                st.session_state.setdefault("account", {})
                st.session_state.account = {
                    "username": username.strip(),
                    "email": email.strip(),
                    "intent": intent,
                }
                st.success("Logged in ✅ Use the left sidebar pages.")
                st.rerun()

    with right:
        st.markdown("### MVP carousel")

        slides = [
            {"pill": "Feature 1", "title": "Trust that decays",
             "desc": "Verified → Stale → Unverified (auto-hidden). No more ‘verified once’ forever.", "art": "🕒"},
            {"pill": "Feature 2", "title": "Safe Chat Interrupt",
             "desc": "Detect deposit-before-viewing, urgency, off-platform payment — interrupt in the moment.", "art": "🚨"},
            {"pill": "Feature 3", "title": "Incident Pack Generator",
             "desc": "One click generates the scam evidence checklist + ‘pack ready’ screen.", "art": "📦"},
            {"pill": "Journey", "title": "Guided student flow",
             "desc": "Onboard → Browse → Chat → Viewing/Lease Safety Check (end-to-end demo).", "art": "🧭"},
        ]

        idx = st.radio(
            "carousel",
            options=list(range(len(slides))),
            format_func=lambda i: f"{slides[i]['pill']}",
            label_visibility="collapsed",
            horizontal=True
        )
        s = slides[idx]

        # Clean dots (no weird math)
        dots = "".join(["● " if i == idx else "○ " for i in range(len(slides))]).strip()

        st.markdown(
            f"""
            <div class="feature-card">
              <span class="pill">{s['pill']}</span>
              <div style="font-weight:950;font-size:1.25rem;margin-top:.55rem;">
                {s['art']} {s['title']}
              </div>
              <div class="muted" style="margin-top:.40rem;">{s['desc']}</div>
              <div class="dots" style="margin-top:.9rem;">{dots}</div>
            </div>
            """,
            unsafe_allow_html=True
        )

        st.write("")
        st.markdown(
            """
            <div class="phone">
              <div class="phone-notch"></div>
              <div style="font-weight:900;font-size:1.05rem;">Safe Mode Preview</div>
              <div class="muted" style="margin-top:.25rem;">Watch the interrupt happen live.</div>
              <div style="margin-top:.75rem;padding:.75rem;border-radius:16px;border:1px solid rgba(0,0,0,.08);background:rgba(0,0,0,.02);">
                <div style="font-weight:800;">Landlord</div>
                <div class="muted">Send deposit now to hold it — many people interested.</div>
              </div>
              <div class="interrupt" style="margin-top:.75rem;">
                <div style="font-weight:950;">⚠️ Scam interrupt</div>
                <div class="muted">Book a viewing first. Don’t pay off-platform.</div>
              </div>
            </div>
            """,
            unsafe_allow_html=True
        )


def main():
    inject_css()
    init_state()

    # load listings so sidebar timeline works after login
    df = load_listings("data/listings.csv")

    # Sidebar brand
    st.sidebar.markdown("## ScamProof")
    st.sidebar.caption("Safety-by-design housing journey")

    # If not logged in, show login screen and stop
    if not st.session_state.auth:
        login_screen()
        return

    # Logged-in sidebar info
    acct = st.session_state.get("account", {})
    st.sidebar.markdown(f"**User:** {acct.get('username','(demo)')}")
    st.sidebar.markdown(f"**Role:** {st.session_state.role.title()}")

    if st.sidebar.button("Log out"):
        st.session_state.auth = False
        st.session_state.risk_timeline = []
        st.session_state.chat = []
        st.session_state.email_verified = False
        st.session_state.otp_sent = False
        st.session_state.otp_code = None
        st.rerun()

    st.sidebar.markdown("---")
    render_risk_timeline_sidebar(df)

    # Main logged-in home
    st.markdown("## ✅ Logged in")
    st.write("Use the **Pages** menu in the sidebar to navigate the MVP.")
    st.caption("Tip: start with **Student Browse** → **Student Safe Chat** to trigger the scam interrupt.")


if __name__ == "__main__":
    main()