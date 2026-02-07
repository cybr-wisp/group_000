import streamlit as st
import pandas as pd
from app.utils import init_state, load_listings

init_state()
df = load_listings("data/listings.csv")

st.markdown("## Landlord — Confirm Availability")

if st.session_state.role != "landlord":
    st.info("Switch to Landlord role from Home (log out and log in as Landlord).")
    st.stop()

st.caption("MVP: reconfirmation restores trust. In demo, we just show the concept.")

listing_id = st.selectbox("Select listing (demo)", df["id"].tolist())
row = df[df["id"] == int(listing_id)].iloc[0]
st.write(f"**{row['title']}** — {row['area']} — ${int(row['price'])}")

if st.button("Confirm availability", type="primary"):
    st.success("Availability confirmed (demo). In real app: updates verified_at → badge becomes Verified.")