import streamlit as st
from utils import init_state, load_listings

init_state()
from utils import get_listings
df = get_listings()
st.markdown("## 1) Onboarding → Squad")

if st.session_state.role != "student":
    st.info("Switch to Student role from Home (log out and log in as Student).")
    st.stop()

left, right = st.columns([1.2, 1])

with left:
    st.markdown("### Your constraints")
    budget = st.slider("Monthly budget (CAD)", 500, 2500, int(st.session_state.profile["budget"]), 25)
    move_in = st.date_input("Move-in date", st.session_state.profile["move_in"])
    areas = st.multiselect("Preferred areas", sorted(df["area"].unique().tolist()),
                           default=st.session_state.profile["areas"] or [])
    commute = st.slider("Max commute (minutes)", 5, 90, int(st.session_state.profile["commute_max"]), 5)
    roommates = st.selectbox("Roommate count", [1,2,3,4], index=[1,2,3,4].index(st.session_state.profile["roommates"]))

    st.session_state.profile.update({
        "budget": budget,
        "move_in": move_in,
        "areas": areas,
        "commute_max": commute,
        "roommates": roommates,
    })

    st.session_state.squad["checklist"]["Set budget + move-in date"] = True
    st.session_state.squad["checklist"]["Pick areas"] = bool(areas)

with right:
    st.markdown("### Squad")
    st.session_state.squad["name"] = st.text_input("Squad name", st.session_state.squad["name"])
    st.text_input("Invite link (demo)", f"https://scamproof.app/invite/{st.session_state.squad['invite_code']}", disabled=True)

    nm = st.text_input("Add teammate name", "")
    if st.button("Add member", type="primary", use_container_width=True):
        if nm.strip():
            st.session_state.squad["members"].append(nm.strip())
            st.success(f"Added {nm.strip()}")

    st.markdown("**Members**")
    st.write(", ".join(st.session_state.squad["members"]))

    st.markdown("### Decision readiness")
    for k in list(st.session_state.squad["checklist"].keys()):
        st.session_state.squad["checklist"][k] = st.checkbox(k, st.session_state.squad["checklist"][k])

    done = sum(st.session_state.squad["checklist"].values())
    total = len(st.session_state.squad["checklist"])
    st.progress(done/total)
    st.caption(f"{done}/{total} complete")