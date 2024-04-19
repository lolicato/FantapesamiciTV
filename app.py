import streamlit as st
import sqlite3
import re




def local_css():
    st.markdown(
        f"""
        <style>
            /* Default styles for desktop */
            .stApp {{
                --sidebar-bg-color: black; /* Streamlit's variable for sidebar background */
            }}
            .stSidebar .css-1d391kg, .stSidebar .css-1l02zno, .stSidebar .st-bx, .stSidebar .st-cx {{
                color: white;
            }}
            .logo {{
                height: 200px;
                width: auto;
                display: block;
                margin: 20px auto;
            }}

            /* Media queries for tablets */
            @media (max-width: 768px) {{
                .stApp {{
                    --sidebar-bg-color: #333;
                }}
                .logo {{
                    height: 150px; /* Smaller logo for smaller devices */
                }}
            }}

            /* Media queries for smartphones */
            @media (max-width: 480px) {{
                .stApp {{
                    --sidebar-bg-color: #666;
                }}
                .stSidebar .css-1d391kg, .stSidebar .css-1l02zno, .stSidebar .st-bx, .stSidebar .st-cx {{
                    color: #ccc;
                }}
                .logo {{
                    height: 100px; /* Even smaller logo for smartphones */
                }}
            }}
        </style>
        """,
        unsafe_allow_html=True
    )

    # Add logo to the sidebar
    st.sidebar.markdown(
        f"""
        <img src="https://www.fantamanagerleague.it/leghe/fantapesamici/images/headerlogo.PNG" alt="Logo" class="logo">
        """,
        unsafe_allow_html=True
    )


# Apply the custom CSS
local_css()


# Database setup
conn = sqlite3.connect('matches.db', check_same_thread=False)  # Allow multi-thread access if needed
c = conn.cursor()

def create_table():
    try:
        c.execute('''
            CREATE TABLE IF NOT EXISTS match_data(
                youtube_link TEXT,
                competition_type TEXT,
                player1 TEXT,
                player2 TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
    except Exception as e:
        st.error(f"Failed to create table: {e}")


create_table()


@st.cache_data
def load_teams():
    try:
        teams = []
        with open('clubs.txt', 'r') as file:
            lines = file.readlines()
            for line in lines:
                parts = line.strip().split(',')
                if len(parts) == 2:
                    team_name = parts[0].strip().strip('"')
                    logo_url = parts[1].strip().strip('"')
                    teams.append((team_name, logo_url))
        return teams
    except Exception as e:
        st.error(f"Failed to load teams: {e}")
        return []

def load_competitions():
    try:
        with open('competitions.txt', 'r') as file:
            competitions = [line.strip().strip('"') for line in file.readlines()]
        return competitions
    except Exception as e:
        st.error(f"Failed to load competitions: {e}")
        return []

def add_data(youtube_link, competition_type, player1, player2):
    try:
        c.execute('''
            INSERT INTO match_data (youtube_link, competition_type, player1, player2)
            VALUES (?, ?, ?, ?)
        ''', (youtube_link, competition_type, player1, player2))
        conn.commit()
    except Exception as e:
        st.error(f"Failed to add data: {e}")


def view_all_data():
    try:
        c.execute('SELECT youtube_link, competition_type, player1, player2, created_at FROM match_data ORDER BY created_at DESC')
        data = c.fetchall()
        return data
    except Exception as e:
        st.error(f"Failed to fetch data: {e}")
        return []


def extract_youtube_id(url):
    if 'youtu.be' in url:
        return url.split('/')[-1]
    regex = r"(?<=v=)[^&#]+"
    matches = re.search(regex, url)
    if matches:
        return matches.group(0)
    return None


def main_page():
    st.title('FantaPesAmici TV')
    st.markdown("---")

    data = view_all_data()
    team_dict = dict(load_teams())

    for index, entry in enumerate(data):
        youtube_id = extract_youtube_id(entry[0])
        competition_type, player1, player2, created_at = entry[1], entry[2], entry[3], entry[4]
        if youtube_id:
            logo1 = team_dict.get(player1, "")
            logo2 = team_dict.get(player2, "")
            
            players_matchup_html = f"""
            <div style="color: black; font-size: 18px; margin-bottom: 10px;">
                {competition_type}
            </div>
            <div style="display: flex; align-items: center; font-size: 20px; font-weight: bold; margin-bottom: 20px;">
                <img src="{logo1}" alt="{player1}" style="width: 50px; height: auto; margin-right: 10px;">
                <span style="color: red;">{player1}</span>
                <span style="color: black; margin: 0 5px;">Vs</span>
                <span style="color: red;">{player2}</span>
                <img src="{logo2}" alt="{player2}" style="width: 50px; height: auto; margin-left: 10px;">
            </div>
            """
            st.markdown(players_matchup_html, unsafe_allow_html=True)
            
            
            # Embed YouTube video with custom margin for spacing
            youtube_iframe = f"""
            <div style="margin-bottom: 20px;">
                <iframe width="560" height="315" src="https://www.youtube.com/embed/{youtube_id}" frameborder="0" allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture" allowfullscreen></iframe>
            </div>
            {created_at}
            """
            st.markdown(youtube_iframe, unsafe_allow_html=True)
            
            st.markdown("---")  # Horizontal line for separation between entries


def get_competition_stats():
    try:
        # Define lists for each category
        lega_competitions = ["LEGA A", "LEGA B", "LEGA C"]
        final_eight_competitions = ["Final Eight Gold", "Final Eight Silver", "Final Eight Bronze", "GOLDEN FINAL", "SILVER FINAL", "BRONZE FINAL"]
        amichevole = ["Amichevole"]
        coppa_delle_leghe = ["COPPA DELLE LEGHE"]

        # SQL query that filters for specific competitions, ensuring placeholders match the number of competitions
        c.execute('''
            SELECT player1, competition_type, COUNT(*) as count
            FROM match_data
            WHERE competition_type IN (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            GROUP BY player1, competition_type
            ORDER BY player1
        ''', (*lega_competitions, *final_eight_competitions, *amichevole, *coppa_delle_leghe))

        raw_data = c.fetchall()
        return raw_data
    except Exception as e:
        st.error(f"Failed to fetch competition stats: {e}")
        return []


def stats_page():
    st.title('Statistiche delle Dirette Stagione 1')

    data = get_competition_stats()
    if data:
        # Prepare a dictionary to hold the data in a structured format
        from collections import defaultdict
        import pandas as pd

        competition_counts = defaultdict(lambda: defaultdict(int))
        for player, competition, count in data:
            category = None
            if competition in ["LEGA A", "LEGA B", "LEGA C"]:
                category = "LEGA"
            elif competition in ["Final Eight Gold", "Final Eight Silver", "Final Eight Bronze", "GOLDEN FINAL", "SILVER FINAL", "BRONZE FINAL"]:
                category = "Final Eight"
            elif competition == "Amichevole":
                category = "Amichevole"
            elif competition == "COPPA DELLE LEGHE":
                category = "COPPA DELLE LEGHE"
            if category:
                competition_counts[player][category] += count

        # Convert the dictionary to a DataFrame for display
        df = pd.DataFrame.from_dict(competition_counts, orient='index').fillna(0).astype(int)
        df.index.name = 'Player Name'
        df.columns.name = 'Competition'

        # Show the DataFrame as a table in Streamlit
        st.table(df)
    else:
        st.write("No data available.")



def form_page():
    st.title('Match Submission Form')
    competitions = load_competitions()  # Load competition names
    youtube_link = st.text_input('YouTube Link for the Online Match', key='youtube_link')
    with st.form(key='match_form'):
        competition_type = st.selectbox('Type of Competition', competitions)  # Use loaded competitions for dropdown
        team_names = [team[0] for team in load_teams()]
        player1 = st.selectbox('Casa', team_names)
        player2 = st.selectbox('Trasferta', team_names)
        submitted = st.form_submit_button('Submit')
        if submitted:
            add_data(youtube_link, competition_type, player1, player2)
            st.success('Submission successful!')


def irpef_calculation_page():
    st.title('Calcolo IRPEF')
    team_names = [team[0] for team in load_teams()]  # Load team names from the clubs.txt file
    team_name = st.selectbox('Nome della squadra', team_names)
    average_age = st.number_input('Età media della squadra', min_value=0.0, format="%.1f")
    
    # Input for salary
    salary_input = st.text_input("Monte ingaggio della squadra (€)", value="")

    # Format input on the fly
    if salary_input:
        try:
            # Remove any non-numeric characters for calculation purposes
            salary = float(salary_input.replace(".", "").replace(",", ""))
            formatted_salary = f"{salary:,.0f}".replace(",", ".")
            st.write("Monte ingaggio inserito: €" + formatted_salary)
        except ValueError:
            st.error("Inserire un numero valido.")
    else:
        salary = 0

    calculate_button = st.button('Calcola')

    if calculate_button:
        tax_rate = 0
        if average_age <= 22:
            tax_rate = 0
        elif 22.1 <= average_age <= 23:
            tax_rate = 5
        elif 23.1 <= average_age <= 24:
            tax_rate = 10
        elif 24.1 <= average_age <= 25:
            tax_rate = 15
        elif 25.1 <= average_age <= 26:
            tax_rate = 20
        elif average_age > 26.1:
            tax_rate = 25

        tax_to_pay = (tax_rate / 100) * salary
        st.success(f"La tua IRPEF da pagare ammonta a €{tax_to_pay:,.0f} ({tax_rate}% del monte ingaggio).".replace(",", "."))

# Add to the sidebar navigation
st.sidebar.title('Menu')
page = st.sidebar.radio(' ', ('Live Streaming', 'Carica Link', 'Statistiche', 'Calcolo IRPEF'))

# Add to the main control flow in your Streamlit app
if page == 'Live Streaming':
    main_page()
elif page == 'Carica Link':
    form_page()
elif page == 'Statistiche':
    stats_page()
elif page == 'Calcolo IRPEF':
    irpef_calculation_page()


