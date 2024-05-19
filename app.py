import streamlit as st
import sqlite3
import re
import os

# Constants
DB_FILE_PATH = 'matches.db'
LOGO_URL = "https://www.fantamanagerleague.it/leghe/fantapesamici/images/headerlogo.PNG"
CORRECT_PASSWORD = os.getenv("ADMIN_PASSWORD", "admin")  # Use environment variable for the password

# Database connection
conn = sqlite3.connect(DB_FILE_PATH, check_same_thread=False)
c = conn.cursor()

# Functions
def apply_custom_css():
    st.markdown(
        f"""
        <style>
            .stApp {{
                --sidebar-bg-color: black;
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
            @media (max-width: 768px) {{
                .stApp {{
                    --sidebar-bg-color: #333;
                }}
                .logo {{
                    height: 150px;
                }}
            }}
            @media (max-width: 480px) {{
                .stApp {{
                    --sidebar-bg-color: #666;
                }}
                .stSidebar .css-1d391kg, .stSidebar .css-1l02zno, .stSidebar .st-bx, .stSidebar .st-cx {{
                    color: #ccc;
                }}
                .logo {{
                    height: 100px;
                }}
            }}
        </style>
        """,
        unsafe_allow_html=True
    )

def add_sidebar_logo():
    st.sidebar.markdown(
        f"""
        <img src="{LOGO_URL}" alt="Logo" class="logo">
        """,
        unsafe_allow_html=True
    )

def initialize_database():
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
        conn.commit()
    except Exception as e:
        st.error(f"Failed to create table: {e}")

@st.cache_data
def load_teams():
    try:
        with open('clubs.txt', 'r') as file:
            teams = [tuple(line.strip().split(',')) for line in file.readlines()]
        return teams
    except Exception as e:
        st.error(f"Failed to load teams: {e}")
        return []

@st.cache_data
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
        return c.fetchall()
    except Exception as e:
        st.error(f"Failed to fetch data: {e}")
        return []

def extract_youtube_id(url):
    regex = r"(?<=v=)[^&#]+"
    match = re.search(regex, url)
    if match:
        return match.group(0)
    if 'youtu.be' in url:
        return url.split('/')[-1]
    return None

def main_page():
    st.title('FantaPesAmici TV')
    st.markdown("---")

    st.markdown("""
        <h2 style='font-weight: bold; font-size: 24px;'>Opzioni di Filtro</h2>
        """, unsafe_allow_html=True)

    competitions = load_competitions()
    teams = load_teams()
    team_names = [team[0] for team in teams]

    selected_player = st.selectbox("Select Player", ['All'] + team_names, index=0)
    selected_competition = st.selectbox("Select Competition Type", ['All'] + competitions, index=0)

    st.markdown("---")

    data = view_filtered_data(selected_player, selected_competition)

    team_dict = dict(teams)

    for entry in data:
        youtube_id = extract_youtube_id(entry[0])
        competition_type, player1, player2, created_at = entry[1], entry[2], entry[3], entry[4]
        if youtube_id:
            logo1 = team_dict.get(player1, "")
            logo2 = team_dict.get(player2, "")
            st.markdown(f"""
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
                <div style="margin-bottom: 20px;">
                    <iframe width="560" height="315" src="https://www.youtube.com/embed/{youtube_id}" frameborder="0" allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture" allowfullscreen></iframe>
                </div>
                {created_at}
            """, unsafe_allow_html=True)
            st.markdown("---")

def view_filtered_data(player, competition):
    query = 'SELECT youtube_link, competition_type, player1, player2, created_at FROM match_data'
    conditions, params = [], []
    if player != 'All':
        conditions.append('(player1 = ? OR player2 = ?)')
        params.extend([player, player])
    if competition != 'All':
        conditions.append('competition_type = ?')
        params.append(competition)
    if conditions:
        query += ' WHERE ' + ' AND '.join(conditions)
    query += ' ORDER BY created_at DESC'
    c.execute(query, params)
    return c.fetchall()

def get_competition_stats():
    try:
        c.execute('''
            SELECT player1, competition_type, COUNT(*) as count
            FROM match_data
            WHERE competition_type IN (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            GROUP BY player1, competition_type
            ORDER BY player1
        ''', ("LEGA A", "LEGA B", "LEGA C", "Final Eight Gold", "Final Eight Silver", "Final Eight Bronze", "GOLDEN FINAL", "SILVER FINAL", "BRONZE FINAL", "Amichevole", "COPPA DELLE LEGHE"))
        return c.fetchall()
    except Exception as e:
        st.error(f"Failed to fetch competition stats: {e}")
        return []

def stats_page():
    st.title('Statistiche delle Dirette Stagione 1')
    data = get_competition_stats()
    if data:
        import pandas as pd
        from collections import defaultdict

        competition_counts = defaultdict(lambda: defaultdict(int))
        for player, competition, count in data:
            if competition in ["LEGA A", "LEGA B", "LEGA C"]:
                category = "LEGA"
            elif competition in ["Final Eight Gold", "Final Eight Silver", "Final Eight Bronze", "GOLDEN FINAL", "SILVER FINAL", "BRONZE FINAL"]:
                category = "Final Eight"
            elif competition == "Amichevole":
                category = "Amichevole"
            elif competition == "COPPA DELLE LEGHE":
                category = "COPPA DELLE LEGHE"
            else:
                continue
            competition_counts[player][category] += count

        df = pd.DataFrame.from_dict(competition_counts, orient='index').fillna(0).astype(int)
        df.index.name = 'Player Name'
        df.columns.name = 'Competition'
        st.table(df)
    else:
        st.write("No data available.")

def form_page():
    st.title('Match Submission Form')
    competitions = load_competitions()
    youtube_link = st.text_input('YouTube Link for the Online Match')

    with st.form(key='match_form'):
        competition_type = st.selectbox('Type of Competition', competitions)
        team_names = [team[0] for team in load_teams()]
        player1 = st.selectbox('Casa', team_names)
        player2 = st.selectbox('Trasferta', team_names)
        submitted = st.form_submit_button('Submit')
        if submitted:
            if not youtube_link.strip():
                st.error('Please enter a valid YouTube link.')
            else:
                add_data(youtube_link, competition_type, player1, player2)
                st.success('Submission successful!')

def irpef_calculation_page():
    st.title('Calcolo IRPEF')
    team_names = [team[0] for team in load_teams()]
    team_name = st.selectbox('Nome della squadra', team_names)
    average_age = st.number_input('Età media della squadra', min_value=0.0, format="%.1f")
    salary_input = st.text_input("Monte ingaggio della squadra (€)", value="")

    if salary_input:
        try:
            salary = float(salary_input.replace(".", "").replace(",", ""))
            formatted_salary = f"{salary:,.0f}".replace(",", ".")
            st.write("Monte ingaggio inserito: €" + formatted_salary)
        except ValueError:
            st.error("Inserire un numero valido.")
    else:
        salary = 0

    if st.button('Calcola'):
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
        else:
            tax_rate = 25
        tax_to_pay = (tax_rate / 100) * salary
        st.success(f"La tua IRPEF da pagare ammonta a €{tax_to_pay:,.0f} ({tax_rate}% del monte ingaggio).".replace(",", "."))

def delete_youtube_entry(youtube_link):
    try:
        c.execute("DELETE FROM match_data WHERE youtube_link=?", (youtube_link,))
        conn.commit()
        st.success("Entry deleted successfully.")
    except Exception as e:
        st.error(f"Failed to delete entry: {e}")

def delete_invalid_entries():
    try:
        c.execute("DELETE FROM match_data WHERE youtube_link IS NULL OR youtube_link = '' OR youtube_link NOT LIKE '%youtube.com/%'")
        conn.commit()
        st.success("Invalid entries have been successfully deleted.")
    except Exception as e:
        st.error(f"Failed to delete invalid entries: {e}")

def admin_page():
    st.title("Admin Tools")

    youtube_link = st.text_input("Enter the YouTube link to delete:")
    if st.button("Delete YouTube Entry"):
        delete_youtube_entry(youtube_link)

    if st.sidebar.button("Delete Invalid Entries"):
        delete_invalid_entries()

    data = view_all_data()
    st.write(data)

    if os.path.exists(DB_FILE_PATH):
        with open(DB_FILE_PATH, "rb") as fp:
            st.sidebar.download_button(
                label="Download Database",
                data=fp,
                file_name="matches.db",
                mime="application/octet-stream"
            )

# Main Application
apply_custom_css()
add_sidebar_logo()
initialize_database()

st.sidebar.title('Menu')
page = st.sidebar.radio(' ', ('Live Streaming', 'Carica Link', 'Statistiche', 'Calcolo IRPEF'))

st.sidebar.title('Admin Tools')
password = st.sidebar.text_input("Enter password:", type='password')

if password == CORRECT_PASSWORD:
    admin_page()
else:
    if password:
        st.sidebar.error("Password incorrect, please try again.")

if page == 'Live Streaming':
    main_page()
elif page == 'Carica Link':
    form_page()
elif page == 'Statistiche':
    stats_page()
elif page == 'Calcolo IRPEF':
    irpef_calculation_page()
