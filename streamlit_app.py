import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
from pinotdb import connect
import pandas as pd

# Connect to Apache Pinot
conn = connect(host='47.129.174.92', port=8099, path='/query/sql', schema='http')
curs = conn.cursor()

# Set the Streamlit page configuration
st.set_page_config(layout="wide", page_title="Real-Time Dashboard")

# Fetch data and define graphs
# Graph 1: Stacked Bar Chart (Top-Right)
def graph1():
    curs.execute('''SELECT 
      DOG_MENU,
      COOK_LV,
      SUM(QUANTITY) AS total_quantity
    FROM 
      TP3_dogmenu
    GROUP BY 
      DOG_MENU, COOK_LV
    ORDER BY 
      total_quantity DESC
    LIMIT 10;''')
    data = [row for row in curs.fetchall()]

    menu_items = list(set(row[0] for row in data))
    cooking_levels = list(set(row[1] for row in data))
    menu_quantities = {menu: {level: 0 for level in cooking_levels} for menu in menu_items}

    for row in data:
        menu_quantities[row[0]][row[1]] += row[2]

    colors = {"Rare": "#eab676", "Medium": "#e28743", "Well-done": "#873e23"}
    fig = go.Figure()
    for level in cooking_levels:
        fig.add_trace(go.Bar(
            x=menu_items,
            y=[menu_quantities[menu][level] for menu in menu_items],
            name=level,
            marker_color=colors.get(level, "#CCCCCC")
        ))
    fig.update_layout(
        barmode='stack',
        title='Stacked Bar Chart of Dog Menu Quantities by Cooking Level',
        xaxis=dict(title='Dog Menu Items'),
        yaxis=dict(title='Total Quantity'),
        legend_title='Cooking Level'
    )
    return fig

# Graph 2: Leaderboard Table (Bottom-Left)
def graph2():
    curs.execute('''SELECT 
      USERID,
      COUNT(ORDERID) AS total_orders
    FROM 
      TP3_dogmenu
    GROUP BY 
      USERID
    ORDER BY 
      total_orders DESC
    LIMIT 10;''')
    leaderboard_data = [row for row in curs.fetchall()]
    ranked_data = [[rank + 1] + list(row) for rank, row in enumerate(leaderboard_data)]
    df_leaderboard = pd.DataFrame(ranked_data, columns=['Rank', 'UserID', 'Total Orders'])
    max_orders = df_leaderboard['Total Orders'].max()
    min_orders = df_leaderboard['Total Orders'].min()
    normalized_orders = (df_leaderboard['Total Orders'] - min_orders) / (max_orders - min_orders)
    gradient_colors = [
        f'rgba({255 - int(255 * value)}, {int(200 + 55 * value)}, {int(255 * value)}, 0.8)'
        for value in normalized_orders
    ]
    fig = go.Figure(data=[go.Table(
        header=dict(
            values=['<b>Rank</b>', '<b>UserID</b>', '<b>Total Orders</b>'],
            fill_color='#074d89',
            font=dict(color='white', size=14),
            align='center'
        ),
        cells=dict(
            values=[
                df_leaderboard['Rank'],
                df_leaderboard['UserID'],
                df_leaderboard['Total Orders']
            ],
            fill_color=[
                ['white'] * len(df_leaderboard),
                ['white'] * len(df_leaderboard),
                gradient_colors
            ],
            align='center',
            font=dict(size=12)
        )
    )])
    fig.update_layout(
        title='Leaderboard of Top Users by Total Orders',
        title_x=0.5
    )
    return fig

# Graph 3: Heatmap (Top-Left)
def graph3():
    curs.execute('''SELECT 
      DOG_BREED,
      DRINKS_MENU,
      COUNT(*) AS pair_count
    FROM 
      TP3_dogmenu
    GROUP BY 
      DOG_BREED, DRINKS_MENU
    ORDER BY 
      pair_count DESC
    LIMIT 10;''')
    table2 = [row for row in curs.fetchall()]
    df = pd.DataFrame(table2, columns=['DOG_BREED', 'DRINKS_MENU', 'pair_count'])
    df = df[df['pair_count'] > 0]
    fig = px.density_heatmap(
        df,
        x='DOG_BREED',
        y='DRINKS_MENU',
        z='pair_count',
        color_continuous_scale=[
            [0.0, 'rgb(64, 0, 75)'], [0.1, 'rgb(118, 42, 131)'], [0.2, 'rgb(153, 112, 171)'],
            [0.3, 'rgb(194, 165, 207)'], [0.4, 'rgb(231, 212, 232)'], [0.5, 'rgb(247, 247, 247)'],
            [0.7, 'rgb(254, 224, 144)'], [0.9, 'rgb(253, 174, 97)'], [1.0, 'rgb(215, 48, 39)']
        ],
        labels={'pair_count': 'Pair Count'},
        title='Heatmap of Pairing Count Between Dog Breed and Drinks Menu'
    )
    fig.update_layout(
        xaxis_title='Dog Breed',
        yaxis_title='Drinks Menu',
        coloraxis_colorbar=dict(title='Pair Count')
    )
    return fig

# Graph 4: Geographic Map (Bottom-Right)
def graph4():
    curs.execute('''SELECT 
      regionid, 
      COUNT(*) AS total_count
    FROM 
      TP2_users
    GROUP BY 
      regionid
    ORDER BY 
      total_count DESC;''')
    region_data = [row for row in curs.fetchall()]
    region_coordinates = {
        "Region_1": {"province": "Bangkok", "lat": 13.7563, "lon": 100.5018},
        "Region_2": {"province": "Chiang Mai", "lat": 18.7883, "lon": 98.9867},
        "Region_3": {"province": "Phuket", "lat": 7.8804, "lon": 98.3923},
        "Region_4": {"province": "Khon Kaen", "lat": 16.4322, "lon": 102.8236},
        "Region_5": {"province": "Nakhon Ratchasima", "lat": 14.9799, "lon": 102.0977},
        "Region_6": {"province": "Chonburi", "lat": 13.3611, "lon": 100.9847},
        "Region_7": {"province": "Songkhla", "lat": 7.1897, "lon": 100.5953},
        "Region_8": {"province": "Udon Thani", "lat": 17.4138, "lon": 102.7877},
        "Region_9": {"province": "Surat Thani", "lat": 9.1382, "lon": 99.3214},
        "Region_10": {"province": "Nakhon Si Thammarat", "lat": 8.4333, "lon": 99.9630}
    }
    region_df = pd.DataFrame(region_data, columns=['regionid', 'total_count'])
    region_df['province'] = region_df['regionid'].map(lambda x: region_coordinates[x]["province"])
    region_df['lat'] = region_df['regionid'].map(lambda x: region_coordinates[x]["lat"])
    region_df['lon'] = region_df['regionid'].map(lambda x: region_coordinates[x]["lon"])
    fig = px.scatter_geo(
        region_df,
        lat="lat",
        lon="lon",
        text="province",
        size="total_count",
        color="total_count",
        title="Thailand Region Counts",
        labels={"total_count": "Count"}
    )
    fig.update_geos(
        visible=True,
        resolution=50,
        showcountries=True,
        countrycolor="Black",
        showcoastlines=True,
        coastlinecolor="Gray",
        showland=True,
        landcolor="LightYellow",
        center={"lat": 13.736717, "lon": 100.523186},
        projection_scale=6.5
    )
    return fig

# Streamlit Layout
col1, col2 = st.columns(2)
with col1:
    st.plotly_chart(graph3(), use_container_width=True)  # Top-Left
    st.plotly_chart(graph2(), use_container_width=True)  # Bottom-Left
with col2:
    st.plotly_chart(graph1(), use_container_width=True)  # Top-Right
    st.plotly_chart(graph4(), use_container_width=True)  # Bottom-Right
