import os
import sqlite3
from datetime import timedelta
from sqlite3 import Connection

import pandas as pd
import plotly.graph_objects as go
import plotly.io as pio
import streamlit as st
from plotly.subplots import make_subplots


pio.templates.default = "plotly_white"

userDir = os.path.expanduser("~")
URI_SQLITE_DB = userDir + "/BirdNET-Pi/scripts/birds.db"


st.set_page_config(layout="wide")

# Remove whitespace from the top of the page
st.markdown(
    """
        <style>
               .css-18e3th9 {
                    padding-top: 2.5rem;
                    padding-bottom: 10rem;
                    padding-left: 5rem;
                    padding-right: 5rem;
                }
               .css-1d391kg {
                    padding-top: 3.5rem;
                    padding-right: 1rem;
                    padding-bottom: 3.5rem;
                    padding-left: 1rem;
                }
        </style>
        """,
    unsafe_allow_html=True,
)


# @st.cache(hash_funcs={Connection: id})
# @st.cache(allow_output_mutation=True)
@st.experimental_singleton
def get_connection(path: str):
    return sqlite3.connect(path, check_same_thread=False)


def get_data(conn: Connection):
    df1 = pd.read_sql("SELECT * FROM detections", con=conn)
    return df1


def get_data2(conn: Connection):
    df1 = pd.read_sql("SELECT * FROM daylight", con=conn)
    return df1


conn = get_connection(URI_SQLITE_DB)


df_daylight = get_data2(conn)
df_daylight["sunr_min"] = [
    (int(m.split(":")[0]) * 60 + int(m.split(":")[1])) for m in df_daylight["sunrise"]
]
df_daylight["suns_min"] = [
    (int(m.split(":")[0]) * 60 + int(m.split(":")[1])) for m in df_daylight["sunset"]
]
df_daylight["dawn_min"] = [
    (int(m.split(":")[0]) * 60 + int(m.split(":")[1])) for m in df_daylight["dawn"]
]
df_daylight["dusk_min"] = [
    (int(m.split(":")[0]) * 60 + int(m.split(":")[1])) for m in df_daylight["dusk"]
]


# def get_db():
#
#
#     conn = get_connection(URI_SQLITE_DB)
#     df = get_data(conn)
#     df2 = df.copy()
#     df2['DateTime'] = pd.to_datetime(df2['Date'] + " " + df2['Time'])
#     df2 = df2.set_index('DateTime')
#     return df2
#
# df2 = get_db()

try:
    df2 = st.session_state["df2"]
except:
    df2 = pd.read_sql("SELECT * FROM detections", con=conn)
    df2["DateTime"] = pd.to_datetime(df2["Date"] + " " + df2["Time"])
    df2 = df2.set_index("DateTime")

Start_Date = pd.to_datetime(df2.index.min()).date()
End_Date = pd.to_datetime(df2.index.max()).date()

#    cols1, cols2 = st.columns((1, 1))
start_date, end_date = st.sidebar.slider(
    "Date Range",
    min_value=Start_Date - timedelta(days=1),
    max_value=End_Date,
    value=(Start_Date, End_Date),
    help="Select start and end date, if same date get a clockplot for a single day",
)

# start_date, end_date = cols1.date_input(
#     "Date Input for Analysis - select Range for single specie analysis, select single date for daily view",
#     value=(Start_Date, End_Date),
#     min_value=Start_Date,
#     max_value=End_Date)

# start_date = datetime(2022 ,5 ,17).date()
# end_date = datetime(2022 ,5 ,17).date()


@st.experimental_memo(persist="disk")
def date_filter(df, start_date, end_date):
    filt = (df2.index >= pd.Timestamp(start_date)) & (
        df2.index <= pd.Timestamp(end_date + timedelta(days=1))
    )
    df = df[filt]
    return df


df2 = date_filter(df2, start_date, end_date)


resample_sel = st.sidebar.radio(
    "Resample Resolution",
    ("15 minutes", "Hourly"),
    index=0,
    help="Select resolution for single day - larger times run faster",
)

resample_times = {"15 minutes": "15min", "Hourly": "1H"}
resample_time = resample_times[resample_sel]


@st.experimental_memo(persist="disk")
def time_resample(df, resample_time):
    if resample_time == "Raw":
        df_resample = df["Com_Name"]

    else:
        df_resample = (
            df.resample(resample_time)["Com_Name"].aggregate("unique").explode()
        )

    return df_resample


top_bird = df2["Com_Name"].mode()[0]
df5 = time_resample(df2, resample_time)

# Create species count for selected date range


Specie_Count = df5.value_counts()

# Create Hourly Crosstab
hourly = pd.crosstab(df5, df5.index.hour, dropna=True, margins=True)

# Filter on species
species = list(hourly.sort_values("All", ascending=False).index)

font_size = 15


try:
    idx = max(species.index(st.session_state["specie"]) - 1, 0)
except:
    idx = 0


specie = st.sidebar.selectbox(
    "Which bird would you like to explore for the dates "
    + str(start_date)
    + " to "
    + str(end_date)
    + "?",
    species[1:],
    key='specie',
    index=idx,
)

df_counts = int(hourly[hourly.index == specie]["All"])
fig = make_subplots(
    rows=2,
    cols=1,
    row_heights=[0.75, 0.25],
    specs=[[{"rowspan": 1}], [{"rowspan": 1}]],
    shared_xaxes=True,
    vertical_spacing=0,
)


df4 = df2["Com_Name"][df2["Com_Name"] == specie].resample(resample_time).count()

df4.index = [df4.index.date, df4.index.time]
day_hour_freq = df4.unstack().fillna(0)

while day_hour_freq.index.min() != df2.index.date.min():
    new_day = pd.DataFrame(
        index=[day_hour_freq.index.min() - timedelta(days=1)],
        columns=day_hour_freq.columns,
    ).fillna(0)
    day_hour_freq = pd.concat([new_day, day_hour_freq])

while day_hour_freq.index.max() != df2.index.date.max():
    new_day = pd.DataFrame(
        index=[day_hour_freq.index.max() + timedelta(days=1)],
        columns=day_hour_freq.columns,
    ).fillna(0)
    day_hour_freq = pd.concat([day_hour_freq, new_day])


fig_x = [d.strftime("%d-%m-%Y") for d in day_hour_freq.index.tolist()]
fig_y = [h.hour * 60 + h.minute for h in day_hour_freq.columns.tolist()]
fig_z = day_hour_freq.values.transpose()

fig_sunr = df_daylight["sunr_min"][df_daylight["date"].isin(fig_x)]
fig_suns = df_daylight["suns_min"][df_daylight["date"].isin(fig_x)]
fig_dawn = df_daylight["dawn_min"][df_daylight["date"].isin(fig_x)]
fig_dusk = df_daylight["dusk_min"][df_daylight["date"].isin(fig_x)]

fig.add_trace(
    go.Heatmap(
        x=fig_x,
        y=fig_y,
        z=fig_z,
        autocolorscale=False,
        showlegend=True,
        name="Detections",
        showscale=False,
        colorbar=dict(len=0.5),
        #                                 colorscale='Blugrn',
        colorscale=[
            [0, "rgb(0, 0, 0)"],
            [1.0 / 10000, "rgb(16, 119, 26,1)"],
            # [0.25, "rgb(120, 120, 120)"],
            [1.0 / 1000, "rgb(16, 119, 26)"],
            # [0.5, "rgb(160, 160, 160)"],
            [1.0 / 100, "rgb(16, 119, 26)"],
            # [0.75, "rgb(210, 210, 210)"],
            [1.0, "rgb(16, 119, 26)"],
        ],
        hovertemplate="<i>Date<i>: %{x}" + "<br>Time: %{y}" + "<br>Detections: %{z}",
    ),
    row=1,
    col=1,
)

fig.add_trace(
    go.Scatter(
        x=fig_x,
        y=fig_dawn,
        showlegend=True,
        name="Darkness",
        fill="tozeroy",
        line_color="black",
    ),
    row=1,
    col=1,
)
fig.add_trace(
    go.Scatter(
        x=fig_x,
        y=fig_sunr,
        showlegend=True,
        name="Sunrise <br> Dawn",
        fill="tonexty",
        line_color="palegoldenrod",
    ),
    row=1,
    col=1,
)
fig.add_trace(
    go.Scatter(
        x=fig_x,
        y=fig_suns,
        showlegend=True,
        name="Daylight",
        fill="tonexty",
        line_color="white",
    ),
    row=1,
    col=1,
)
fig.add_trace(
    go.Scatter(
        x=fig_x,
        y=fig_dusk,
        showlegend=True,
        name="Dusk <br> Sunset",
        fill="tonexty",
        line_color="darkgoldenrod",
    ),
    row=1,
    col=1,
)

fig.update_yaxes(
    row=1,
    col=1,
    tickvals=[i * 60 for i in range(96)],
    ticktext=[
        str(timedelta(minutes=60 * x)) for x in range(96)
    ],  # [time.strftime('%H:%M', [time.gmtime(i*60*15) for i in range(96)])],
    title_text="Time",
)

fig.update_yaxes(row=2, col=1, title_text=f"Detections per {resample_time}")

fig.update_xaxes(row=2, col=1, title_text="Date", fixedrange=True)
fig.update_xaxes(row=1, col=1, fixedrange=True)

fig.update_layout(
    width=1500,
    height=750,
    title=f" Detections of {specie} on a {resample_time} basis between {start_date:%d-%m-%Y} and {end_date:%d-%m-%Y}",
)

daily = pd.crosstab(df5, df5.index.date, dropna=True, margins=True)

fig.add_trace(
    go.Bar(
        x=daily.columns[:-1],
        y=daily.loc[specie][:-1],
        showlegend=False,
        hovertemplate="<i>Date<i>: %{x}" + "<br> Detections: %{y}",
        marker_color="seagreen",
    ),
    row=2,
    col=1,
)

st.plotly_chart(
    fig, width=1500, height=750, use_container_width=False
)  # , config=config)
st.session_state