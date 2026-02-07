import streamlit as st
from app.utils import (
    inject_css, init_state, get_listings, ensure_selected_listing,
    compute_price_band, trust_badge, trust_status,
    listing_meta, is_visible_to_students
)

inject_css()
init_state()
df = get_listings()
st.markdown(
    """
    <div class="hero">
      <div class="hero-title">Verified Listings</div>
      <div class="hero-sub">Browse listings that passed verification. Trust decays automatically.</div>
    </div>
    """,
    unsafe_allow_html=True
)
st.write("")
st.write("")

if st.session_state.role != "student":
    st.info("Switch to Student role from Home (log out and log in as Student).")
    st.stop()

# Funnel visibility
visible = df[df.apply(is_visible_to_students, axis=1)].copy()
if visible.empty:
    st.warning("No visible listings yet. (Landlord listings must be Verified/Stale + have photos.)")
    st.stop()

# Filters (clean + minimal)
c1, c2, c3 = st.columns([1, 1, 1])
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
    st.warning("No visible listings match. Try changing filters.")
    st.stop()

ensure_selected_listing(f)

left, right = st.columns([1.25, 1])

with left:
    st.markdown("### Results")
    for _, row in f.sort_values("price").iterrows():
        band_lo, band_hi = compute_price_band(df, row["area"])
        selected = int(row["id"]) == int(st.session_state.selected_listing_id)
        meta = listing_meta(int(row["id"]))

        with st.container(border=True):
            st.markdown(f"**{row['title']}**")
            st.markdown(
                f"<span class='muted'>{row['area']} • {row['beds']} bed • {row['landlord']}</span>",
                unsafe_allow_html=True
            )

            st.caption(f"📍 {row['area']} • {meta['address']}")
            st.caption(f"📅 Available: {meta['available_date']} • Lease: {meta['lease_length']}")
            st.caption(f"🖼️ Photos on file: {meta['photo_count']}")

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
    meta = listing_meta(int(sel["id"]))
    band_lo, band_hi = compute_price_band(df, sel["area"])
    status, _ = trust_status(sel["verified_at"])

    with st.container(border=True):
        st.markdown(f"**{sel['title']}**")
        st.markdown(
            f"<span class='muted'>{sel['area']} • {sel['beds']} bed • {sel['landlord']}</span>",
            unsafe_allow_html=True
        )

        st.caption(f"📍 {sel['area']} • {meta['address']}")
        st.caption(f"📅 Available: {meta['available_date']} • Lease: {meta['lease_length']}")
        st.caption(f"🖼️ Photos on file: {meta['photo_count']}")

        st.markdown(f"### ${int(sel['price'])}/mo")

        st.markdown("**Proof-of-Availability**")
        st.markdown(trust_badge(sel["verified_at"]), unsafe_allow_html=True)

        st.markdown("**Price sanity band**")
        st.write(f"Typical: **${band_lo}–${band_hi}**")

        st.markdown("**Why this is visible**")
        st.write(f"- Status: **{status}** (decays over time)")
        st.write("- Passed funnel: photos uploaded + not pending")

        st.info("Next: go to **Student Safe Chat** to contact landlord in-platform and trigger the scam interrupt.")