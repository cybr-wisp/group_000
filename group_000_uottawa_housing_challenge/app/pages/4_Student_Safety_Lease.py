import streamlit as st
from app.utils import init_state, load_listings, lease_scan

init_state()
df = load_listings("data/listings.csv")

st.markdown("## 4) Viewing + Lease Safety Check")

if st.session_state.role != "student":
    st.info("Switch to Student role from Home (log out and log in as Student).")
    st.stop()

if st.session_state.selected_listing_id is None:
    st.warning("Select a listing in Browse first.")
    st.stop()

listing = df[df["id"] == int(st.session_state.selected_listing_id)].iloc[0]
left, right = st.columns([1.25, 1])

with left:
    st.markdown(f"### Viewing checklist — **{listing['title']}**")
    for k in list(st.session_state.viewing_checklist.keys()):
        st.session_state.viewing_checklist[k] = st.checkbox(k, st.session_state.viewing_checklist[k])

    if all(st.session_state.viewing_checklist.values()):
        st.success("✅ Checklist complete — you can mark this as Ready to Rent.")
    else:
        st.info("Complete all items before marking 'Ready to Rent'.")

    st.divider()

    st.markdown("### Lease scan (MVP rules)")
    st.caption("For MVP: paste lease text. (No PDF parsing.)")
    lease_text = st.text_area("Paste lease text here", height=170)

    if st.button("Run Lease Scan", type="primary"):
        if not lease_text.strip():
            st.warning("Paste lease text to scan.")
        else:
            flags = lease_scan(lease_text)
            st.session_state.squad["checklist"]["Upload lease draft (optional)"] = True
            if flags:
                st.warning("Potential issues found:")
                for f in flags:
                    st.write(f"**• {f['name']}**")
                    st.caption(f["tip"])
            else:
                st.success("No obvious flags found by MVP rules. Still review carefully.")

with right:
    st.markdown("### Final Safety Check (filters → matched listings)")
    with st.container(border=True):
        st.write("For the demo, this can simply confirm their constraints and show a shortlist.")
        st.write(f"**Budget:** ${st.session_state.profile['budget']} | **Areas:** {', '.join(st.session_state.profile['areas'] or ['(none)'])}")
        st.write(f"**Move-in:** {st.session_state.profile['move_in']} | **Roommates:** {st.session_state.profile['roommates']}")

        # Lightweight "matches"
        matches = df[df["price"] <= int(st.session_state.profile["budget"])].head(12)
        st.markdown(f"**These {len(matches)} listings match your situation.**")
        for _, r in matches.iterrows():
            st.write(f"• {r['title']} — {r['area']} — ${int(r['price'])}")

    st.markdown("### Incident Pack (one-click generator)")
    with st.container(border=True):
        if not st.session_state.incident_pack["ready"]:
            st.caption("Generate it from Safe Chat when something feels off.")
        else:
            st.success("📦 Incident Pack: Ready (demo)")
            for k in list(st.session_state.incident_pack["items"].keys()):
                st.session_state.incident_pack["items"][k] = st.checkbox(
                    k, st.session_state.incident_pack["items"][k]
                )
            if all(st.session_state.incident_pack["items"].values()):
                st.success("✅ Pack complete (in a real app: export ZIP / share link).")
            else:
                st.info("Keep collecting evidence — this prevents 'unpreventable' losses.")