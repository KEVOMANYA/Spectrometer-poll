
import streamlit as st
import pandas as pd
import hashlib
from supabase import create_client

st.set_page_config(
    page_title="SPH 401 Atomic Spectrometer Project Poll",
    page_icon="🔬",
    layout="centered",
)

TITLE = "SPH 401 Atomic Spectrometer Project Poll"

OPTIONS = [
    "Option 1: Lecturer-guided design — lecturer guides design/construction; students handle data acquisition and analysis.",
    "Option 2: Student-led design — students design/build; lecturer guides data acquisition and analysis.",
    "Option 3: Collaborative approach — design/construction together; students collect and analyse data with lecturer support.",
    "Option 4: Fully independent project — students handle all stages independently, asking for clarification when needed.",
    "Option 5: Simplified design and guided practical sessions — use a standard design and focus on spectra, calibration, analysis, and identifying elements.",
]


def get_supabase_client():
    """Connect using Streamlit Community Cloud Secrets."""
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_ANON_KEY"]
    return create_client(url, key)


def hash_code(code):
    """Hash the one-time voting code."""
    return hashlib.sha256(
        code.strip().upper().encode("utf-8")
    ).hexdigest()


st.title("🔬 " + TITLE)

st.write(
    "Please select ONE approach. The aim is to agree on a fair and "
    "manageable arrangement while meeting the learning objectives."
)

st.info(
    "Do not enter your name or admission number. Enter only your assigned "
    "one-time voting code. Your selected option is stored without your "
    "code or identity."
)

# 1. Connect to Supabase
try:
    supabase = get_supabase_client()
except Exception as e:
    st.error("Cannot connect to the poll database.")
    st.code(repr(e))
    st.stop()

# 2. Read poll status
try:
    status_result = (
        supabase.table("poll_settings")
        .select("status")
        .eq("id", 1)
        .single()
        .execute()
    )

    if not status_result.data:
        st.error("No poll settings row was found.")
        st.stop()

    poll_status = status_result.data["status"]

except Exception as e:
    st.error("Cannot read poll status. Actual database error:")
    st.code(repr(e))
    st.stop()

# 3. Voting form
if poll_status != "OPEN":
    st.warning("Voting is currently closed.")

else:
    with st.form("vote_form"):
        code = st.text_input(
            "Your one-time voting code",
            max_chars=8,
            help="Enter the 8-character code provided to you.",
        ).strip().upper()

        choice = st.radio(
            "Which approach do you prefer?",
            OPTIONS,
            index=None,
        )

        submitted = st.form_submit_button(
            "Submit my vote",
            use_container_width=True,
        )

    if submitted:
        if len(code) != 8 or not code.isalnum():
            st.error("Enter a valid 8-character voting code.")

        elif choice is None:
            st.error("Please select one option.")

        else:
            try:
                result = supabase.rpc(
                    "cast_vote",
                    {
                        "p_code_hash": hash_code(code),
                        "p_option": choice,
                    },
                ).execute()

                response = result.data

                if response == "OK":
                    st.success(
                        "Your vote has been recorded. Thank you!"
                    )
                    st.rerun()

                elif response == "USED":
                    st.error(
                        "This voting code has already been used."
                    )

                elif response == "INVALID":
                    st.error(
                        "That voting code is not valid. Check it "
                        "with the class representative."
                    )

                elif response == "CLOSED":
                    st.error("Voting has closed.")

                else:
                    st.error(
                        "The vote was not recorded. Unexpected "
                        "database response:"
                    )
                    st.code(repr(response))

            except Exception as e:
                st.error("The vote could not be submitted.")
                st.code(repr(e))

# 4. Aggregate results only
st.divider()
st.subheader("Poll results")

st.caption(
    "Only aggregate totals are displayed; individual votes are not shown."
)

try:
    results = (
        supabase.table("poll_results")
        .select("option_text,vote_count")
        .execute()
        .data
    )

    counts = {option: 0 for option in OPTIONS}

    for row in results:
        if row["option_text"] in counts:
            counts[row["option_text"]] = int(row["vote_count"])

    total = sum(counts.values())
    st.metric("Total votes", total)

    if total == 0:
        st.write("No votes have been recorded yet.")

    else:
        results_df = pd.DataFrame(
            [
                {"Option": option, "Votes": count}
                for option, count in counts.items()
            ]
        )

        st.bar_chart(results_df.set_index("Option"))

        for option, count in sorted(
            counts.items(),
            key=lambda item: item[1],
            reverse=True,
        ):
            percentage = count / total * 100

            st.write(
                f"**{count} votes ({percentage:.1f}%)** — {option}"
            )

except Exception as e:
    st.warning("The results could not be loaded.")
    st.code(repr(e))
