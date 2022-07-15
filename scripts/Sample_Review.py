import os
import streamlit as st
import pandas as pd
import numpy as np
from numpy import ma
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import plotly.io as pio
from datetime import timedelta, datetime
from pathlib import Path
import sqlite3
from sqlite3 import Connection
import plotly.express as px
from sklearn.preprocessing import normalize
import time
from st_aggrid import AgGrid, GridOptionsBuilder, GridUpdateMode, DataReturnMode, JsCode


import glob
from pathlib import Path
from scipy.io import wavfile
from scipy import signal
import matplotlib.pyplot as plt
from pydub import AudioSegment

import urllib3
import certifi
from urllib3 import request
import json

st.set_page_config(layout='wide')

http = urllib3.PoolManager(
       cert_reqs='CERT_REQUIRED',
       ca_certs=certifi.where())

userDir = os.path.expanduser('~')
dir_path = userDir + '/BirdSongs/Extracted/By_Date/**/*.mp3'
sound_files = [os.path.basename(x) for x in glob.glob(dir_path, recursive=True)]

pio.templates.default = "plotly_white"

URI_SQLITE_DB = userDir + '/BirdNET-Pi/scripts/birds.db'



# Remove whitespace from the top of the page
st.markdown("""
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
        """, unsafe_allow_html=True)


@st.cache(hash_funcs={Connection: id})
    #@st.cache(allow_output_mutation=True)
def get_connection(path: str):
    return sqlite3.connect(path, check_same_thread=False)

def get_data(conn: Connection):
    df1 = pd.read_sql("SELECT * FROM detections", con=conn)
    return df1

conn = get_connection(URI_SQLITE_DB)
df = get_data(conn)
df2 = df.copy()
df2['DateTime'] = pd.to_datetime(df2['Date'] + " " + df2['Time'])
df2 = df2.set_index('DateTime')

species = df2['Com_Name'].value_counts().index.tolist()

df3 = df2[df2['File_Name'].isin(sound_files)]



specie = st.selectbox(
        'Which bird would you like to review ?', 
        species,
        index = 0)

recordings=df3[df3['Com_Name']==specie]['File_Name']

def update_db():
    # try: 
    conn = get_connection(URI_SQLITE_DB)
    cursor = conn.cursor()
    cursor.execute(f''' UPDATE detections SET Manual_ID = "{corrected}" WHERE File_Name = "{recording}" ''')
    conn.commit()
    # con.close()


recording = st.selectbox('Available recordings', recordings.sort_index(ascending=False),help='These are the recordings available on your Birdie-Pi at the moment for you to review')
date_specie = df2.loc[df2['File_Name']==recording,['Date','Com_Name','Sci_Name']]
date_dir = date_specie['Date'].values[0]
specie_dir = date_specie['Com_Name'].values[0].replace(" ","_")
sci_name = date_specie['Sci_Name'].values[0] #.replace(' ','+')
com_name = date_specie['Com_Name'].values[0]

df_names = pd.read_csv(userDir+'/BirdNET-Pi/model/labels.txt', delimiter= '_', names=['Sci_Name', 'Com_Name']) 
df_unknown= pd.DataFrame({"Sci_Name":["UNKNOWN"],"Com_Name":["UNKNOWN"]})
non_bird = ["Frog", "Insect", "Machine", "Vehicle", "Rainfall", "Ambulance", "Telephone", "Baby"]
non_bird_sci = ["None"] * len(non_bird)
df_not_bird= pd.DataFrame({"Sci_Name":non_bird_sci,"Com_Name":non_bird})
df_names = pd.concat([df_unknown, df_not_bird, df_names], ignore_index=True)


url = 'https://www.xeno-canto.org/api/2/recordings?query='+ sci_name +'+q:A'
r = http.request('GET', url)
data = json.loads(r.data.decode('utf-8'))

if data['numRecordings']=='0':
    url = 'https://www.xeno-canto.org/api/2/recordings?query='+ com_name +'+q:A'
    r = http.request('GET', url)
    data = json.loads(r.data.decode('utf-8'))


df = pd.json_normalize(data,['recordings'])

#try:
st.sidebar.header('Xeno-Canto Samples')
xc_sample = st.sidebar.selectbox('Xeno-Canto sample select',(0,1,2,3,4), help='Select from the top 5 Xeno-Canto samples for the selected species for comparison purposes')

sample = df['file'][xc_sample]
spectro = 'https:'+ df['sono.med'][xc_sample]
xc_id =  df['id'][xc_sample]
xc_en = df['en'][xc_sample]
xc_rec = df['rec'][xc_sample]
xc_cnt = df['cnt'][xc_sample]
xc_lic = df['lic'][xc_sample]
xc_url = df['url'][xc_sample]

st.sidebar.image(spectro)
st.sidebar.audio(sample)
st.sidebar.text(f"XC sample: {xc_id}\nXC name: {xc_en}\nXC Contributor: {xc_rec}\nXC License: Unmodified")
st.sidebar.write(f"http:{xc_url}", unsafe_allow_html=True)
st.sidebar.write(f"http:{xc_lic}", unsafe_allow_html=True)
# except:
#     st.sidebar.header('No Xeno-Canto Samples for this Specie')

col1, col2 = st.columns((1, 2))
with col1:
    try: 
        st.image(userDir + '/BirdSongs/Extracted/By_Date/'+ date_dir + '/'+ specie_dir + '/' + recording + '.png')
        st.audio(userDir +'/BirdSongs/Extracted/By_Date/'+ date_dir + '/'+ specie_dir + '/' + recording)
    except:
        st.title('RECORDING NOT AVAILABLE :(')    


   
    manual_id_checked = (df2.loc[df2['File_Name']==recording]['Manual_ID']!='Not_Reviewed')[0]
    verification = st.checkbox('Click to Review', value = manual_id_checked, disabled=manual_id_checked)
    if verification:
        verified = st.radio("Verification",['True Positive','False Positive'], horizontal = True)
        if verified == "False Positive":
            
            corrected = st.selectbox('What specie?', df_names['Com_Name'])
        else:
            corrected = df2.loc[df2['File_Name']==recording]['Com_Name'][0]
        
        db_ID = df2.loc[df2['File_Name']==recording]['Manual_ID'][0]
        corrected_ID = corrected
        
        if db_ID == corrected_ID:
            pass            
        else:
            placeholder = st.empty()
            isclick = placeholder.button('Commit to DB', on_click= update_db)
            if isclick:
                placeholder.empty()
with col2:

    data = df2[df2['Com_Name']==specie][['File_Name','Manual_ID']].sort_index(ascending=False)
    # st.dataframe(data = df2[df2['Com_Name']==specie][['File_Name','Manual_ID']].sort_index(ascending=False))
    

    gb = GridOptionsBuilder.from_dataframe(data)
    gb.configure_default_column(groupable=True, value=True, enableRowGroup=True)
    
    # gb.configure_column('Manual_ID',
    # cellEditorParams ={'values': df_names['Com_Name']}
    # )
    
    
    style_color = """
    function(params) {
        if (params.value == 'Not_Reviewed') {
            return {
                'color': 'white',
                'backgroundColor': 'gray'
            }
        } else if (params.value != """ +f"{specie}"+""") {
            return {
                'color': 'black',
                'backgroundColor': 'red'
            }
        }
    };
    """


    #configures to use custom styles based on cell's value, injecting JsCode on components front end
    cellsytle_jscode = JsCode("""
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
    """)
    gb.configure_column("File_Name", cellStyle ={'backgroundColor':'grey','color':'white'})
    gb.configure_column("Manual_ID", cellStyle=cellsytle_jscode)
    
    
    gridOptions = gb.build()

    grid_response = AgGrid(
        data,
        gridOptions=gridOptions,
        # data_return_mode=return_mode_value,
        # update_mode=update_mode_value,
        allow_unsafe_jscode=True
    )


#     grid_options = {
#     "columnDefs": [
#         {
#             "headerName": "File_Name",
#             "field": "col1",
#             "editable": False,
#         },
#         {
#             "headerName": "Manual_ID",
#             "field": "col2",
#             "editable": True,
#         },
#     ],
# }
    
    
    
    
    
#     grid_return = AgGrid( df2[df2['Com_Name']==specie][['File_Name','Manual_ID']].sort_index(ascending=False),
#     grid_options)
#     new_df=grid_return["data"]
#     st.write(new_df)
