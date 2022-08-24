import os
import streamlit as st
import pandas as pd
import sqlite3
from sqlite3 import Connection
from st_aggrid import AgGrid, GridOptionsBuilder, JsCode, GridUpdateMode
import requests

import glob
import urllib3
import certifi
import json

st.set_page_config(layout="wide")

http = urllib3.PoolManager(cert_reqs="CERT_REQUIRED", ca_certs=certifi.where())

userDir = os.path.expanduser("~")
dir_path = userDir + "/BirdSongs/Extracted/By_Date/**/*.mp3"
sound_files = [os.path.basename(x) for x in glob.glob(dir_path, recursive=True)]


URI_SQLITE_DB = userDir + "/BirdNET-Pi/scripts/birds.db"

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


def get_connection(path: str):
    return sqlite3.connect(path, check_same_thread=False)


def get_data(conn: Connection):
    df1 = pd.read_sql("SELECT * FROM detections WHERE Com_Name == {specie}", con=conn)
    return df1


conn = get_connection(URI_SQLITE_DB)

species = df1 = pd.read_sql(
    "SELECT Com_Name, count(Com_Name)AS Frequency FROM detections GROUP BY Com_Name ORDER BY COUNT(Com_Name) DESC",
    con=conn,
)["Com_Name"].tolist()


try:
    idx = species.index(st.session_state["specie"])
except:
    idx = 0

specie = st.sidebar.selectbox(
    "Which bird would you like to review ?",
    species,
    help="Select specie to review",
    index=idx,
    key="specie",
)


try:
    df1 = st.session_state["df2"]
except:
    df1 = pd.read_sql("SELECT * FROM detections", con=conn)
    df1["DateTime"] = pd.to_datetime(df1["Date"] + " " + df1["Time"])
    df1 = df1.set_index("DateTime")


df2 = df1[df1["Com_Name"] == specie]

recordings1 = df2[df2["File_Name"].isin(sound_files)]


df_names = pd.read_csv(
    userDir + "/BirdNET-Pi/model/labels.txt",
    delimiter="_",
    names=["Sci_Name", "Com_Name"],
)
df_unknown = pd.DataFrame({"Sci_Name": ["UNKNOWN"], "Com_Name": ["UNKNOWN"]})
non_bird = [
    "Not_Reviewed",
    "Frog",
    "Insect",
    "Machine",
    "Noise",
    "Siren",
    "Aircraft",
    "Vehicle",
    "Rainfall",
    "Bell",
    "Ambulance",
    "Telephone",
    "Baby",
]
non_bird_sci = ["None"] * len(non_bird)
df_not_bird = pd.DataFrame({"Sci_Name": non_bird_sci, "Com_Name": non_bird})
df_names = pd.concat([df_unknown, df_not_bird, df_names], ignore_index=True)


col1, col2 = st.columns((1, 2))

with col2:
    data_select = st.sidebar.radio(
        "Review Sample Filter",
        ["All", "Reviewed", "Not_Reviewed"],
        horizontal=True,
        help="Filter samples for review",
    )
    data_sort = st.sidebar.radio(
        "Review Sample Sort",
        ["Date", "Confidence"],
        horizontal=True,
        help="Sort samples for review",
    )

    if data_select == "All":
        record = recordings1.sort_values(by=data_sort, ascending=False)
    elif data_select == "Reviewed":
        record = recordings1[recordings1["Manual_ID"] != "Not_Reviewed"].sort_values(
            by=data_sort, ascending=False
        )
    else:
        record = recordings1[recordings1["Manual_ID"] == data_select].sort_values(
            by=data_sort, ascending=False
        )

    data = record[["File_Name", "Manual_ID", "Rating", "Confidence"]]

    gb = GridOptionsBuilder.from_dataframe(data)
    gb.configure_default_column(groupable=True, value=True, enableRowGroup=True)
    gb.configure_selection(use_checkbox=True, pre_selected_rows=[0])
    style_color = (
        """
    function(params) {
        if (params.value == 'Not_Reviewed') {
            return {
                'color': 'white',
                'backgroundColor': 'gray'
            }
        } else if (params.value != """
        + f"{specie}"
        + """) {
            return {
                'color': 'black',
                'backgroundColor': 'red'
            }
        }
    };
    """
    )

    cellsytle_jscode = JsCode(
        """
    function(params) {
        if (params.value == 'Not_Reviewed') {
            return {
                'color': 'white',
                'backgroundColor': 'gray'
            }
        } else if (params.value == 'UNKNOWN') {
            return {
                'color': 'black',
                'backgroundColor': 'red'
            }
        }
    };
    """
    )

    gb.configure_column(
        "File_Name",
        cellStyle={"backgroundColor": "grey", "color": "white"},
        editable=True,
    )
    gb.configure_column("Manual_ID", cellStyle=cellsytle_jscode)
    st.header("Review Sample Selection")
    st.caption(
        "Select sample for review by ticking.  Filter and Sort selection in the sidebar or by clicking the headers in this table."
    )
    gridOptions = gb.build()
    grid_response = AgGrid(
        data,
        gridOptions=gridOptions,
        allow_unsafe_jscode=True,
        update_mode=GridUpdateMode.MODEL_CHANGED,
    )
    reviewed_filter = df1[df1["Manual_ID"] != "Not_Reviewed"]
    reviewed_filter["truth"] = (
        reviewed_filter["Com_Name"] == reviewed_filter["Manual_ID"]
    )
    reviewed_summary = pd.crosstab(
        reviewed_filter["Com_Name"], reviewed_filter["truth"]
    )
    # reviewed_summary['Percent True']= (reviewed_summary[True]/(reviewed_summary[True]+reviewed_summary[False])*100).astype(int)
    st.header("Review Summary")
    st.dataframe(reviewed_summary)

    try:
        recording = grid_response["selected_rows"][0]["File_Name"]
    except:
        st.write("Please Select a Recording to Review")
        recording = data["File_Name"][0]


date_specie = df2.loc[df2["File_Name"] == recording, ["Date", "Com_Name", "Sci_Name"]]
date_dir = date_specie["Date"].values[0]
specie_dir = date_specie["Com_Name"].values[0].replace(" ", "_")
sci_name = date_specie["Sci_Name"].values[0]
com_name = date_specie["Com_Name"].values[0]


xc_active = st.sidebar.checkbox(
    "Use Xeno-Canto Comparison?",
    help="Click here to access sound samples for comparison (Runs slower when checked)",
    value=False,
)
if xc_active:
    url = (
        "https://www.xeno-canto.org/api/2/recordings?query="
        + sci_name.replace(" ", "+")
        + "+q:A"
    )

    try:
        r = requests.get(url, timeout=10)
        data = json.loads(r.content.decode("utf-8"))

        if data["numRecordings"] == "0":
            url = (
                "https://www.xeno-canto.org/api/2/recordings?query="
                + com_name.replace(" ", "+")
                + "+q:A"
            )
            r = http.request("GET", url)
            data = json.loads(r.content.decode("utf-8"))

        df = pd.json_normalize(data, ["recordings"])

        st.sidebar.header("Xeno-Canto Reference Samples")
        xc_sample = st.sidebar.selectbox(
            "Xeno-Canto sample select",
            (0, 1, 2, 3, 4),
            help="Select from the top 5 Xeno-Canto samples for the selected species for comparison purposes",
        )

        sample = df["file"][xc_sample]

        spectro = "https:" + df["sono.med"][xc_sample]
        xc_id = df["id"][xc_sample]
        xc_en = df["en"][xc_sample]
        xc_rec = df["rec"][xc_sample]
        xc_cnt = df["cnt"][xc_sample]
        xc_lic = df["lic"][xc_sample]
        xc_url = df["url"][xc_sample]
        xc_lat = df["lat"][xc_sample]
        xc_lng = df["lng"][xc_sample]
        xc_date = df["date"][xc_sample]

        st.sidebar.image(spectro)
        st.sidebar.audio(sample)
        st.sidebar.text(
            f"XC sample: {xc_id}\nXC name: {xc_en}\nXC Contributor: {xc_rec}\nXC License: Unmodified"
        )
        st.sidebar.write(f"http:{xc_url}", unsafe_allow_html=True)
        st.sidebar.write(f"http:{xc_lic}", unsafe_allow_html=True)
    except:
        st.sidebar.write("Xeno Canto Unavailable")


with col1:
    try:
        st.image(
            userDir
            + "/BirdSongs/Extracted/By_Date/"
            + date_dir
            + "/"
            + specie_dir
            + "/"
            + recording
            + ".png"
        )
        st.audio(
            userDir
            + "/BirdSongs/Extracted/By_Date/"
            + date_dir
            + "/"
            + specie_dir
            + "/"
            + recording
        )
    except:
        st.title("RECORDING NOT AVAILABLE :(")

    with st.form("Review"):
        current_ID = df2.loc[df2["File_Name"] == recording]["Manual_ID"].values[0]
        st.write("Current Recording:", recording)
        st.write("Manual ID:", current_ID)
        st.write(
            "Manual Rating:",
            df2.loc[df2["File_Name"] == recording]["Rating"].values[0],
        )

        radio_index = current_ID != specie
        verified = st.radio(
            "Verification",
            ["True Positive", "False Positive"],
            horizontal=True,
            index=radio_index,
            help="Select True Positive/False Positive. Defaults to False Positive for un-reveiwed samples",
        )

        if verified == "False Positive":
            dropdown_index = int(
                df_names.loc[df_names["Com_Name"] == current_ID].index.values[0]
            )
            corrected = st.selectbox(
                "Manual ID?",
                df_names["Com_Name"],
                help="If False Positive, select correct specie, non-bird sound or UNKNOWN",
                index=dropdown_index,
            )
        else:
            corrected = st.selectbox(
                "Specie", df2.loc[df2["File_Name"] == recording]["Com_Name"]
            )
        #
        rating = st.select_slider(
            "Rating",
            options=["*****", "****", "***", "**", "*"],
            value="*",
            help="Select your rating for the sample quality - *=bad; ****=excellent",
        )

        db_ID = df2.loc[df2["File_Name"] == recording]["Manual_ID"][0]
        corrected_ID = corrected

        submitted = st.form_submit_button(
            "Commit to DB",
            help="When the ID and rating above have been entered, click to commit to Database",
        )

    if submitted:
        conn = get_connection(URI_SQLITE_DB)
        cursor = conn.cursor()
        cursor.execute(
            f""" UPDATE detections SET Manual_ID = "{corrected}" WHERE File_Name = "{recording}" """
        )
        cursor.execute(
            f""" UPDATE detections SET Rating = "{rating}" WHERE File_Name = "{recording}" """
        )
        conn.commit()
        df2 = pd.read_sql("SELECT * FROM detections", con=conn)
        df2["DateTime"] = pd.to_datetime(df2["Date"] + " " + df2["Time"])
        df2 = df2.set_index("DateTime")
        st.session_state.df2 = df2
        st.experimental_rerun()
