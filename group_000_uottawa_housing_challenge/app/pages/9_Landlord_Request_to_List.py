import streamlit as st
import pandas as pd
from datetime import datetime
from utils import init_state, get_listings, set_listings, trust_badge

init_state()
st.markdown("## Landlord Profile")

if st.session_state.role != "landlord":
    st.info("Log out and log in as **Landlord** to access this page.")
    st.stop()

p = st.session_state.landlord_profile
df = get_listings()

if not p["company_name"].strip():
    st.warning("No landlord profile yet. Go to **Landlord Onboarding** first.")
    st.stop()

# Profile header
with st.container(border=True):
    st.markdown(f"### {p['company_name']}")
    st.caption(f"Contact: {p.get('contact_name','')} • {p.get('email','')} • {p.get('phone','')}")
    ver = []
    ver.append("✅ Email" if p["email_verified"] else "❌ Email")
    ver.append("✅ Phone" if p["phone_verified"] else "❌ Phone")
    ver.append("✅ Card on file" if p["card_on_file"] else "❌ Card on file")
    ver.append("✅ ID" if p["id_on_file"] else "❌ ID")
    st.write(" | ".join(ver))
    st.caption(f"Created: {p.get('created_at') or '(demo)'}")

# Filter listings owned by this landlord name (simple MVP)
owned = df[df["landlord"].str.lower() == p["company_name"].strip().lower()].copy()

st.markdown("### Your listings")
if owned.empty:
    st.info("No listings found for this landlord name in data/listings.csv.")
    st.caption("MVP tip: set your Company/Landlord name to match an existing listing landlord value (e.g., 'Private Landlord').")
else:
    for _, row in owned.sort_values("id").iterrows():
        with st.container(border=True):
            st.markdown(f"**{row['title']}** — {row['area']} — **${int(row['price'])}/mo**")
            st.markdown(trust_badge(row["verified_at"]), unsafe_allow_html=True)

            c1, c2 = st.columns([1, 1])
            with c1:
                if st.button("Confirm availability (re-verify)", key=f"reverify_{row['id']}", type="primary", use_container_width=True):
                    df.loc[df["id"] == row["id"], "verified_at"] = pd.Timestamp.now().normalize()
                    set_listings(df)
                    st.success("Availability confirmed. Badge refreshed to Verified (demo).")
                    st.rerun()
            with c2:
                if st.button("Send reconfirmation email (demo)", key=f"email_{row['id']}", use_container_width=True):
                    st.info("Sent email: 'Please reconfirm availability' (demo).")