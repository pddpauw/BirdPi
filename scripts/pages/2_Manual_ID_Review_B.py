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

xc_active = st.sidebar.checkbox(
    "Use Xeno-Canto Comparison?",
    help="Click here to access sound samples for comparison (Runs slower when checked)",
    value=False,
)

specie = st.sidebar.selectbox(
    "Which bird would you like to review ?",
    species,
    help="Select specie to review",
    index=idx,
    key="specie",
)



df2 = pd.read_sql(f"SELECT * FROM detections WHERE Com_Name = '{specie}'", con=conn)
# df1["DateTime"] = pd.to_datetime(df1["Date"] + " " + df1["Time"])
# df2 = df1.set_index("DateTime")


sci_name = df2[df2['Com_Name']==specie]['Sci_Name'][0]
com_name = specie


if xc_active:
    url = (
        "https://www.xeno-canto.org/api/2/recordings?query="
        + sci_name.replace(" ", "+")
        + "+q:A"
    )

    try:
        r = requests.get(url, timeout=20)
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



#Create dataframe of possible names
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
df_current = pd.DataFrame({"Sci_Name": [sci_name], "Com_Name": [com_name]})
df_names = pd.concat([df_current, df_unknown, df_not_bird, df_names], ignore_index=True)


review_recordings=[]
recordings1 = df2[df2["File_Name"].isin(sound_files)]

with st.sidebar.form('Sample Filter'):
    #Filter and sort Review Samples
    data_select = st.radio(
        "Review Sample Filter",
        ["All", "Reviewed", "Not_Reviewed"],
        horizontal=True,
        help="Filter samples for review",
    )
    data_sort = st.radio(
        "Review Sample Sort",
        ["Date", "Confidence"],
        index = 0,
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
        record = recordings1[recordings1["Manual_ID"] == "Not_Reviewed"].sort_values(
            by=data_sort, ascending=False
        )
    data_select = st.slider(
        "Review Sample Number",
        min_value=1,
        max_value=5,
        
        help="Select number of samples for review",
    )
    pre_select= [x for x in range(data_select)]    
    data = record[["File_Name", "Manual_ID", "Rating", "Confidence"]]
    st.form_submit_button()

#Check if there are sound samples for that specie
if len(data)==0:
    specie_error=True
else:
    specie_error=False
   
selection = data.head(data_select)

review_recordings=[]
for i in range(len(selection)):
    review_recordings.append(selection.iloc[i]['File_Name'])
    

j=0
corrected_list=[]
rating_list = []

# try:
#     st.header("Sample Review Form")
with st.form("Review", clear_on_submit=True):
    if len(review_recordings)>0:
        for i in st.columns(len(review_recordings)):

              
            with i:
                date_specie = df2.loc[df2["File_Name"] == review_recordings[j], ["Date", "Com_Name", "Sci_Name", "Rating"]]
                date_dir = date_specie["Date"].values[0]
                specie_dir = date_specie["Com_Name"].values[0].replace(" ", "_")
                sci_name = date_specie["Sci_Name"].values[0]
                com_name = date_specie["Com_Name"].values[0]
                rating = date_specie["Rating"].values[0]
                recording = review_recordings[j]
                j+=1
                try:
                    current_ID = df2.loc[df2["File_Name"] == recording]["Manual_ID"].values[0]
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
                    st.header("RECORDING NOT AVAILABLE")

                if specie_error!= True:
                    

                    dropdown_index = int(df_names[df_names['Com_Name']==current_ID].index[0])
                    
                    corrected = st.selectbox(
                        "Manual ID?",
                        df_names["Com_Name"],
                        help="If False Positive, select correct specie, non-bird sound or UNKNOWN",
                        index=dropdown_index,
                        key = "select1"+str(i)
                    )

                    corrected_list.append(corrected)
                    
                    if rating == 'NULL':
                        rating_index = "*"
                    else:
                        rating_index= rating
                    rating = st.select_slider(
                        "Rating",
                        options=["*****", "****", "***", "**", "*", "NULL"],
                        value="NULL",
                        help="Select your rating for the sample quality - *=bad; ****=excellent",
                        key = "slider1"+str(i),
                    )
                    rating_list.append(rating)

#                 db_ID = df2.loc[df2["File_Name"] == recording]["Manual_ID"]
                
              
        submitted = st.form_submit_button(
            "Commit Reviewed Samples to DB",
            args = (corrected_list, rating_list),
            help="When the ID and rating above have been entered, click to commit to Database",
        )

        if submitted:
            conn = get_connection(URI_SQLITE_DB)
            with conn:
                cursor = conn.cursor()
                
                for i in range(len(corrected_list)):
                    cursor.execute(
                        f""" UPDATE detections SET Manual_ID = "{corrected_list[i]}" WHERE File_Name = "{review_recordings[i]}" """
                    )
                    cursor.execute(
                        f""" UPDATE detections SET Rating = "{rating_list[i]}" WHERE File_Name = "{review_recordings[i]}" """
                   )
                conn.commit()
            
                df1 = pd.read_sql(f"SELECT * FROM detections WHERE Com_Name = '{specie}'", con=conn)
                df1["DateTime"] = pd.to_datetime(df1["Date"] + " " + df1["Time"])
                df2 = df1.set_index("DateTime")

                #st.experimental_rerun()


    else:
        st.form_submit_button("No Recordings for Selection")
        
 
if len(review_recordings)>0:
    j=0 
    for i in st.columns(len(review_recordings)):

          
        with i:
            date_specie = df2.loc[df2["File_Name"] == review_recordings[j], ["Date", "Com_Name", "Sci_Name", "Rating"]]
            date_dir = date_specie["Date"].values[0]
            specie_dir = date_specie["Com_Name"].values[0].replace(" ", "_")
            sci_name = date_specie["Sci_Name"].values[0]
            com_name = date_specie["Com_Name"].values[0]
            rating = date_specie["Rating"].values[0]
            recording = review_recordings[j]
            j+=1
            try:
                current_ID = df2.loc[df2["File_Name"] == recording]["Manual_ID"].values[0]
                st.write("Current Recording:", recording)
                st.write("Manual ID:", current_ID)
                st.write(
                    "Manual Rating:",
                    df2.loc[df2["File_Name"] == recording]["Rating"].values[0],
                )

            except:
                st.header("RECORDING NOT AVAILABLE")

