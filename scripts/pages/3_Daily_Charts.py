import os
import sqlite3
from datetime import timedelta
from sqlite3 import Connection

import pandas as pd
import plotly.graph_objects as go
import plotly.io as pio
import streamlit as st
from numpy import ma
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


@st.experimental_singleton
def get_connection(path: str):
    return sqlite3.connect(path, check_same_thread=False)


def get_data(conn: Connection):
    df1 = pd.read_sql("SELECT * FROM detections", con=conn)
    return df1


try:
    df2 = st.session_state["df2"]
except:
    conn = get_connection(URI_SQLITE_DB)
    df2 = pd.read_sql("SELECT * FROM detections", con=conn)
    df2["DateTime"] = pd.to_datetime(df2["Date"] + " " + df2["Time"])
    df2 = df2.set_index("DateTime")


@st.experimental_memo(persist="disk")
def time_resample(df, resample_time):
    if resample_time == "Raw":
        df_resample = df["Com_Name"]

    else:
        df_resample = (
            df.resample(resample_time)["Com_Name"].aggregate("unique").explode()
        )

    return df_resample


# Date as slider
Start_Date = pd.to_datetime(df2.index.min()).date()
End_Date = pd.to_datetime(df2.index.max()).date()
end_date = st.sidebar.date_input(
    "Date to View",
    min_value=Start_Date,
    max_value=End_Date,
    value=(End_Date),
    help="Select date for single day view",
)
start_date = end_date


@st.experimental_memo(persist="disk")
def date_filter(df, start_date, end_date):
    filt = (df2.index >= pd.Timestamp(start_date)) & (
        df2.index <= pd.Timestamp(end_date + timedelta(days=1))
    )
    df = df[filt]
    return df


resample_sel = st.sidebar.radio(
    "Resample Resolution",
    ("Raw", "15 minutes", "Hourly"),
    index=1,
    help="Select resolution for single day - larger times run faster",
)


resample_times = {"Raw": "Raw", "15 minutes": "15min", "Hourly": "1H"}
resample_time = resample_times[resample_sel]


df2 = date_filter(df2, start_date, end_date)
df5 = time_resample(df2, resample_time)
Specie_Count = df5.value_counts()

# Create Hourly Crosstab
hourly = pd.crosstab(df5, df5.index.hour, dropna=True, margins=True)

# Filter on species
species = list(hourly.sort_values("All", ascending=False).index)
top_bird = df2["Com_Name"].mode()[0]

df2 = date_filter(df2, start_date, end_date)

st.write(
    "<style>div.row-widget.stRadio > div{flex-direction:row;justify-content: left;} </style>",
    unsafe_allow_html=True,
)
st.write(
    "<style>div.st-bf{flex-direction:column;} div.st-ag{font-weight:bold;padding-left:2px;}</style>",
    unsafe_allow_html=True,
)

top_N = st.sidebar.slider(
    "Select Number of Birds to Show",
    min_value=1,
    max_value=len(Specie_Count),
    value=min(10, len(Specie_Count)),
)

top_N_species = df5.value_counts()[:top_N]

font_size = 15


fig = make_subplots(
    rows=1,
    cols=2,
    specs=[[{"type": "xy", "rowspan": 1}, {"type": "xy", "rowspan": 1}]],
    subplot_titles=(
        "<b>Top " + str(top_N) + " Species For " + str(start_date) + "</b>",
        "<b>Daily "
        + str(start_date)
        + " Detections on "
        + resample_sel
        + " interval</b>",
    ),
    shared_yaxes="all",
    horizontal_spacing=0,
)

df6 = df5.to_frame(name="Com_Name")
readings = top_N

plt_topN_today = df6["Com_Name"].value_counts()[:readings]
freq_order = pd.value_counts(df6["Com_Name"]).iloc[:readings].index

fig.add_trace(
    go.Bar(
        y=plt_topN_today.index,
        x=plt_topN_today,
        marker_color="seagreen",
        orientation="h",
    ),
    row=1,
    col=1,
)


df6["Hour of Day"] = [r.hour for r in df6.index.time]
heat = pd.crosstab(df6["Com_Name"], df6["Hour of Day"])
# Order heatmap Birds by frequency of occurrance
heat.index = pd.CategoricalIndex(heat.index, categories=freq_order)
heat.sort_index(level=0, inplace=True)

heat_plot_values = ma.log(heat.values).filled(0)

hours_in_day = pd.Series(data=range(0, 24))
heat_frame = pd.DataFrame(data=0, index=heat.index, columns=hours_in_day)

heat = (heat + heat_frame).fillna(0)


labels = heat.values.astype(int).astype("str")
labels[labels == "0"] = ""
fig.add_trace(
    go.Heatmap(
        x=heat.columns,
        y=heat.index,
        z=heat.values,
        xgap=1,
        ygap=1,
        showscale=False,
        name=None,
        text=labels,
        texttemplate="%{text}",
        colorscale="Blugrn",
        hovertemplate="Time: %{x}" + "<br>Specie: %{y}" + "<br>Detections: %{z}",
    ),
    row=1,
    col=2,
)

fig.update_xaxes(
    row=1, col=1, title_text=f"Detections on {resample_time} interval", fixedrange=True
)
fig.update_xaxes(
    row=1,
    col=2,
    title_text="Time",
    fixedrange=True,
)

fig.update_yaxes(
    visible=True,
    autorange="reversed",
    ticks="inside",
    tickson="boundaries",
    ticklen=10000,
    showgrid=True,
)
fig.update_layout(xaxis_ticks="inside", margin=dict(l=0, r=0, t=50, b=0))

st.plotly_chart(fig, use_container_width=True)  # , config=config)
