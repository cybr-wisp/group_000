import streamlit as st
from datetime import datetime
from app.utils import init_state

init_state()

st.markdown("## Landlord Onboarding")

if st.session_state.role != "landlord":
    st.info("Log out and log in as **Landlord** to access this page.")
    st.stop()

p = st.session_state.landlord_profile

with st.container(border=True):
    st.markdown("### Create your landlord profile")
    p["company_name"] = st.text_input("Company / Landlord name", p["company_name"], placeholder="e.g., Maple Rentals or Private Landlord")
    p["contact_name"] = st.text_input("Contact name", p["contact_name"], placeholder="e.g., Alex Chen")
    p["email"] = st.text_input("Email", p["email"], placeholder="alex@email.com")
    p["phone"] = st.text_input("Phone", p["phone"], placeholder="(613) 555-1234")

    st.divider()
    st.markdown("### Verification (demo)")
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        p["email_verified"] = st.checkbox("Email verified", p["email_verified"])
    with c2:
        p["phone_verified"] = st.checkbox("Phone verified", p["phone_verified"])
    with c3:
        p["card_on_file"] = st.checkbox("Card on file", p["card_on_file"])
    with c4:
        p["id_on_file"] = st.checkbox("ID on file", p["id_on_file"])

    st.caption("In a real system, this step would run OTP + identity verification and store payment method securely.")

    if st.button("Complete onboarding", type="primary", use_container_width=True):
        if not p["company_name"].strip():
            st.error("Please enter a Company/Landlord name.")
        else:
            p["created_at"] = p["created_at"] or datetime.now().strftime("%Y-%m-%d %H:%M")
            st.success("Onboarding complete. Go to **Landlord Profile** next.")