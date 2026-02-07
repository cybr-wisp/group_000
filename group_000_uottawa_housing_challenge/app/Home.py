import streamlit as st
import numpy as np
from utils import inject_css, init_state, load_listings, render_risk_timeline_sidebar

# ✅ MUST be at top-level (before any UI calls)
st.set_page_config(page_title="ScamProof Housing", page_icon="🛡️", layout="wide")


def login_screen():
    st.markdown(
        """
        <div class="hero">
          <div class="hero-title">🛡️ ScamProof Housing</div>
          <div class="hero-sub">
            Verified listings + real-time scam interruption — built for uOttawa students under pressure.
          </div>
        </div>
        """,
        unsafe_allow_html=True
    )
    st.write("")

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
                    # For demo speed you can optionally show it:
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

        st.markdown("---")
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
            {
                "pill": "Feature 1",
                "title": "Trust that decays",
                "desc": "Verified → Stale → Unverified (auto-hidden). No more ‘verified once’ forever.",
                "art": "🕒"
            },
            {
                "pill": "Feature 2",
                "title": "Safe Chat Interrupt",
                "desc": "Detect deposit-before-viewing, urgency, off-platform payment — interrupt in the moment.",
                "art": "🚨"
            },
            {
                "pill": "Feature 3",
                "title": "Incident Pack Generator",
                "desc": "One click generates the scam evidence checklist + ‘pack ready’ screen.",
                "art": "📦"
            },
            {
                "pill": "Journey",
                "title": "Guided student flow",
                "desc": "Onboard → Browse → Chat → Viewing/Lease Safety Check (end-to-end demo).",
                "art": "🧭"
            },
        ]

        idx = st.radio(
            "carousel",
            options=list(range(len(slides))),
            format_func=lambda i: f"{slides[i]['pill']}",
            label_visibility="collapsed",
            horizontal=True
        )
        s = slides[idx]
        st.markdown(
            f"""
            <div class="feature-card">
              <span class="pill">{s['pill']}</span>
              <div style="font-weight:950;font-size:1.25rem;margin-top:.55rem;">
                {s['art']} {s['title']}
              </div>
              <div class="muted" style="margin-top:.40rem;">{s['desc']}</div>
              <div class="dots" style="margin-top:.9rem;">{"● " * (idx+1)}{"○ " * (len(slides)-idx-idx-1 if False else (len(slides)-idx-1))}</div>
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