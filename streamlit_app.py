# streamlit_app.py
import streamlit as st
import pandas as pd
import json
import os
from PyPDF2 import PdfReader

# ------------------------
# Setup
# ------------------------
st.set_page_config(page_title="Country Simulator", layout="wide")
st.title("🗳️ Country Simulator")
st.write("Create a country, propose laws, vote, manage regions and parties!")

SAVE_FILE = "savegame.json"

# ------------------------
# Initialize game state
# ------------------------
if os.path.exists(SAVE_FILE):
    with open(SAVE_FILE, "r") as f:
        game_state = json.load(f)
else:
    game_state = {
        "country_name": "Unnamed Confederation",
        "constitution": "Articles of Confederation (unnamed country)",
        "laws": [],
        "metrics": {"economy": 50, "happiness": 50, "stability": 50},
        "regions": {},  # {"RegionName": {"economy": 50, "happiness": 50, "stability": 50}}
        "parties": {},
        "history": []
    }

# ------------------------
# Helper functions
# ------------------------
def save_state():
    with open(SAVE_FILE, "w") as f:
        json.dump(game_state, f, indent=4)

def add_law(title, content):
    law = {"title": title, "content": content, "votes": {}}
    game_state["laws"].append(law)
    game_state["history"].append(f"New law proposed: {title}")
    save_state()

def vote_law(index, voter, vote):
    law = game_state["laws"][index]
    law["votes"][voter] = vote
    # AI vote simulation
    ai_vote = "Yes" if index % 2 == 0 else "No"
    law["votes"]["AI"] = ai_vote

    # Apply effects on country metrics
    for key in game_state["metrics"]:
        if vote.lower() == "yes":
            game_state["metrics"][key] += 2
        else:
            game_state["metrics"][key] -= 1

    # Apply effects on each region
    for rmetrics in game_state["regions"].values():
        if vote.lower() == "yes":
            rmetrics["economy"] += 2
            rmetrics["happiness"] += 1
            rmetrics["stability"] += 1
        else:
            rmetrics["economy"] -= 1
            rmetrics["happiness"] -= 2
            rmetrics["stability"] -= 1

    game_state["history"].append(f"{voter} voted {vote} on {law['title']}")
    save_state()

def create_party(name, ideology):
    game_state["parties"][name] = {"ideology": ideology, "popularity": 50}
    game_state["history"].append(f"Party created: {name}")
    save_state()

def add_region(name):
    if name not in game_state["regions"]:
        game_state["regions"][name] = {"economy": 50, "happiness": 50, "stability": 50}
        game_state["history"].append(f"Region created: {name}")
        save_state()

# ------------------------
# UI - Country Name
# ------------------------
st.subheader("🏴 Country Name")
country_name_input = st.text_input("Set Country Name", value=game_state["country_name"])
if st.button("Update Country Name"):
    game_state["country_name"] = country_name_input
    save_state()
    st.success("Country name updated!")

# ------------------------
# UI - Constitution
# ------------------------
st.subheader("📜 Constitution")
st.write(game_state["constitution"])
new_constitution = st.text_area("Edit Constitution", value=game_state["constitution"])
if st.button("Save Constitution"):
    game_state["constitution"] = new_constitution
    save_state()
    st.success("Constitution updated!")

# ------------------------
# UI - Regions
# ------------------------
st.subheader("🗺️ Regions")
new_region_name = st.text_input("Add New Region")
if st.button("Add Region"):
    if new_region_name:
        add_region(new_region_name)
        st.success(f"Region '{new_region_name}' added!")

# Show regional metrics
st.write("**Regional Metrics**")
for rname, rmetrics in game_state["regions"].items():
    st.write(f"**{rname}** - Economy: {rmetrics['economy']}, Happiness: {rmetrics['happiness']}, Stability: {rmetrics['stability']}")

# ------------------------
# UI - Propose Laws
# ------------------------
st.subheader("📝 Propose a Law")
law_title = st.text_input("Law Title", key="law_title")
law_file = st.file_uploader("Upload PDF Law (optional)", type="pdf")
if st.button("Submit Law"):
    content = ""
    if law_file:
        reader = PdfReader(law_file)
        for page in reader.pages:
            text = page.extract_text()
            if text:
                content += text
    add_law(law_title, content)
    st.success(f"Law '{law_title}' proposed!")

# ------------------------
# UI - Vote on Laws
# ------------------------
st.subheader("✅ Vote on Laws")
for i, law in enumerate(game_state["laws"]):
    st.write(f"**{law['title']}**")
    st.write(law.get("content", "No text available."))
    col1, col2 = st.columns(2)
    with col1:
        if st.button(f"Vote YES on {law['title']}", key=f"yes_{i}"):
            vote_law(i, "Player", "Yes")
            st.experimental_rerun()
    with col2:
        if st.button(f"Vote NO on {law['title']}", key=f"no_{i}"):
            vote_law(i, "Player", "No")
            st.experimental_rerun()
    st.write("Votes:", law["votes"])

# ------------------------
# UI - Country Metrics
# ------------------------
st.subheader("📊 Country Metrics")
metrics_df = pd.DataFrame.from_dict(game_state["metrics"], orient="index", columns=["Value"])
st.bar_chart(metrics_df)

# ------------------------
# UI - Political Parties
# ------------------------
st.subheader("🏛️ Political Parties")
party_name = st.text_input("Party Name", key="party_name")
party_ideology = st.text_input("Ideology", key="party_ideology")
if st.button("Create Party"):
    create_party(party_name, party_ideology)
    st.success(f"Party '{party_name}' created!")

for pname, pdata in game_state["parties"].items():
    st.write(f"**{pname}** - Ideology: {pdata['ideology']} | Popularity: {pdata['popularity']}%")

# ------------------------
# UI - Game History
# ------------------------
st.subheader("📜 Game History")
for entry in game_state["history"][-20:]:  # last 20 actions
    st.write("-", entry)

st.info("Game auto-saves after every action.")
