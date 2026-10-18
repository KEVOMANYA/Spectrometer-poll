import streamlit as st
import pandas as pd
import hashlib
import os
import time
from datetime import datetime, timezone
from supabase import create_client, Client

st.set_page_config(page_title="SPH 401 Project Poll", page_icon="🔬", layout="centered")

TITLE = "SPH 401 Atomic Spectrometer Project Poll"
OPTIONS = [
    "Option 1: Lecturer-guided design — lecturer guides design/construction; students handle data acquisition and analysis.",
    "Option 2: Student-led design — students design/build; lecturer guides data acquisition and analysis.",
    "Option 3: Collaborative approach — design/construction together; students collect and analyse data with lecturer support.",
    "Option 4: Fully independent project — students handle all stages independently, asking for clarification when needed.",
    "Option 5: Simplified design and guided practical sessions — use a standard design and focus on spectra, calibration, analysis, and identifying elements."
]

def supabase_client() -> Client:
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_ANON_KEY"]
    return create_client(url, key)

def digest(code: str) -> str:
    # Codes should be random, high-entropy strings; only the digest is stored.
    return hashlib.sha256(code.strip().upper().encode("utf-8")).hexdigest()

st.title("🔬 " + TITLE)
st.write("Please select ONE approach. The aim is to agree on a fair and manageable arrangement while meeting the learning objectives.")
st.info("Do not enter your name or admission number. Enter only your assigned one-time voting code. Your selected option is stored without your code or identity.")

try:
    supabase = supabase_client()
except Exception:
    st.error("The poll database is not configured yet. The lecturer must finish the setup steps in the README before voting opens.")
    st.stop()

# Public poll status is read from a table with RLS/policies configured in the setup guide.
try:
    status_result = supabase.table("poll_settings").select("status").eq("id", 1).single().execute()
    poll_status = status_result.data["status"]
except Exception:
    st.error("The poll database tables or permissions are not configured correctly yet.")
    st.stop()

if poll_status != "OPEN":
    st.warning("Voting is currently closed.")
else:
    with st.form("vote_form"):
        code = st.text_input("Your one-time voting code", max_chars=8, help="Enter the 8-character code given to you.")
        choice = st.radio("Which approach do you prefer?", OPTIONS, index=None)
        submitted = st.form_submit_button("Submit my vote", use_container_width=True)

    if submitted:
        code = code.strip().upper()
        if len(code) != 8 or not code.isalnum():
            st.error("Enter a valid 8-character voting code.")
        elif choice is None:
            st.error("Please select one option.")
        else:
            try:
                code_hash = digest(code)
                # Atomic RPC function validates unused code, records anonymous vote,
                # and marks the code used in a single database transaction.
                result = supabase.rpc("cast_vote", {
                    "p_code_hash": code_hash,
                    "p_option": choice
                }).execute()
                if result.data == "OK":
                    st.success("Your vote has been recorded. Thank you!")
                    st.rerun()
                elif result.data == "USED":
                    st.error("This voting code has already been used.")
                elif result.data == "INVALID":
                    st.error("That voting code is not valid. Check it with the class representative.")
                elif result.data == "CLOSED":
                    st.error("Voting has closed.")
                else:
                    st.error("Your vote could not be recorded. Please contact the class representative.")
            except Exception:
                st.error("The vote could not be submitted. Please try again later or contact the lecturer.")

st.divider()
st.subheader("Poll results")
st.caption("Results are aggregate totals only.")
try:
    rows = supabase.table("poll_results").select("option_text,vote_count").execute().data
    total = sum(int(r["vote_count"]) for r in rows)
    st.metric("Total votes", total)
    if total:
        df = pd.DataFrame([{"Option": r["option_text"], "Votes": int(r["vote_count"])} for r in rows])
        st.bar_chart(df.set_index("Option"))
        for r in sorted(rows, key=lambda x: int(x["vote_count"]), reverse=True):
            count = int(r["vote_count"])
            pct = count * 100 / total if total else 0
            st.write(f"**{count} votes ({pct:.1f}%)** — {r['option_text']}")
    else:
        st.write("No votes have been recorded yet.")
except Exception:
    st.caption("Results will appear once the poll database setup is complete.")
