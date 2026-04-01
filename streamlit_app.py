# country_simulator.py
import streamlit as st
from docx import Document
import PyPDF2
import random
import os

# ------------------------
# INITIALIZATION
# ------------------------
st.set_page_config(page_title="Country Simulator", layout="wide")
st.title("📜 Country Simulation Game")

# Initialize metrics in session state
if "metrics" not in st.session_state:
    st.session_state.metrics = {
        "Economy": 50,
        "Happiness": 50,
        "Stability": 50,
        "Social Policy": 50,
        "Foreign Policy": 50,
        "Military": 50,
        "War Threat": 0,
        "Environment": 50
    }

if "history" not in st.session_state:
    st.session_state.history = []

# ------------------------
# KEYWORD EFFECTS
# ------------------------
KEYWORD_EFFECTS = {
    # Economic
    "tax increase": {"Economy": -2, "Happiness": -1, "Social Policy": +1},
    "tax cut": {"Economy": +2, "Stability": -1},
    "trade agreement": {"Economy": +2, "Happiness": +1, "Foreign Policy": +3},
    "deregulation": {"Economy": +2, "Stability": -1, "Social Policy": -1, "Environment": -1},
    # Social
    "healthcare": {"Economy": -1, "Happiness": +3, "Social Policy": +3},
    "education": {"Economy": +1, "Happiness": +2, "Social Policy": +3},
    "civil rights": {"Happiness": +2, "Stability": +2, "Social Policy": +3},
    "welfare": {"Economy": -1, "Happiness": +2, "Social Policy": +2},
    # Foreign / War
    "declare war": {"Economy": -3, "Happiness": -2, "Stability": -2, "Foreign Policy": +3, "Military": +3, "War Threat": +3},
    "peace treaty": {"Economy": +1, "Happiness": +1, "Stability": +1, "Foreign Policy": +3, "War Threat": -1},
    "sanctions": {"Economy": -1, "Stability": +1, "Foreign Policy": -2, "War Threat": +1},
    "military spending": {"Economy": -2, "Stability": +2, "Foreign Policy": +1, "Military": +3},
    "invasion repelled": {"Economy": +1, "Happiness": +2, "Stability": +2, "Foreign Policy": +1, "Military": +2},
    "environment": {"Economy": -1, "Happiness": +2, "Stability": +1, "Environment": +3}
}

# ------------------------
# FUNCTION: EXTRACT TEXT FROM FILE
# ------------------------
def extract_text(file):
    text = ""
    if file.name.endswith(".pdf"):
        pdf_reader = PyPDF2.PdfReader(file)
        for page in pdf_reader.pages:
            text += page.extract_text().lower()
    elif file.name.endswith(".docx"):
        doc = Document(file)
        for para in doc.paragraphs:
            text += para.text.lower()
    else:
        st.error("Unsupported file format! Upload PDF or DOCX only.")
    return text

# ------------------------
# FUNCTION: CALCULATE EFFECTS
# ------------------------
def calculate_effects(text):
    effects = {metric: 0 for metric in st.session_state.metrics}
    for keyword, vals in KEYWORD_EFFECTS.items():
        if keyword in text:
            for metric, value in vals.items():
                effects[metric] += value
    return effects

# ------------------------
# FUNCTION: APPLY EFFECTS
# ------------------------
def apply_effects(effects, law_name, passed):
    for metric, change in effects.items():
        if passed:
            st.session_state.metrics[metric] += change
        else:
            # small penalty for failed opportunity
            st.session_state.metrics[metric] -= max(1, change // 2)
        # Clamp between 0-100
        st.session_state.metrics[metric] = min(max(st.session_state.metrics[metric], 0), 100)
    # Log history
    st.session_state.history.append({
        "Law": law_name,
        "Passed": passed,
        "Effects": effects
    })

# ------------------------
# UPLOAD LAW
# ------------------------
st.header("📄 Propose a Law or Action")
law_file = st.file_uploader("Upload PDF or Word (.docx) of your law:", type=["pdf", "docx"])
law_name = st.text_input("Or enter a law/action name:")

# ------------------------
# AI VOTING SYSTEM
# ------------------------
def simulate_votes():
    # Parties: Progressive, Conservative, Centrist
    votes = {"Progressive": random.choice([True, False]),
             "Conservative": random.choice([True, False]),
             "Centrist": random.choice([True, False])}
    return votes

if st.button("Submit Law / Action"):
    if law_file or law_name:
        # Extract text if file uploaded
        text = ""
        if law_file:
            text = extract_text(law_file)
        if law_name:
            text += " " + law_name.lower()
        # Calculate effects
        effects = calculate_effects(text)
        # AI votes
        votes = simulate_votes()
        player_vote = st.radio("Your Vote:", ("Yes", "No"), index=0)
        yes_count = sum(votes.values()) + (1 if player_vote == "Yes" else 0)
        no_count = len(votes) - sum(votes.values()) + (1 if player_vote == "No" else 0)
        passed = yes_count > no_count
        apply_effects(effects, law_name if law_name else law_file.name, passed)
        st.success(f"Law {'PASSED' if passed else 'FAILED'}! ✅" if passed else f"Law FAILED ❌")
        st.write("AI Votes:", votes)
        st.write("Effects Applied:", effects)
    else:
        st.warning("Please upload a file or enter a law name!")

# ------------------------
# METRICS DISPLAY
# ------------------------
st.header("📊 Country Metrics")
for metric, value in st.session_state.metrics.items():
    st.progress(value/100, text=f"{metric}: {value}")

# ------------------------
# HISTORY DISPLAY
# ------------------------
st.header("📜 Law & Action History")
for entry in st.session_state.history[::-1]:
    st.write(f"**{entry['Law']}** — {'PASSED' if entry['Passed'] else 'FAILED'}")
    st.write(entry["Effects"])
    st.write("---")
