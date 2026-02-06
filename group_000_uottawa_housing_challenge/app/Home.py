import streamlit as st
from utils import inject_css, init_state, load_listings, render_risk_timeline_sidebar

st.set_page_config(page_title="ScamProof Housing", page_icon="🛡️", layout="wide")

def login_screen():
    st.markdown("## 🛡️ ScamProof Housing")
    st.caption("Hackathon demo login. Use password **demo**.")

    c1, c2 = st.columns([1, 1])
    with c1:
        role = st.selectbox("Role", ["student", "landlord"], format_func=lambda x: x.title())
        pw = st.text_input("Password", type="password", placeholder="demo")
        if st.button("Login", type="primary", use_container_width=True):
            if pw.strip() == "demo":
                st.session_state.auth = True
                st.session_state.role = role
                st.success("Logged in (demo). Use the left sidebar pages.")
            else:
                st.error("Wrong password. Try: demo")

    with c2:
        st.markdown("### MVP features")
        st.write("✅ Trust decays (Verified → Stale → Unverified)")
        st.write("✅ Scam interrupt in messaging + explainable timeline")
        st.write("✅ Incident pack generator")
        st.write("✅ Guided student journey (4 pages)")

def main():
    inject_css()
    init_state()

    # Load listings once so sidebar can use it
    df = load_listings("data/listings.csv")

    # Sidebar header
    st.sidebar.markdown("## ScamProof")
    st.sidebar.caption("Safety-by-design housing journey")

    # Login gate
    if not st.session_state.auth:
        login_screen()
        return

    # Role indicator + logout
    st.sidebar.markdown(f"**Role:** {st.session_state.role.title()}")
    if st.sidebar.button("Log out"):
        st.session_state.auth = False
        st.session_state.risk_timeline = []
        st.session_state.chat = []
        st.session_state.incident_pack["ready"] = False
        st.rerun()

    st.sidebar.markdown("---")
    render_risk_timeline_sidebar(df)

    # Main home content
    st.markdown("## ✅ Logged in")
    st.write("Use the **Pages** menu in the sidebar to navigate the MVP.")
    st.caption("Tip: start with **Student Browse** → **Safe Chat** to trigger the scam interrupt.")

if __name__ == "__main__":
    main()