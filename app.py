import streamlit as st
import pandas as pd
import json
import hashlib
from pathlib import Path

st.set_page_config(page_title="SPH 401 Project Poll", page_icon="🔬", layout="centered")
TITLE = "SPH 401 Atomic Spectrometer Project Poll"
OPTIONS = [
    "Option 1: Lecturer-guided design — lecturer guides design/construction; students handle data acquisition and analysis.",
    "Option 2: Student-led design — students design/build; lecturer guides data acquisition and analysis.",
    "Option 3: Collaborative approach — design/construction together; students collect and analyse data with lecturer support.",
    "Option 4: Fully independent project — students handle all stages independently, asking for clarification when needed.",
    "Option 5: Simplified design and guided practical sessions — use a standard design and focus on spectra, calibration, analysis, and identifying elements."
]
DATA_FILE = Path("poll_data.json")

def load_data():
    if DATA_FILE.exists():
        try:
            return json.loads(DATA_FILE.read_text(encoding="utf-8"))
        except Exception:
            pass
    return {"status": "OPEN", "votes": [], "used_code_hashes": []}

def save_data(data):
    DATA_FILE.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

def hash_code(code):
    return hashlib.sha256(code.strip().upper().encode("utf-8")).hexdigest()

st.title("🔬 " + TITLE)
st.write("Please select ONE approach for completing the project. The aim is to agree on a fair and manageable arrangement while meeting the learning objectives.")
st.info("Do not enter your name or registration number. Use your assigned one-time voting code. Important: this starter version stores data in a local file, which is not reliable persistent storage on free cloud hosting.")

data = load_data()
if data["status"] != "OPEN":
    st.warning("Voting is currently closed.")
else:
    with st.form("vote_form"):
        code = st.text_input("Your one-time voting code", max_chars=20).strip().upper()
        choice = st.radio("Which approach do you prefer?", OPTIONS, index=None)
        submitted = st.form_submit_button("Submit my vote", use_container_width=True)
    if submitted:
        if not code:
            st.error("Enter your assigned voting code.")
        elif choice is None:
            st.error("Select one option.")
        else:
            code_hash = hash_code(code)
            current = load_data()
            if current["status"] != "OPEN":
                st.error("Voting has closed.")
            elif code_hash in current["used_code_hashes"]:
                st.error("This voting code has already been used.")
            else:
                current["used_code_hashes"].append(code_hash)
                current["votes"].append({"option": choice})
                save_data(current)
                st.success("Your vote has been recorded. Thank you!")
                st.rerun()

st.divider()
st.subheader("Poll results")
st.caption("Refresh the page to see current results.")
data = load_data()
counts = {option: 0 for option in OPTIONS}
for vote in data["votes"]:
    if vote.get("option") in counts:
        counts[vote["option"]] += 1
total = sum(counts.values())
st.metric("Total votes", total)
if total:
    results = pd.DataFrame([{"Option": option, "Votes": count} for option, count in counts.items()])
    st.bar_chart(results.set_index("Option"))
    for option, count in sorted(counts.items(), key=lambda item: item[1], reverse=True):
        pct = count / total * 100 if total else 0
        st.write(f"**{count} votes ({pct:.1f}%)** — {option}")
else:
    st.write("No votes have been recorded yet.")
st.caption("Do not use this prototype for the live class poll until persistent storage is configured and tested.")
