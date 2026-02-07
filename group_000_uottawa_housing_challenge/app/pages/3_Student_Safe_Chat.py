import streamlit as st
from datetime import datetime
from app.utils import init_state, load_listings, risk_detect

init_state()
from app.utils import get_listings
df = get_listings()

st.markdown("## 3) Safe Messaging (Scam Interrupt)")

if st.session_state.role != "student":
    st.info("Switch to Student role from Home (log out and log in as Student).")
    st.stop()

if st.session_state.selected_listing_id is None:
    st.warning("Select a listing in Browse first.")
    st.stop()

listing = df[df["id"] == int(st.session_state.selected_listing_id)].iloc[0]

left, right = st.columns([1.35, 1])

with left:
    with st.container(border=True):
        st.markdown(f"### Chat about: **{listing['title']}**")
        st.caption("All messages stay in-platform. We interrupt risky moments in real time.")

        if st.session_state.chat:
            for msg in st.session_state.chat[-14:]:
                who = "🧑‍🎓 You" if msg["sender"] == "you" else "🏠 Landlord"
                st.markdown(f"**{who}:** {msg['text']}")
                st.caption(msg["ts"])
        else:
            st.caption("No messages yet — try a simulated scam message to trigger the interrupt.")

        st.divider()

        colA, colB, colC = st.columns(3)
        with colA:
            user_text = st.text_input("Your message", "")
            if st.button("Send", type="primary", use_container_width=True):
                if user_text.strip():
                    st.session_state.chat.append({"sender":"you","text":user_text.strip(),"ts":datetime.now().strftime("%H:%M:%S")})
                    st.rerun()

        with colB:
            if st.button("Simulate: deposit before viewing", use_container_width=True):
                scam = "To hold it, send the deposit before viewing. Many people are interested."
                st.session_state.chat.append({"sender":"landlord","text":scam,"ts":datetime.now().strftime("%H:%M:%S")})
                st.rerun()

        with colC:
            if st.button("Simulate: WhatsApp + wire", use_container_width=True):
                scam = "Message me on WhatsApp and we can do a wire transfer today only."
                st.session_state.chat.append({"sender":"landlord","text":scam,"ts":datetime.now().strftime("%H:%M:%S")})
                st.rerun()

        # Detect risk on last landlord message
        if st.session_state.chat and st.session_state.chat[-1]["sender"] == "landlord":
            last = st.session_state.chat[-1]["text"]
            score, hits = risk_detect(last)

            if hits:
                excerpt = (last[:70] + "…") if len(last) > 70 else last
                st.session_state.risk_timeline.append({
                    "time": datetime.now().strftime("%H:%M"),
                    "event": "Scam pattern detected",
                    "score": score,
                    "excerpt": excerpt
                })

                st.markdown("<div class='interrupt'>", unsafe_allow_html=True)
                st.markdown("### ⚠️ Students are often scammed at this step.")
                st.write("We recommend booking a viewing before paying anything.")
                st.write(f"**Risk score:** {score}/100")
                st.markdown("**Triggers:**")
                for h in hits:
                    st.write(f"- **{h['name']}** — {h['why']}")
                a1, a2, a3 = st.columns(3)
                with a1:
                    if st.button("Request viewing", type="primary", use_container_width=True):
                        st.session_state.squad["checklist"]["Book at least 1 viewing"] = True
                        st.success("Viewing requested (demo).")
                with a2:
                    if st.button("Ask for ID", use_container_width=True):
                        st.info("Sent request for ID / proof of ownership (demo).")
                with a3:
                    if st.button("Report", use_container_width=True):
                        st.warning("Report logged (demo). Consider generating Incident Pack.")
                st.markdown("</div>", unsafe_allow_html=True)

with right:
    st.markdown("### Explainability + Incident Pack")
    with st.container(border=True):
        st.caption("Risk events are logged in the sidebar timeline with the exact pattern that triggered it.")
        if st.button("Generate Incident Pack", use_container_width=True):
            st.session_state.incident_pack["ready"] = True
            st.success("Incident Pack ready (demo). Go to Safety & Lease page.")