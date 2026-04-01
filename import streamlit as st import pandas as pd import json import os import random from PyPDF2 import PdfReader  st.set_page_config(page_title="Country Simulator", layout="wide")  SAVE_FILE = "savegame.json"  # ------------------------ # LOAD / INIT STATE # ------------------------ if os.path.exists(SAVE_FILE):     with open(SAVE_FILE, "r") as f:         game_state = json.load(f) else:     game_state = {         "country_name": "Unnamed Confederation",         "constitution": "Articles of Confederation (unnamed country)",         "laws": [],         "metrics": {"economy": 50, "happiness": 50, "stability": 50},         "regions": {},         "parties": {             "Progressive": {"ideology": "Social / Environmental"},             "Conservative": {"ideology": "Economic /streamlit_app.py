import streamlit as st
import pandas as pd
import json
import os
import random
from PyPDF2 import PdfReader

st.set_page_config(page_title="Country Simulator", layout="wide")

SAVE_FILE = "savegame.json"

# ------------------------
# LOAD / INIT STATE
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
        "regions": {},
        "parties": {
            "Progressive": {"ideology": "Social / Environmental"},
            "Conservative": {"ideology": "Economic / Security"},
            "Centrist": {"ideology": "Balanced"}
        },
        "history": [],
        "legislature": [
            {"name": "Player", "party": "Independent", "type": "Human"},
            {"name": "AI_1", "party": "Progressive", "type": "AI"},
            {"name": "AI_2", "party": "Conservative", "type": "AI"},
            {"name": "AI_3", "party": "Centrist", "type": "AI"}
        ]
    }

def save():
    with open(SAVE_FILE, "w") as f:
        json.dump(game_state, f, indent=4)

# ------------------------
# AI VOTING
# ------------------------
def ai_vote(party):
    if party == "Progressive":
        return "Yes"
    elif party == "Conservative":
        return "No"
    return "Yes" if random.random() > 0.5 else "No"

# ------------------------
# FUNCTIONS
# ------------------------
def propose_law(title, content):
    game_state["laws"].append({"title": title, "content": content, "votes": {}})
    game_state["history"].append(f"Law proposed: {title}")
    save()

def vote_on_law(index, vote):
    law = game_state["laws"][index]
    law["votes"]["Player"] = vote

    for member in game_state["legislature"]:
        if member["type"] == "AI":
            law["votes"][member["name"]] = ai_vote(member["party"])

    yes = list(law["votes"].values()).count("Yes")
    no = list(law["votes"].values()).count("No")

    if yes > no:
        for k in game_state["metrics"]:
            game_state["metrics"][k] += 2
        for r in game_state["regions"].values():
            r["economy"] += 2
            r["happiness"] += 1
            r["stability"] += 1
        result = "PASSED"
    else:
        for k in game_state["metrics"]:
            game_state["metrics"][k] -= 1
        for r in game_state["regions"].values():
            r["economy"] -= 1
            r["happiness"] -= 2
            r["stability"] -= 1
        result = "FAILED"

    game_state["history"].append(f"{law['title']} {result} ({yes}-{no})")
    save()

def add_region(name):
    if name not in game_state["regions"] and name != "":
        game_state["regions"][name] = {"economy": 50, "happiness": 50, "stability": 50}
        game_state["history"].append(f"Region added: {name}")
        save()

def add_party(name, ideology):
    if name != "":
        game_state["parties"][name] = {"ideology": ideology}
        game_state["history"].append(f"Party created: {name}")
        save()

# ------------------------
# UI
# ------------------------
st.title("🌍 Country Simulator")

tabs = st.tabs([
    "🏠 Country",
    "🏛️ Legislature",
    "🗺️ Regions",
    "📝 Laws",
    "🏛️ Parties",
    "📊 Metrics",
    "📜 History",
    "⚠️ Reset"
])

# COUNTRY
with tabs[0]:
    st.subheader("Country Name")
    name = st.text_input("Name", game_state["country_name"])
    if st.button("Update Name"):
        game_state["country_name"] = name
        save()
        st.success("Updated!")

    st.subheader("Constitution")
    constitution = st.text_area("Edit Constitution", game_state["constitution"])
    if st.button("Save Constitution"):
        game_state["constitution"] = constitution
        save()
        st.success("Saved!")

# LEGISLATURE
with tabs[1]:
    st.subheader("Legislature")
    df = pd.DataFrame(game_state["legislature"])
    st.dataframe(df)

    counts = df["party"].value_counts()
    st.bar_chart(counts)

    if len(counts) > 0:
        st.success(f"{counts.idxmax()} controls ({counts.max()}/{len(df)})")

# REGIONS
with tabs[2]:
    st.subheader("Regions")
    new_region = st.text_input("New Region")
    if st.button("Add Region"):
        add_region(new_region)

    for r, stats in game_state["regions"].items():
        st.write(f"**{r}** → {stats}")

# LAWS
with tabs[3]:
    st.subheader("Propose Law")

    title = st.text_input("Law Title")
    pdf = st.file_uploader("Upload PDF", type="pdf")

    if st.button("Submit Law"):
        content = ""
        if pdf:
            reader = PdfReader(pdf)
            for page in reader.pages:
                text = page.extract_text()
                if text:
                    content += text
        propose_law(title, content)

    st.subheader("Vote")

    for i, law in enumerate(game_state["laws"]):
        st.write(f"### {law['title']}")
        st.write(law["content"][:300] if law["content"] else "No content")

        yes = list(law["votes"].values()).count("Yes")
        no = list(law["votes"].values()).count("No")

        st.write(f"👍 {yes} | 👎 {no}")

        col1, col2 = st.columns(2)
        with col1:
            if st.button(f"YES {i}"):
                vote_on_law(i, "Yes")
                st.experimental_rerun()
        with col2:
            if st.button(f"NO {i}"):
                vote_on_law(i, "No")
                st.experimental_rerun()

        st.write(law["votes"])

# PARTIES
with tabs[4]:
    st.subheader("Political Parties")

    name = st.text_input("Party Name")
    ideology = st.text_input("Ideology")

    if st.button("Create Party"):
        add_party(name, ideology)

    for p, data in game_state["parties"].items():
        st.write(f"**{p}** - {data['ideology']}")

# METRICS
with tabs[5]:
    st.subheader("Country Metrics")
    st.bar_chart(pd.DataFrame.from_dict(game_state["metrics"], orient="index"))

# HISTORY
with tabs[6]:
    st.subheader("History")
    for h in game_state["history"][-20:]:
        st.write("-", h)

# RESET
with tabs[7]:
    st.subheader("Reset Game")
    if st.button("Reset Country"):
        if os.path.exists(SAVE_FILE):
            os.remove(SAVE_FILE)
        st.success("Reset complete. Refresh page.")
