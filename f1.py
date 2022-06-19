import streamlit as st
import pydeck as pdk
from bs4 import BeautifulSoup
import numpy as np
import pandas as pd
import requests

from matplotlib.backends.backend_agg import RendererAgg
from matplotlib import pyplot as plt
from matplotlib.figure import Figure
import seaborn as sns

st.set_page_config(layout="wide")

_lock = RendererAgg.lock

### Data Import ###
color_dict = {'Red Bull': '#121145', 'Ferrari':'#DC0000', 'Mercedes':'#00D2BE', 'McLaren':'#FF8700', 'Alpine':'#0090FF', 
			  'Alfa Romeo':'#900000', 'AlphaTauri':'#2B4562', 'Aston Martin':'#006F62', 'Haas':'#FFFFFF', 'Williams':'#005AFF'}

def get_championship_standing(season):
    URL = 'https://www.racing-statistics.com/en/seasons/' + season
    page = requests.get(URL)
    soup = BeautifulSoup(page.content, 'html.parser')
    results = soup.find('div', {'class': 'blocks blocks2'}).find('table')
    
    table = []
    for row in results.select("tr")[1:]:
        table.append([td.get_text() for td in row.select("td")])
    standings = pd.DataFrame(table,columns=['row_num','remove_0','Driver','remove_1','Team','Points'])
    standings['Rank'] = np.arange(standings.shape[0])+1
    standings = standings.drop(['row_num', 'remove_0', 'remove_1'], axis=1)
    standings['Team'] = standings['Team'].replace(['Alpine F1 Team','Haas F1 Team'],['Alpine','Haas'])
    
    return standings

def get_grand_prix_results(season):
    URL = 'https://www.racing-statistics.com/en/seasons/' + season
    page = requests.get(URL)
    soup = BeautifulSoup(page.content, 'html.parser')
    results = soup.find('div', {'class': 'blocks blocks'}).find('table')
    
    table = []
    for row in results.select("tr")[1:]:
        table.append([td.get_text() for td in row.select("td")])
    gp_result = pd.DataFrame(table,columns=['remove_0','Race Date','Grand Prix','Circuit','remove_1','Driver','Team','# of Laps','Lap Time'])
    gp_result = gp_result.drop(['remove_0', 'remove_1'], axis=1)
    gp_result['Team'] = gp_result['Team'].replace(['Alpine F1 Team','Haas F1 Team'],['Alpine','Haas'])
    
    return gp_result

def get_constructor_standing(df):
    constructor = df.copy()
    constructor["Points"] = pd.to_numeric(constructor["Points"])
    constructor = constructor.groupby("Team").sum()
    constructor = constructor.drop(['Rank'], axis=1)
    constructor.sort_values("Points",ascending=False,inplace=True) 
    
    return constructor.reset_index()

champ_standings = get_championship_standing('2022')
champ_standings = champ_standings.iloc[:,[3,0,1,2]]

gp_results = get_grand_prix_results('2022')

constructor = get_constructor_standing(champ_standings)

circuit = pd.read_csv('f1_circuit.csv')

##############
### HELPER ###
##############

hide_table_row_index = """
            <style>
            tbody th {display:none}
            .blank {display:none}
            </style>
            """
st.markdown(hide_table_row_index, unsafe_allow_html=True)

def plot_points_per_team(df):
    rc = {'figure.figsize':(10,6),
          'axes.facecolor':'#0e1117',
          'axes.edgecolor': '#0e1117',
          'axes.labelcolor': 'white',
          'figure.facecolor': '#0e1117',
          'patch.edgecolor': '#0e1117',
          'text.color': 'white',
          'xtick.color': 'white',
          'ytick.color': 'white',
          'grid.color': 'grey',
          'font.size' : 8,
          'axes.labelsize': 15,
          'xtick.labelsize': 9,
          'ytick.labelsize': 12}

    plt.rcParams.update(rc)
    fig, ax = plt.subplots()
    ax.set(xlabel = "Team", ylabel = "Points")
    # if specific_team_colors:
    ax = sns.barplot(x="Team", y="Points", data=df, palette = color_dict)
    # else:
    # 	ax = sns.barplot(x="Team", y="Points", data=df, color = "#b80606")
    st.pyplot(fig)

#Circuit Map Helper
layer = pdk.Layer(
    "ScatterplotLayer",
    data=circuit,
    get_position='[lon, lat]',
    auto_highlight=True,
    pickable=True,
    get_color='[200, 30, 0, 160]',
    radius_min_pixels=5
)

view_state = pdk.ViewState(
    longitude=8.724596, latitude=20.294902, zoom=1, min_zoom=1, max_zoom=20
)

circuit_map = pdk.Deck(
			    map_style="https://basemaps.cartocdn.com/gl/voyager-gl-style/style.json",
			    layers=[layer],
			    initial_view_state=view_state,
			    tooltip={"html": "<b>Grand Prix:</b> {grand_prix} <br> <b>Circuit Name:</b> {name} <br> <b>Race Date:</b> {date} <br> <b>Circuit Length:</b> {circuit_length} km <br> <b>No. of Laps:</b> {number_of_laps} <br> <b>No. of Turns:</b> {number_of_turns}", 
			    		 "style": {"backgroundColor": "steelblue", "color": "white"}}
)

####################
### INTRODUCTION ###
####################
row0_spacer1, row0_1, row0_spacer2, row0_2, row0_spacer3 = st.columns((.1, 2.3, .1, 1.3, .1))
with row0_1:
    st.title('Formula 1 2022 🏎')
with row0_2:
    st.text("")
    st.subheader('Streamlit App by [Novie Chiuman](https://www.linkedin.com/in/novie-chiuman-605332128/)')

row3_spacer1, row3_1, row3_spacer2 = st.columns((.1, 3.2, .1))
with row3_1:
    st.markdown("Hello folks! This is a simple weekend project that I recently worked on in order to learn Streamlit and BeautifulSoup.")
    st.markdown("Data is sourced from www.racing-statistics.com and is updated regularly!")
    st.markdown("Learning resources: https://github.com/tylerjrichards/streamlit_goodreads_app and https://github.com/tdenzl/BuLiAn")

#################
### STANDINGS ###
#################
row1_spacer1, row1_1, row1_spacer2 = st.columns((.2, 7.1, .2))
with row1_1:
    st.header("Current Standings 1️⃣")
    st.markdown("See who's on top.")

row2_space1, row2_1, row2_space2, row2_2, row2_space3 = st.columns((.1, 1, .1, 1, .1))

with row2_1, _lock:
    st.subheader("Driver Standing")
    st.markdown("**{}** is currently #1".format(champ_standings.iloc[0]['Driver']))
    st.table(champ_standings)

with row2_2, _lock:
    st.subheader("Constructor Standing")
    st.markdown("**{}** is currently #1".format(constructor.iloc[0]['Team']))
    st.table(constructor)
    plot_points_per_team(constructor)

##################
### GRAND PRIX ###
##################
row3_spacer1, row3_1, row3_spacer2 = st.columns((.2, 7.1, .2))
with row3_1:
    st.header('2022 Grand Prix Results 🏁')
    st.table(gp_results)

####################
### CIRCUIT MAPS ###
####################
row4_spacer1, row4_1, row4_spacer2 = st.columns((.2, 7.1, .2))
with row4_1:
    st.header("2022 Circuits 🗺")
    # st.map(circuit, zoom=1, use_container_width=True)
    st.pydeck_chart(circuit_map)
    st.subheader("Statistics 📊")
    st.markdown("**{}** is the longest circuit with circuit length of **{}** km."
    	.format(circuit.sort_values("circuit_length",ascending=False).iloc[0]['name'], circuit.sort_values("circuit_length",ascending=False).iloc[0]['circuit_length']))
    st.markdown("**{}** is the shortest circuit with circuit length of **{}** km."
    	.format(circuit.sort_values("circuit_length",ascending=True).iloc[0]['name'], circuit.sort_values("circuit_length",ascending=True).iloc[0]['circuit_length']))
    st.markdown("The circuit with the most turns is **{}** with a whopping total of **{}** turns."
    	.format(circuit.sort_values("number_of_turns",ascending=False).iloc[0]['name'], circuit.sort_values("number_of_turns",ascending=False).iloc[0]['number_of_turns']))
    st.markdown("The circuit with the least number of turns is **{}** with only **{}** turns."
    	.format(circuit.sort_values("number_of_turns",ascending=True).iloc[0]['name'], circuit.sort_values("number_of_turns",ascending=True).iloc[0]['number_of_turns']))
    st.markdown("The average number of turns for a circuit on the 2022 calendar is **{}**.".format(np.int64(round(circuit['number_of_turns'].mean()))))