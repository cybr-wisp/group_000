import streamlit as st
from utils import init_state, load_listings, ensure_selected_listing, compute_price_band, trust_badge, trust_status

init_state()
from utils import get_listings
df = get_listings()

st.markdown("## 2) Verified Listings Browse")

if st.session_state.role != "student":
    st.info("Switch to Student role from Home (log out and log in as Student).")
    st.stop()

# Trust decay: only show Verified + Stale in browse
df["trust"] = df["verified_at"].apply(lambda x: trust_status(x)[0])
visible = df[df["trust"].isin(["Verified", "Stale"])].copy()

c1, c2, c3 = st.columns(3)
with c1:
    max_price = st.slider("Max price", 500, 2500, int(st.session_state.profile["budget"]), 25)
with c2:
    area = st.selectbox("Area", ["All"] + sorted(visible["area"].unique().tolist()))
with c3:
    beds = st.selectbox("Bedrooms", ["Any", "Studio (0)", "1", "2", "3+"])

f = visible[visible["price"] <= max_price]
if area != "All":
    f = f[f["area"] == area]
if beds != "Any":
    if beds == "Studio (0)":
        f = f[f["beds"] == 0]
    elif beds == "3+":
        f = f[f["beds"] >= 3]
    else:
        f = f[f["beds"] == int(beds)]

if f.empty:
    st.warning("No verified/stale listings match. Try changing filters.")
    st.stop()

ensure_selected_listing(f)

left, right = st.columns([1.25, 1])

with left:
    st.markdown("### Results")
    for _, row in f.sort_values("price").iterrows():
        band_lo, band_hi = compute_price_band(df, row["area"])
        selected = int(row["id"]) == int(st.session_state.selected_listing_id)

        with st.container(border=True):
            st.markdown(f"**{row['title']}**")
            st.markdown(f"<span class='muted'>{row['area']} • {row['beds']} bed • {row['landlord']}</span>", unsafe_allow_html=True)
            st.markdown(f"### ${int(row['price'])}/mo")
            st.markdown(trust_badge(row["verified_at"]), unsafe_allow_html=True)
            st.caption(f"Typical for {row['area']}: ${band_lo}–${band_hi}")

            if st.button("Select", key=f"sel_{row['id']}", type="primary" if selected else "secondary"):
                st.session_state.selected_listing_id = int(row["id"])
                st.session_state.squad["checklist"]["Shortlist 3 listings"] = True
                st.rerun()

with right:
    st.markdown("### Selected listing")
    sel = df[df["id"] == int(st.session_state.selected_listing_id)].iloc[0]
    band_lo, band_hi = compute_price_band(df, sel["area"])

    with st.container(border=True):
        st.markdown(f"**{sel['title']}**")
        st.markdown(f"<span class='muted'>{sel['area']} • {sel['beds']} bed • {sel['landlord']}</span>", unsafe_allow_html=True)
        st.markdown(f"### ${int(sel['price'])}/mo")
        st.markdown("**Proof-of-Availability**")
        st.markdown(trust_badge(sel["verified_at"]), unsafe_allow_html=True)
        st.markdown("**Price sanity band**")
        st.write(f"Typical: **${band_lo}–${band_hi}**")
        st.info("Next: go to **Student Safe Chat** to contact landlord in-platform.")