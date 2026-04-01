# Filename: elon_simulator_final.py
import streamlit as st
import random
import pickle
import plotly.express as px

st.set_page_config(page_title="Commonwealth of Elon Simulator", layout="wide")

# --- Load or Initialize Game State ---
try:
    with open("game_state.pkl", "rb") as f:
        game_state = pickle.load(f)
except:
    game_state = {
        "year": 1,
        "session": 1,
        "players": {},
        "delegates": [],
        "factions": {},
        "laws_passed": [],
        "metrics": {"economy":50,"social":50,"foreign":50,"approval":50},
        "events": [],
        "constitution": """
Constitution of the Commonwealth of Elon

Preamble
We, the citizens of the Commonwealth of Elon, in order to form a free, just, and enlightened society, establish equality, ensure liberty, promote education, and secure the blessings of self-governance for ourselves and future generations, do hereby ordain this Constitution.

Article I – State Identity
Name: Commonwealth of Elon
Type: Sovereign Republic
Government: Unicameral Legislature with Executive and Judiciary

Article II – Legislative Branch (General Assembly)
Type: Unicameral
Members: Elected by citizens (100 total)
Term: 3 years
Powers: Pass laws, taxes, budgets, approve treaties, oversight of executive branch

Article III – Executive Branch (President)
Role: Head of State & Government
Term: 6 years
Powers: Enforce laws, Commander-in-Chief, represent internationally
Removal: Two-thirds Assembly vote for constitutional violations

Article IV – Judiciary (Supreme Court of Elon)
Role: Interpret constitutionality
Appointment: President appoints judges with Assembly approval
Function: Protect rights, resolve disputes

Article V – Rights of Citizens
Freedom of Speech, Assembly, Right to Bear Arms, Right to Education, Equality, Privacy, Right to Petition

Article VI – Civic Duties
Participate in elections, respect rights, contribute to community

Article VII – Amendments
Proposed by: Two-thirds Assembly or 10% citizen petition
Ratification: Majority vote in referendum

Article VIII – National Symbols
Flag, motto, and anthem reflect unity, scholarship, and civic pride
"""
    }

MAX_DELEGATES = 100
LAWS_PER_SESSION = 4
SESSIONS_PER_YEAR = 2

# --- Foreign Relations Setup ---
if "foreign_relations" not in game_state:
    game_state["foreign_relations"] = {
        "Dominion of Highpoint": {"diplomacy": 50, "trade": 50, "allied": False, "at_war": False},
        "Republic of Astoria": {"diplomacy": 40, "trade": 30, "allied": False, "at_war": False},
        "United Provinces of Veldt": {"diplomacy": 70, "trade": 60, "allied": False, "at_war": False},
        "Confederation of Solaria": {"diplomacy": 30, "trade": 20, "allied": False, "at_war": False},
    }

# --- Helper Functions ---
def add_player(name):
    if name not in game_state["players"]:
        faction_name = f"{name} Faction"
        game_state["players"][name] = {"faction": faction_name}
        game_state["factions"][faction_name] = {"leader": name, "popularity":50}
        game_state["delegates"].append({"name":name,"type":"player","faction":faction_name,"title":"Delegate"})

def redistribute_ai_delegates():
    player_factions = list(game_state["factions"].keys())
    player_count = len(player_factions)
    total_ai = MAX_DELEGATES - player_count
    total_pop = sum(game_state["factions"][f]["popularity"] for f in player_factions)
    if total_pop <= 0: total_pop = 1
    new_ai_dist = {}
    for f in player_factions:
        prop = game_state["factions"][f]["popularity"]/total_pop
        new_ai_dist[f] = max(round(prop*total_ai),1)
    diff = total_ai - sum(new_ai_dist.values())
    idx=0
    while diff!=0:
        fac = player_factions[idx%len(player_factions)]
        if diff>0:
            new_ai_dist[fac]+=1
            diff-=1
        else:
            if new_ai_dist[fac]>1:
                new_ai_dist[fac]-=1
                diff+=1
        idx+=1
    for f in player_factions:
        current_ai = [d for d in game_state["delegates"] if d["type"]=="AI" and d["faction"]==f]
        needed = new_ai_dist[f]
        if len(current_ai) > needed:
            to_remove = current_ai[:len(current_ai)-needed]
            for r in to_remove: game_state["delegates"].remove(r)
        elif len(current_ai) < needed:
            for i in range(needed - len(current_ai)):
                new_ai_name = f"{f}_AI{len(current_ai)+i+1}"
                game_state["delegates"].append({"name":new_ai_name,"type":"AI","faction":f,"title":"Delegate"})

def apply_random_event():
    event_chance = random.random()
    if event_chance < 0.3:
        event = random.choice([
            {"desc":"Economic Boom","effect":{"economy":+10}},
            {"desc":"Social Unrest","effect":{"social":-10}},
            {"desc":"Foreign Tension","effect":{"foreign":-10}},
            {"desc":"Scandal in Assembly","effect":{"approval":-5}}
        ])
        for key, val in event["effect"].items():
            game_state["metrics"][key] = max(0,min(100,game_state["metrics"][key]+val))
        game_state["events"].append(f"Year {game_state['year']} Session {game_state['session']}: {event['desc']}")
    else:
        game_state["events"].append(f"Year {game_state['year']} Session {game_state['session']}: No event occurred.")

def pass_laws():
    for _ in range(LAWS_PER_SESSION):
        law_name = f"Law_{game_state['year']}_{game_state['session']}_{random.randint(1,100)}"
        unconstitutional = random.random()<0.15
        if unconstitutional:
            game_state["events"].append(f"{law_name} was struck down by Judiciary.")
        else:
            game_state["laws_passed"].append(law_name)
            fac = random.choice(list(game_state["factions"].keys()))
            game_state["factions"][fac]["popularity"] = min(100, game_state["factions"][fac]["popularity"]+5)

def advance_session():
    pass_laws()
    apply_random_event()
    redistribute_ai_delegates()
    game_state["session"]+=1
    if game_state["session"]>SESSIONS_PER_YEAR:
        game_state["session"]=1
        game_state["year"]+=1

# --- UI ---
st.title("Commonwealth of Elon Simulator")

player_name = st.text_input("Enter your name to join:")
if st.button("Join Game") and player_name:
    add_player(player_name)
    redistribute_ai_delegates()

st.sidebar.header("Controls")
if st.sidebar.button("Advance Session"):
    advance_session()

# --- Presidential Election Interface (Every 6 Years) ---
st.sidebar.header("🗳 Presidential Election")

# Only trigger election every 6 years
if game_state["year"] % 6 == 1:  # e.g., years 1,7,13...
    candidates = st.sidebar.multiselect(
        "Select candidates to run for President",
        list(game_state["players"].keys())
    )

    if st.sidebar.button("Run Presidential Election"):
        if not candidates:
            st.sidebar.warning("No candidates selected!")
        else:
            # Tally support scores based on faction popularity
            support_scores = {}
            for cand in candidates:
                faction = game_state["players"][cand]["faction"]
                pop = game_state["factions"][faction]["popularity"]
                # Candidate support = faction popularity + small randomness
                support_scores[cand] = pop + random.randint(0, 10)

            # Determine winner
            winner = max(support_scores, key=support_scores.get)

            # Update titles
            for pid in game_state["players"]:
                if game_state["players"][pid].get("title") == "President":
                    game_state["players"][pid]["title"] = "Delegate"
            game_state["players"][winner]["title"] = "President"

            st.sidebar.success(f"{winner} is elected President!")
else:
    st.sidebar.info("No Presidential Election this year.")

# --- Legislature Tab ---
tab_legislature, tab_foreign, tab_map, tab_metrics = st.tabs(
    ["General Assembly", "Foreign Policy", "Regional Map", "Metrics"]
)

with tab_legislature:
    st.header("📝 General Assembly - Lawmaking")

    # --- LAW PROPOSAL ---
    st.subheader("Propose a Law (Players Only)")
    if player_name:
        law_title = st.text_input("Law Title", key="law_title_input")
        law_summary = st.text_area("Law Summary", key="law_summary_input")
        if st.button("Propose Law", key="propose_law_btn"):
            if law_title.strip() and law_summary.strip():
                proposed_law = {
                    "title": law_title.strip(),
                    "summary": law_summary.strip(),
                    "proposer": player_name,
                    "session": game_state["session"],
                    "year": game_state["year"]
                }

                votes_for = 0
                votes_against = 0
                delegates = game_state["delegates"]
                factions = game_state["factions"]

                for d in delegates:
                    # Player always votes YES for own law
                    if d["type"] == "player" and d["name"] == player_name:
                        votes_for += 1
                    # AI delegates in same faction vote YES
                    elif d["faction"] == game_state["players"][player_name]["faction"]:
                        votes_for += 1
                    else:
                        # AI delegates outside faction vote based on popularity
                        pop = factions[d["faction"]]["popularity"]
                        if random.random() < (pop / 100):
                            votes_for += 1
                        else:
                            votes_against += 1

                # Judiciary check: 15% chance to strike down
                if votes_for > votes_against:
                    unconstitutional = random.random() < 0.15
                    if unconstitutional:
                        st.warning(f"✅ {law_title} PASSED but struck down by Judiciary!")
                        game_state["events"].append(
                            f"Year {game_state['year']} Session {game_state['session']}: {law_title} struck down by Judiciary"
                        )
                    else:
                        st.success(f"✅ {law_title} PASSED!")
                        game_state["laws_passed"].append(proposed_law)
                        # Boost proposer faction popularity slightly
                        proposer_faction = game_state["players"][player_name]["faction"]
                        game_state["factions"][proposer_faction]["popularity"] = min(
                            100, game_state["factions"][proposer_faction]["popularity"] + 5
                        )
                        game_state["events"].append(
                            f"Year {game_state['year']} Session {game_state['session']}: {law_title} PASSED"
                        )
                else:
                    st.error(f"❌ {law_title} FAILED to pass.")
                    game_state["events"].append(
                        f"Year {game_state['year']} Session {game_state['session']}: {law_title} FAILED"
                    )
            else:
                st.error("Please provide both a Law Title and Summary.")

    # --- FOREIGN POLICY VOTING ---
    if game_state.get("current_foreign_proposal"):
        proposal = game_state["current_foreign_proposal"]
        st.subheader("📣 Assembly Vote on Foreign Policy")
        st.write(f"Proposal: {proposal['type'].replace('_',' ').title()} with {proposal['country']}")

        if st.button("Vote on Foreign Policy", key="foreign_vote_btn_legislature"):
            votes_for = 0
            votes_against = 0
            for d in game_state["delegates"]:
                if d["type"] == "player":
                    votes_for += 1
                else:
                    faction = d["faction"]
                    pop = game_state["factions"][faction]["popularity"]
                    if random.random() < (pop / 100):
                        votes_for += 1
                    else:
                        votes_against += 1

            st.write(f"Votes — For: {votes_for}, Against: {votes_against}")

            if votes_for > votes_against:
                st.success("Proposal PASSED!")
                c = proposal["country"]
                if proposal["type"] == "propose_alliance":
                    game_state["foreign_relations"][c]["allied"] = True
                elif proposal["type"] == "propose_declaration_of_war":
                    game_state["foreign_relations"][c]["at_war"] = True
                elif proposal["type"] == "trade_deal":
                    game_state["foreign_relations"][c]["trade"] += 10
                elif proposal["type"] == "send_aid":
                    game_state["foreign_relations"][c]["diplomacy"] += 10
            else:
                st.error("Proposal FAILED.")

            del game_state["current_foreign_proposal"]

    # --- DISPLAY PASSED LAWS ---
    st.subheader("📚 Passed Laws")
    if game_state["laws_passed"]:
        for law in game_state["laws_passed"]:
            st.markdown(f"**{law['title']}** — {law['summary']} (Proposed by {law['proposer']})")
    else:
        st.info("No laws have been passed yet.")

    # --- DISPLAY EVENTS LOG ---
    st.subheader("📜 Recent Events")
    if game_state["events"]:
        for e in game_state["events"][-10:]:  # last 10 events
            st.write(f"- {e}")
    else:
        st.info("No events yet this session.")
            
# --- Foreign Policy UI ---
with tab5:  # Or create a new tab like tab7 with st.tabs([...,"Foreign Policy",...])
    st.header("🌍 Foreign Policy & Diplomacy")

    # Show current status with each country
    for country, rel in game_state["foreign_relations"].items():
        st.write(f"**{country}** — Diplomacy: {rel['diplomacy']} | Trade: {rel['trade']} | "
                 f"Allied: {rel['allied']} | War: {rel['at_war']}")

    # Only allow President to propose actions
    current_pres = None
    for pid, pdata in game_state["players"].items():
        if pdata.get("title") == "President":
            current_pres = pid

    if current_pres:
        st.subheader("🇪🇱 Presidential Diplomatic Actions")

        # Choose a country
        target_country = st.selectbox("Select a country for action:",
                                      list(game_state["foreign_relations"].keys()))

        # Buttons for diplomatic proposals
        if st.button("Propose Alliance"):
            st.write(f"{game_state['players'][current_pres]['name']} proposes an alliance with {target_country}.")
            game_state["events"].append(
                f"Year {game_state['year']} Session {game_state['session']}: Proposal - Alliance with {target_country}"
            )
            # Send proposal to legislature for voting
            game_state["current_foreign_proposal"] = {
                "type": "alliance",
                "country": target_country,
                "proposed_by": current_pres
            }

        if st.button("Propose Declaration of War"):
            st.write(f"{game_state['players'][current_pres]['name']} proposes declaring war on {target_country}.")
            game_state["events"].append(
                f"Year {game_state['year']} Session {game_state['session']}: Proposal - Declare war on {target_country}"
            )
            game_state["current_foreign_proposal"] = {
                "type": "war",
                "country": target_country,
                "proposed_by": current_pres
            }
    else:
        st.write("Only a President can propose foreign policy actions.")

# --- Create Regional Map Tab ---
tab_legislature, tab_foreign, tab_map, tab_metrics = st.tabs(
    ["Legislature", "Foreign Policy", "Regional Map", "Metrics"]
)

with tab_map:
    st.header("🗺️ Regional Map - Commonwealth of Elon & Neighbors")

    countries = ["Commonwealth of Elon"] + list(game_state["foreign_relations"].keys())
    relations = ["self"] + [game_state["foreign_relations"][c] for c in game_state["foreign_relations"]]

    # Assign colors based on relations
    country_colors = []
    for r in relations:
        if r == "self":
            country_colors.append("blue")  # Your country
        elif r["allied"]:
            country_colors.append("green")
        elif r["at_war"]:
            country_colors.append("red")
        else:
            country_colors.append("gray")  # Neutral

    # Simple pie chart representation
    fig, ax = plt.subplots()
    ax.pie([1]*len(countries), labels=countries, colors=country_colors, startangle=90)
    ax.set_title("Regional Relations")
    st.pyplot(fig)

    st.markdown(
        """
        **Legend:**  
        - 🔵 Your country  
        - 🟢 Allied  
        - 🔴 At War  
        - ⚪ Neutral  
        """
    )

# Tabs
tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs(["Overview","Legislature","Factions","Metrics","Map","Events","Constitution"])

with tab1:
    st.subheader(f"Year {game_state['year']} Session {game_state['session']}")
    st.write("Government Approval:", game_state["metrics"]["approval"])
    st.write("Economy:", game_state["metrics"]["economy"])
    st.write("Social:", game_state["metrics"]["social"])
    st.write("Foreign:", game_state["metrics"]["foreign"])

with tab2:
    st.subheader("General Assembly")
    st.dataframe(game_state["delegates"])
    faction_counts = {}
    for d in game_state["delegates"]:
        faction_counts[d["faction"]] = faction_counts.get(d["faction"],0)+1
    fig = px.pie(names=list(faction_counts.keys()), values=list(faction_counts.values()),
                 title="Assembly Makeup", color_discrete_sequence=px.colors.qualitative.Safe)
    st.plotly_chart(fig)

with tab3:
    st.subheader("Factions & Popularity")
    for fac, info in game_state["factions"].items():
        st.write(f"{fac} (Leader: {info['leader']}) - Popularity: {info['popularity']}")
        members = [d["name"] for d in game_state["delegates"] if d["faction"]==fac]
        st.write("Members:", ", ".join(members))

with tab4:
    st.subheader("Metrics Over Time")
    st.write(game_state["metrics"])

with tab5:
    st.subheader("Map of the Commonwealth of Elon")
    st.write("Neighboring countries:")
    st.write("- The Dominion of Highpoint (West)")
    st.write("- Other nations: Novaterra, Arcadia, Eldoria")
    st.map([[35.0, -80.0],[34.5, -81.0],[36.0, -79.0]])  # Placeholder coordinates

with tab6:
    st.subheader("Events History")
    for e in game_state["events"]:
        st.write(e)

with tab7:
    st.subheader("Constitution")
    st.text_area("Full Constitution", game_state["constitution"], height=600)

# Save state
with open("game_state.pkl","wb") as f:
    pickle.dump(game_state,f)4)
