import streamlit as st
import pandas as pd
from app.utils import init_state, get_listings, set_listings, trust_badge, listing_meta, mark_verified

init_state()
st.markdown("## Landlord Profile")
st.caption("Listings are created through a verification funnel — not a free posting feed.")

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

    missing = []
    if not p["email_verified"]: missing.append("Email verification")
    if not p["phone_verified"]: missing.append("Phone verification")
    if not p["card_on_file"]: missing.append("Card on file")
    if missing:
        st.warning("To make listings visible you must complete: " + ", ".join(missing))

# Filter listings owned by this landlord name (simple MVP)
owned = df[df["landlord"].str.lower() == p["company_name"].strip().lower()].copy()

st.markdown("### Your listings")
if owned.empty:
    st.info("No listings found for this landlord name in data/listings.csv.")
    st.caption("MVP tip: set your Company/Landlord name to match an existing listing landlord value (e.g., 'Private Landlord').")
else:
    for _, row in owned.sort_values("id").iterrows():
        meta = listing_meta(int(row["id"]))

        with st.container(border=True):
            st.markdown(f"**{row['title']}** — {row['area']} — **${int(row['price'])}/mo**")
            st.markdown(trust_badge(row["verified_at"]), unsafe_allow_html=True)
            st.caption(f"📍 {meta.get('address','—')} • 📅 {meta.get('available_date','—')} • Lease: {meta.get('lease_length','—')}")
            st.caption("📷 Photos: " + ("✅ Uploaded" if meta.get("photos_ok") else "❌ Missing (required)"))
            st.caption("📝 Lease draft: " + ("✅ Uploaded" if meta.get("lease_uploaded") else "— Not uploaded"))

            c1, c2 = st.columns([1, 1])

            with c1:
                if st.button(
                    "Confirm availability (re-verify)",
                    key=f"reverify_{row['id']}",
                    type="primary",
                    use_container_width=True
                ):
                    # Funnel requirement before visibility
                    if not (p["email_verified"] and p["phone_verified"] and p["card_on_file"]):
                        st.error("Complete verification first: email + phone + card on file.")
                        st.stop()
                    if not meta.get("photos_ok", False):
                        st.error("This listing is missing photos. Photos are mandatory to be visible.")
                        st.stop()

                    df.loc[df["id"] == row["id"], "verified_at"] = pd.Timestamp.now().normalize()
                    set_listings(df)
                    mark_verified(int(row["id"]))
                    st.success("Availability confirmed. Listing is now ✅ visible to students.")
                    st.rerun()

            with c2:
                if st.button("Send reconfirmation email (demo)", key=f"email_{row['id']}", use_container_width=True):
                    st.info("Sent email: 'Please reconfirm availability' (demo).")