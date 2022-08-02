import json
import os
import sqlite3
from datetime import timedelta
from sqlite3 import Connection

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import plotly.io as pio
import requests
import streamlit as st
import wikipedia
from plotly.subplots import make_subplots


pio.templates.default = "plotly_white"

userDir = os.path.expanduser("~")
URI_SQLITE_DB = userDir + "/BirdNET-Pi/scripts/birds.db"


st.set_page_config(layout="wide")
font_size = 15
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


# @st.experimental_singleton
def get_connection(path: str):
    return sqlite3.connect(path, check_same_thread=False)


def get_data(conn: Connection):
    df1 = pd.read_sql("SELECT * FROM detections", con=conn)
    return df1


def get_db():
    conn = get_connection(URI_SQLITE_DB)
    df = get_data(conn)
    df2 = df.copy()
    df2["DateTime"] = pd.to_datetime(df2["Date"] + " " + df2["Time"])
    df2 = df2.set_index("DateTime")
    return df2


df2 = get_db()


Start_Date = pd.to_datetime(df2.index.min()).date()
End_Date = pd.to_datetime(df2.index.max()).date()

start_date, end_date = st.sidebar.slider(
    "Date Range",
    min_value=Start_Date - timedelta(days=1),
    max_value=End_Date,
    value=(Start_Date, End_Date),
    help="Select start and end date, if same date get a clockplot for a single day",
)


@st.experimental_memo
def date_filter(df, start_date, end_date):
    filt = (df2.index >= pd.Timestamp(start_date)) & (
        df2.index <= pd.Timestamp(end_date + timedelta(days=1))
    )
    df = df[filt]
    return df


df2 = date_filter(df2, start_date, end_date)
st.write(
    "<style>div.row-widget.stRadio > div{flex-direction:row;justify-content: left;} </style>",
    unsafe_allow_html=True,
)
st.write(
    "<style>div.st-bf{flex-direction:column;} div.st-ag{font-weight:bold;padding-left:2px;}</style>",
    unsafe_allow_html=True,
)

# st.session_state.df2 = df2
resample_sel = st.sidebar.radio(
    "Resample Resolution",
    ("Raw", "15 minutes", "Hourly"),
    index=1,
    help="Select resolution for single day - larger times run faster",
)
resample_times = {"Raw": "Raw", "15 minutes": "15min", "Hourly": "1H"}
resample_time = resample_times[resample_sel]


@st.experimental_memo
def time_resample(df, resample_time):
    if resample_time == "Raw":
        df_resample = df["Com_Name"]
    else:
        df_resample = (
            df.resample(resample_time)["Com_Name"].aggregate("unique").explode()
        )
    return df_resample


df5 = time_resample(df2, resample_time)


Specie_Count = df5.value_counts()

# Create Hourly Crosstab
hourly = pd.crosstab(df5, df5.index.hour, dropna=True, margins=True)

# Filter on species
species = list(hourly.sort_values("All", ascending=False).index)

try:
    idx = max(species.index(st.session_state["specie"]), 0)
except:
    idx = 0


specie = st.sidebar.selectbox(
    "Which bird would you like to explore for the dates "
    + str(start_date)
    + " to "
    + str(end_date)
    + "?",
    species,
    key="specie",
    index=idx,
)

if specie == "All":
    top_N = st.sidebar.slider(
        "Select Number of Birds to Show",
        min_value=1,
        max_value=len(Specie_Count),
        value=min(10, len(Specie_Count)),
    )

    top_N_species = df5.value_counts()[:top_N]

    df_counts = int(hourly[hourly.index == specie]["All"])
    fig = make_subplots(
        rows=3,
        cols=2,
        specs=[
            [{"type": "xy", "rowspan": 3}, {"type": "polar", "rowspan": 2}],
            [{"rowspan": 1}, {"rowspan": 1}],
            [None, {"type": "xy", "rowspan": 1}],
        ],
        subplot_titles=(
            "<b>Top "
            + str(top_N)
            + " Species in Date Range "
            + str(start_date)
            + " to "
            + str(end_date)
            + "<br>for "
            + str(resample_sel)
            + " sampling interval."
            + "</b>",
            "Total Detect:" + str("{:,}".format(df_counts))
            # +   '   Confidence Max:' + str(
            #     '{:.2f}%'.format(max(df2[df2['Com_Name'] == specie]['Confidence']) * 100)) +
            # '   ' + '   Median:' + str(
            #     '{:.2f}%'.format(np.median(df2[df2['Com_Name'] == specie]['Confidence']) * 100))
        ),
    )
    fig.layout.annotations[1].update(x=0.7, y=0.25, font_size=15)

    fig.add_trace(
        go.Bar(
            y=top_N_species.index,
            x=top_N_species,
            orientation="h",
            marker_color="seagreen",
        ),
        row=1,
        col=1,
    )

    fig.update_layout(
        margin=dict(l=0, r=0, t=50, b=0), yaxis={"categoryorder": "total ascending"}
    )

    # Set 360 degrees, 24 hours for polar plot
    theta = np.linspace(0.0, 360, 24, endpoint=False)

    specie_filt = df5 == specie
    df3 = df5[specie_filt]

    detections2 = pd.crosstab(df3, df3.index.hour)

    d = pd.DataFrame(np.zeros((23, 1))).squeeze()
    detections = hourly.loc[specie]
    detections = (d + detections).fillna(0)
    fig.add_trace(
        go.Barpolar(r=detections, theta=theta, marker_color="seagreen"), row=1, col=2
    )
    fig.update_layout(
        autosize=False,
        width=1000,
        height=500,
        showlegend=False,
        polar=dict(
            radialaxis=dict(
                tickfont_size=font_size,
                showticklabels=False,
                hoverformat="#%{theta}: <br>Popularity: %{percent} </br> %{r}",
            ),
            angularaxis=dict(
                tickfont_size=font_size,
                rotation=-90,
                direction="clockwise",
                tickmode="array",
                tickvals=[
                    0,
                    15,
                    35,
                    45,
                    60,
                    75,
                    90,
                    105,
                    120,
                    135,
                    150,
                    165,
                    180,
                    195,
                    210,
                    225,
                    240,
                    255,
                    270,
                    285,
                    300,
                    315,
                    330,
                    345,
                ],
                ticktext=[
                    "12am",
                    "1am",
                    "2am",
                    "3am",
                    "4am",
                    "5am",
                    "6am",
                    "7am",
                    "8am",
                    "9am",
                    "10am",
                    "11am",
                    "12pm",
                    "1pm",
                    "2pm",
                    "3pm",
                    "4pm",
                    "5pm",
                    "6pm",
                    "7pm",
                    "8pm",
                    "9pm",
                    "10pm",
                    "11pm",
                ],
                hoverformat="#%{theta}: <br>Popularity: %{percent} </br> %{r}",
            ),
        ),
    )

    daily = pd.crosstab(df5, df5.index.date, dropna=True, margins=True)
    fig.add_trace(
        go.Bar(x=daily.columns[:-1], y=daily.loc[specie][:-1], marker_color="seagreen"),
        row=3,
        col=2,
    )
    st.plotly_chart(fig, use_container_width=True)  # , config=config)

else:
    col1, col2 = st.columns(2)
    with col1:
        fig = make_subplots(
            rows=3,
            cols=1,
            specs=[
                [{"type": "polar", "rowspan": 2}],
                [{"rowspan": 1}],
                [{"type": "xy", "rowspan": 1}],
            ],
        )
        # Set 360 degrees, 24 hours for polar plot
        theta = np.linspace(0.0, 360, 24, endpoint=False)

        specie_filt = df5 == specie
        df3 = df5[specie_filt]

        detections2 = pd.crosstab(df3, df3.index.hour)

        d = pd.DataFrame(np.zeros((23, 1))).squeeze()
        detections = hourly.loc[specie]
        detections = (d + detections).fillna(0)
        fig.add_trace(
            go.Barpolar(r=detections, theta=theta, marker_color="seagreen"),
            row=1,
            col=1,
        )
        fig.update_layout(
            title=f"{specie} Detections between {start_date} and {end_date} on {resample_time} basis",
            autosize=False,
            width=1000,
            height=500,
            showlegend=False,
            polar=dict(
                radialaxis=dict(
                    tickfont_size=font_size,
                    showticklabels=False,
                    hoverformat="#%{theta}: <br>Popularity: %{percent} </br> %{r}",
                ),
                angularaxis=dict(
                    tickfont_size=font_size,
                    rotation=-90,
                    direction="clockwise",
                    tickmode="array",
                    tickvals=[
                        0,
                        15,
                        35,
                        45,
                        60,
                        75,
                        90,
                        105,
                        120,
                        135,
                        150,
                        165,
                        180,
                        195,
                        210,
                        225,
                        240,
                        255,
                        270,
                        285,
                        300,
                        315,
                        330,
                        345,
                    ],
                    ticktext=[
                        "12am",
                        "1am",
                        "2am",
                        "3am",
                        "4am",
                        "5am",
                        "6am",
                        "7am",
                        "8am",
                        "9am",
                        "10am",
                        "11am",
                        "12pm",
                        "1pm",
                        "2pm",
                        "3pm",
                        "4pm",
                        "5pm",
                        "6pm",
                        "7pm",
                        "8pm",
                        "9pm",
                        "10pm",
                        "11pm",
                    ],
                    hoverformat="#%{theta}: <br>Popularity: %{percent} </br> %{r}",
                ),
            ),
        )

        daily = pd.crosstab(df5, df5.index.date, dropna=True, margins=True)
        fig.add_trace(
            go.Bar(
                x=daily.columns[:-1], y=daily.loc[specie][:-1], marker_color="seagreen"
            ),
            row=3,
            col=1,
        )
        st.plotly_chart(fig, use_container_width=True)

    with col2:

        df_counts = int(hourly[hourly.index == specie]["All"])

        st.write("Total Detect: " + str("{:,}".format(df_counts)))
        st.write(
            "Confidence Max: "
            + str(
                "{:.2f}%".format(
                    max(df2[df2["Com_Name"] == specie]["Confidence"]) * 100
                )
            )
        )
        st.write(
            "Confidence Median: "
            + str(
                "{:.2f}%".format(
                    np.median(df2[df2["Com_Name"] == specie]["Confidence"]) * 100
                )
            )
        )

        WIKI_REQUEST = "http://en.wikipedia.org/w/api.php?action=query&prop=pageimages&format=json&piprop=original&titles="

        @st.experimental_singleton
        def get_wiki_image(search_term):
            try:
                result = wikipedia.search(search_term, results=1)
                wikipedia.set_lang("en")
                wkpage = wikipedia.WikipediaPage(title=result[0])
                title = wkpage.title
                response = requests.get(WIKI_REQUEST + title)
                json_data = json.loads(response.text)
                img_link = list(json_data["query"]["pages"].values())[0]["original"][
                    "source"
                ]
                return img_link
            except:
                return 0

        try:
            wiki_image = get_wiki_image(df2[df2["Com_Name"] == specie]["Sci_Name"][0])
            st.image(wiki_image, width=300)
            st.caption("Source: Wikipedia")
        except:
            st.title("Can't access image")

        specie_filter = df2[df2["Com_Name"] == specie]

        specie_filter2 = specie_filter[specie_filter["Manual_ID"] != "Not_Reviewed"]
        true_positives = len(specie_filter[specie_filter["Manual_ID"] == specie])
        false_positives = len(specie_filter2) - true_positives
        st.subheader("Manual ID's")
        st.write("True Positives:", true_positives)
        st.write("False Positives", false_positives)
