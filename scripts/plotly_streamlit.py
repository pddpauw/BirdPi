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

pio.templates.default = "plotly_white"

userDir = os.path.expanduser('~')
URI_SQLITE_DB = userDir + '/BirdNET-Pi/scripts/birds.db'

st.set_page_config(layout='wide')

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

def get_data2(conn: Connection):
    df1 = pd.read_sql("SELECT * FROM daylight", con=conn)
    return df1

conn = get_connection(URI_SQLITE_DB)
df = get_data(conn)
df2 = df.copy()
df2['DateTime'] = pd.to_datetime(df2['Date'] + " " + df2['Time'])
df2 = df2.set_index('DateTime')

df_daylight = get_data2(conn)
df_daylight['sunr_min']=[(int(m.split(':')[0])*60 + int(m.split(':')[1])) for m in df_daylight['sunrise']]
df_daylight['suns_min']=[(int(m.split(':')[0])*60 + int(m.split(':')[1])) for m in df_daylight['sunset']]
df_daylight['dawn_min']=[(int(m.split(':')[0])*60 + int(m.split(':')[1])) for m in df_daylight['dawn']]
df_daylight['dusk_min']=[(int(m.split(':')[0])*60 + int(m.split(':')[1])) for m in df_daylight['dusk']]
        

def get_db():
   

    conn = get_connection(URI_SQLITE_DB)
    df = get_data(conn)
    df2 = df.copy()
    df2['DateTime'] = pd.to_datetime(df2['Date'] + " " + df2['Time'])
    df2 = df2.set_index('DateTime')
    return df2

df2 = get_db()

daily_view = st.sidebar.checkbox('Single Day View', help= 'Select if you want single day view, unselect for multi-day views')

if daily_view:
# Date as slider
    Start_Date = pd.to_datetime(df2.index.min()).date()
    End_Date = pd.to_datetime(df2.index.max()).date()
#     cols1, cols2 = st.columns((1, 1))
    end_date = st.sidebar.date_input('Date to View',
                            min_value = Start_Date,
                            max_value = End_Date,
                            value=(End_Date),
                            help= 'Select date for single day view'                                     
                            )
    start_date = end_date
else:
    Start_Date = pd.to_datetime(df2.index.min()).date()
    End_Date = pd.to_datetime(df2.index.max()).date()

#    cols1, cols2 = st.columns((1, 1))
    start_date, end_date = st.sidebar.slider('Date Range',
                                    min_value = Start_Date- timedelta(days=1),
                                    max_value = End_Date,
                                    value=(Start_Date, End_Date),
                                    help= 'Select start and end date, if same date get a clockplot for a single day'                                        
                                    )

# start_date, end_date = cols1.date_input(
#     "Date Input for Analysis - select Range for single specie analysis, select single date for daily view",
#     value=(Start_Date, End_Date),
#     min_value=Start_Date,
#     max_value=End_Date)

# start_date = datetime(2022 ,5 ,17).date()
# end_date = datetime(2022 ,5 ,17).date()

@st.cache()
def date_filter(df, start_date, end_date):
    filt = (df2.index >= pd.Timestamp(start_date)) & (df2.index <= pd.Timestamp(end_date + timedelta(days=1)))
    df = df[filt]
    return(df)

df2 = date_filter(df2, start_date, end_date)

st.write('<style>div.row-widget.stRadio > div{flex-direction:row;justify-content: left;} </style>',
         unsafe_allow_html=True)
st.write('<style>div.st-bf{flex-direction:column;} div.st-ag{font-weight:bold;padding-left:2px;}</style>',
         unsafe_allow_html=True)


# Select time period buttons
# Disallow "Daily time period" for "Daily Chart"

report_type = st.sidebar.radio(
    "Report Type Daily/Intra-Day",
    ('Daily', 'Intra-Day'), index=1, help= 'Daily or Intra-Day?')

if report_type == 'Daily':
    resample_sel = st.sidebar.radio(
        "Resample Resolution",
        ('15 minutes', 'Hourly'), index=1, help= 'Select resolution for single day - larger times run faster' )

    resample_times = {'15 minutes': '15min',
                      'Hourly': '1H'
                        }
    resample_time = resample_times[resample_sel]
else:
    resample_sel = st.sidebar.radio(
        "Resample Resolution",
        ('Raw', '15 minutes', 'Hourly'), index=1, help= 'Select resolution for single day - larger times run faster' )


    resample_times = {'Raw': 'Raw',
                        '15 minutes': '15min',
                        'Hourly': '1H'
                        }
    resample_time = resample_times[resample_sel]




@st.cache()
def time_resample(df, resample_time):
    if resample_time == 'Raw':
        df_resample = df['Com_Name']

    else:
        df_resample = df.resample(resample_time)['Com_Name'].aggregate('unique').explode()

    return(df_resample)
top_bird = df2['Com_Name'].mode()[0]
df5 = time_resample(df2, resample_time)

# Create species count for selected date range

def update_db():
    # try: 
    conn = get_connection(URI_SQLITE_DB)
    cursor = conn.cursor()
    cursor.execute(f''' UPDATE detections SET Manual_ID = "{corrected}" WHERE File_Name = "{recording}" ''')
    conn.commit()
    # con.close()

#List of minutes in day for time charts
spacing = 1
lst=[':'.join(str(i*timedelta(minutes=spacing)).split(':')) for i in range(24*60//spacing)]
for i in range(len(lst)):
    if len(lst[i]) == 7:
        lst[i]='0'+ lst[i]

Specie_Count = df5.value_counts()

# Create Hourly Crosstab
hourly = pd.crosstab(df5, df5.index.hour, dropna=True, margins= True)

# Filter on species
species = list(hourly.sort_values("All", ascending= False).index)

#cols1, cols2 = st.columns((1, 1))
top_N = st.sidebar.slider(
    'Select Number of Birds to Show',
    min_value=1,
    max_value=len(Specie_Count),
    value=min(10, len(Specie_Count))
)

top_N_species = (df5.value_counts()[:top_N])

font_size = 15

if daily_view == False:
    
    if report_type != 'Daily':
        specie = st.selectbox(
        'Which bird would you like to explore for the dates ' 
        + str(start_date) + ' to ' + str(end_date) + '?', 
        species,
        index = 0)


        #specie="Cape Robin-Chat"
        if specie == 'All':
            df_counts = int(hourly[hourly.index==specie]['All'])
            fig = make_subplots(
                rows=3, cols=2,
                specs=[[{"type": "xy", "rowspan": 3}, {"type": "polar", "rowspan": 2}], [{"rowspan": 1}, {"rowspan": 1}],
                    [None, {"type": "xy", "rowspan": 1}]],
                subplot_titles=('<b>Top ' + str(top_N) + ' Species in Date Range ' + str(start_date) + ' to ' + str(
                    end_date) + ' for ' + str(resample_sel) + ' sampling interval.' + '</b>',
                                'Total Detect:' + str('{:,}'.format(df_counts)) 
                                # +   '   Confidence Max:' + str(
                                #     '{:.2f}%'.format(max(df2[df2['Com_Name'] == specie]['Confidence']) * 100)) +
                                # '   ' + '   Median:' + str(
                                #     '{:.2f}%'.format(np.median(df2[df2['Com_Name'] == specie]['Confidence']) * 100))
                                )
            )
            fig.layout.annotations[1].update(x=0.7, y=0.25, font_size=15)

            # Plot verification species for selected date range and number of species
            
            fig.add_trace(go.Bar(y=top_N_species.index, x=top_N_species, orientation='h', marker_color='seagreen'), row=1, col=1)
            
            fig.update_layout(
                margin=dict(l=0, r=0, t=50, b=0),
                yaxis={'categoryorder': 'total ascending'})

            # Set 360 degrees, 24 hours for polar plot
            theta = np.linspace(0.0, 360, 24, endpoint=False)

            specie_filt = df5 == specie
            df3 = df5[specie_filt]

            detections2 = pd.crosstab(df3, df3.index.hour)

            d = pd.DataFrame(np.zeros((23, 1))).squeeze()
            detections = hourly.loc[specie]
            detections = (d + detections).fillna(0)
            fig.add_trace(go.Barpolar(r=detections, theta=theta, marker_color='seagreen'), row=1, col=2)
            fig.update_layout(
                autosize=False,
                width=1000,
                height=500,
                showlegend=False,
                polar=dict(
                    radialaxis=dict(
                        tickfont_size=font_size,
                        showticklabels=False,
                        hoverformat="#%{theta}: <br>Popularity: %{percent} </br> %{r}"
                    ),
                    angularaxis=dict(
                        tickfont_size=font_size,
                        rotation=-90,
                        direction='clockwise',
                        tickmode='array',
                        tickvals=[0, 15, 35, 45, 60, 75, 90, 105, 120, 135, 150, 165, 180, 195, 210, 225, 240, 255, 270,
                                285, 300, 315, 330, 345],
                        ticktext=['12am', '1am', '2am', '3am', '4am', '5am', '6am', '7am', '8am', '9am', '10am', '11am',
                                '12pm', '1pm', '2pm', '3pm', '4pm', '5pm', '6pm', '7pm', '8pm', '9pm', '10pm', '11pm'],
                        hoverformat="#%{theta}: <br>Popularity: %{percent} </br> %{r}"
                    ),
                ),
            )

            daily = pd.crosstab(df5, df5.index.date, dropna=True, margins = True)
            fig.add_trace(go.Bar(x=daily.columns[:-1], y=daily.loc[specie][:-1], marker_color='seagreen'), row=3, col=2)
            st.plotly_chart(fig, use_container_width=True)  # , config=config)

        else:
            col1, col2 = st.columns(2)
            with col1:
                fig = make_subplots(
                    rows=3, cols=1,
                    specs=[[{"type": "polar", "rowspan": 2}],[{"rowspan": 1}], [{"type": "xy", "rowspan": 1}]]
                            )
                # Set 360 degrees, 24 hours for polar plot
                theta = np.linspace(0.0, 360, 24, endpoint=False)

                specie_filt = df5 == specie
                df3 = df5[specie_filt]

                detections2 = pd.crosstab(df3, df3.index.hour)

                d = pd.DataFrame(np.zeros((23, 1))).squeeze()
                detections = hourly.loc[specie]
                detections = (d + detections).fillna(0)
                fig.add_trace(go.Barpolar(r=detections, theta=theta, marker_color='seagreen'), row=1, col=1)
                fig.update_layout(
                    autosize=False,
                    width=1000,
                    height=500,
                    showlegend=False,
                    polar=dict(
                        radialaxis=dict(
                            tickfont_size=font_size,
                            showticklabels=False,
                            hoverformat="#%{theta}: <br>Popularity: %{percent} </br> %{r}"
                        ),
                        angularaxis=dict(
                            tickfont_size=font_size,
                            rotation=-90,
                            direction='clockwise',
                            tickmode='array',
                            tickvals=[0, 15, 35, 45, 60, 75, 90, 105, 120, 135, 150, 165, 180, 195, 210, 225, 240, 255, 270,
                                    285, 300, 315, 330, 345],
                            ticktext=['12am', '1am', '2am', '3am', '4am', '5am', '6am', '7am', '8am', '9am', '10am', '11am',
                                    '12pm', '1pm', '2pm', '3pm', '4pm', '5pm', '6pm', '7pm', '8pm', '9pm', '10pm', '11pm'],
                            hoverformat="#%{theta}: <br>Popularity: %{percent} </br> %{r}"
                        ),
                    ),
                )

                daily = pd.crosstab(df5, df5.index.date, dropna=True, margins = True)
                fig.add_trace(go.Bar(x=daily.columns[:-1], y=daily.loc[specie][:-1], marker_color='seagreen'), row=3, col=1)
                st.plotly_chart(fig, use_container_width=True)  # , config=config)
                df_counts = int(hourly[hourly.index==specie]['All'])
                st.subheader('Total Detect:' + str('{:,}'.format(df_counts)) 
                                +   '   Confidence Max:' + str(
                                    '{:.2f}%'.format(max(df2[df2['Com_Name'] == specie]['Confidence']) * 100)) +
                                '   ' + '   Median:' + str(
                                    '{:.2f}%'.format(np.median(df2[df2['Com_Name'] == specie]['Confidence']) * 100)))


            recordings=df2[df2['Com_Name']==specie]['File_Name']
            
        
            with col2:
                try:
                    recording = st.selectbox('Available recordings', recordings.sort_index(ascending=False))#) format_func=lambda x: print("\033[1,32, 40m x \n"))
                    date_specie = df2.loc[df2['File_Name']==recording,['Date','Com_Name']]
                    date_dir = date_specie['Date'].values[0]
                    specie_dir = date_specie['Com_Name'].values[0].replace(" ","_")
                    st.image(userDir + '/BirdSongs/Extracted/By_Date/'+ date_dir + '/'+ specie_dir + '/' + recording + '.png')
                    
                    st.audio(userDir +'/BirdSongs/Extracted/By_Date/'+ date_dir + '/'+ specie_dir + '/' + recording)
                except:
                    st.title('RECORDING NOT AVAILABLE :(')    
            
            cola, colb, colc, cold = st.columns((3,1,1,1))
            with colb:
                manual_id_checked = (df2.loc[df2['File_Name']==recording]['Manual_ID']!='Not_Reviewed')[0]
                verification = st.checkbox('Click to Review', value = manual_id_checked, disabled=manual_id_checked)
            if verification:
                with colc:
                    verified = st.radio("Verification",['True Positive','False Positive'])#, index = int(df2.loc[df2['File_Name']==recording]['ID_Class']))
                    if verified == "False Positive":
                        df_names = pd.read_csv(userDir+'/BirdNET-Pi/model/labels.txt', delimiter= '_', names=['Sci_Name', 'Com_Name']) 
                        df_unknown= pd.DataFrame({"Sci_Name":["UNKNOWN"],"Com_Name":["UNKNOWN"]})
                        df_not_bird= pd.DataFrame({"Sci_Name":["Frog", "Insect", "Machine", "Vehicle", "Ambulance", "Telephone", "Baby"],"Com_Name":["Frog", "Insect", "Machine", "Vehicle", "Ambulance", "Telephone", "Baby"]})
                        df_names = pd.concat([df_unknown, df_not_bird, df_names], ignore_index=True)
                        with cold:
                            corrected = st.selectbox('What specie?', df_names['Com_Name'])#, index= int(df_names[df_names['Com_Name']==df2[df2['File_Name']==recording]['Manual_ID'][0]].index[0]))
                    else:
                        corrected = df2.loc[df2['File_Name']==recording]['Com_Name'][0]
                
                db_ID = df2.loc[df2['File_Name']==recording]['Manual_ID'][0]
                corrected_ID = corrected
                
                if db_ID == corrected_ID:
                    pass            
                else:
                    col1, col2, col3, col4, col5, col6 = st.columns(6)
                    with col1:
                        pass
                    with col2:
                        pass
                    with col3:
                        pass
                    with col4:
                        pass
                    with col5:
                        pass
                    with col6:
                        placeholder = st.empty()
                        isclick = placeholder.button('Commit to DB', on_click= update_db)
                        if isclick:
                            placeholder.empty()
                        df2 = get_db()
             
    else:

        specie = st.selectbox(
        'Which bird would you like to explore for the dates ' 
        + str(start_date) + ' to ' + str(end_date) + '?', 
        species[1:],
        index = 0)

        df_counts = int(hourly[hourly.index==specie]['All'])
        fig = make_subplots(
                            rows=2, cols =1,
                            row_heights=[0.75,0.25],
                            specs=[[{"rowspan": 1}],[{"rowspan": 1}]],
                            shared_xaxes = True,
                            vertical_spacing = 0
                            )
        
        
        df4=df2['Com_Name'][df2['Com_Name']==specie].resample(resample_time).count()
        
        df4.index=[df4.index.date, df4.index.time]
        day_hour_freq=df4.unstack().fillna(0)

        while  day_hour_freq.index.min() != df2.index.date.min():
            new_day = pd.DataFrame(index= [day_hour_freq.index.min()-timedelta(days = 1)], columns= day_hour_freq.columns).fillna(0)
            day_hour_freq = pd.concat([new_day, day_hour_freq])

        while  day_hour_freq.index.max() != df2.index.date.max():
            new_day = pd.DataFrame(index= [day_hour_freq.index.max()+timedelta(days = 1)], columns= day_hour_freq.columns).fillna(0)
            day_hour_freq = pd.concat([day_hour_freq, new_day])


        fig_x = [d.strftime('%d-%m-%Y') for d in day_hour_freq.index.tolist()]
        fig_y = [h.hour*60+h.minute for h in day_hour_freq.columns.tolist()]
        fig_z = day_hour_freq.values.transpose()
       
        
        fig_sunr = df_daylight['sunr_min'][df_daylight['date'].isin(fig_x)]
        fig_suns = df_daylight['suns_min'][df_daylight['date'].isin(fig_x)]
        fig_dawn = df_daylight['dawn_min'][df_daylight['date'].isin(fig_x)]
        fig_dusk = df_daylight['dusk_min'][df_daylight['date'].isin(fig_x)]


        color_pals= px.colors.named_colorscales()
        selected_pal = st.sidebar.selectbox('Select Color Pallet for Daily Detections', color_pals)
        
        fig.add_trace(go.Heatmap(x=fig_x,y=fig_y,z=fig_z, autocolorscale = False, 
                                showlegend = False,
                                colorbar= dict(len = 0.5),
                                colorscale = [
                                [0, "rgb(0, 0, 0)"],
                                [0.25, "rgb(120, 120, 120)"],

                                [0.25, "rgb(120, 120, 120)"],
                                [0.5, "rgb(160, 160, 160)"],

                                [0.5, "rgb(160, 160, 160)"],
                                [0.75, "rgb(210, 210, 210)"],

                                [0.75, "rgb(210, 210, 210)"],
                                [1.0, "rgb(260, 260, 260)"]
                                ]
                                ),
                                row=1, col=1)
                                
        fig.add_trace(go.Scatter(x=fig_x, y= fig_dawn, showlegend = False, fill = 'tozeroy', line_color='black'), row=1, col=1)
        fig.add_trace(go.Scatter(x=fig_x, y= fig_sunr, showlegend = False, fill = 'tonexty', line_color='grey'), row=1, col=1)
        fig.add_trace(go.Scatter(x=fig_x, y= fig_suns, showlegend = False, fill = 'tonexty', line_color='darkgreen'), row=1, col=1)
        fig.add_trace(go.Scatter(x=fig_x, y= fig_dusk, showlegend = False, fill = 'tonexty', line_color='grey'), row=1, col=1)
        
        fig.update_yaxes(row= 1, col =1, tickvals=[i*60 for i in range(24)],
                            ticktext=['12am', '1am', '2am', '3am', '4am', '5am', '6am', '7am', '8am', '9am', '10am', '11am',
                                    '12pm', '1pm', '2pm', '3pm', '4pm', '5pm', '6pm', '7pm', '8pm', '9pm', '10pm', '11pm'],
                                    title_text="Time")
        
        fig.update_yaxes(row= 2, col =1,
                        title_text= f"Detections per {resample_time}")

        fig.update_xaxes(row= 2, col =1,
                        title_text= f"Date",
                        fixedrange= True)
        fig.update_xaxes(row= 1, col =1,
                        fixedrange= True)                          
        
        fig.update_layout(width = 1500, height = 750,
                        title = f" Detections of {specie} on a {resample_time} basis between {start_date:%d-%m-%Y} and {end_date:%d-%m-%Y}")

        daily = pd.crosstab(df5, df5.index.date, dropna=True, margins = True)
           
        fig.add_trace(go.Bar(x=daily.columns[:-1], y=daily.loc[specie][:-1], showlegend = False, marker_color='seagreen'), row=2, col=1)
 
        st.plotly_chart(fig, width= 1500, height= 750, use_container_width=False)  # , config=config)
else:
    fig = make_subplots(
        rows=1, cols=2,
        specs=[[{"type": "xy", "rowspan": 1}, {"type": "xy", "rowspan": 1}]],
        subplot_titles=('<b>Top ' + str(top_N) + ' Species For ' + str(start_date) + '</b>',
                        '<b>Daily ' + str(start_date) + ' Detections on ' + resample_sel + ' interval</b>'),
        shared_yaxes = 'all',
        horizontal_spacing=0
    )

    df6 = df5.to_frame(name='Com_Name')
    readings = top_N

    plt_topN_today = (df6['Com_Name'].value_counts()[:readings])
    freq_order = pd.value_counts(df6['Com_Name']).iloc[:readings].index
    #        confmax = df6.groupby('Com_Name')['Confidence'].max()
    # reorder confmax to detection frequency order
    #        confmax = confmax.reindex(freq_order)
    #         norm = plt.Normalize(confmax.values.min(), confmax.values.max())
    #
    #         colors = plt.cm.Greens(norm(confmax))
    fig.add_trace(go.Bar(y=plt_topN_today.index, x=plt_topN_today, marker_color='seagreen', orientation='h'), row=1,
                  col=1)

    #        plot=sns.countplot(y='Com_Name', data = df_plt_topN_today, palette = colors,  order=freq_order, ax=axs[0])

    df6['Hour of Day'] = [r.hour for r in df6.index.time]
    heat = pd.crosstab(df6['Com_Name'], df6['Hour of Day'])
    # Order heatmap Birds by frequency of occurrance
    heat.index = pd.CategoricalIndex(heat.index, categories=freq_order)
    heat.sort_index(level=0, inplace=True)

    heat_plot_values = ma.log(heat.values).filled(0)

    hours_in_day = pd.Series(data=range(0, 24))
    heat_frame = pd.DataFrame(data=0, index=heat.index, columns=hours_in_day)

    heat = (heat + heat_frame).fillna(0)
    heat_values_normalized = normalize(heat.values, axis=1, norm='l1')

    labels = heat.values.astype(int).astype('str')
    labels[labels == '0'] = ""
    fig.add_trace(go.Heatmap(x=heat.columns, y=heat.index, z=heat_values_normalized,
                             showscale=False,
                             text=labels, texttemplate="%{text}", colorscale='Blugrn'
                             ),row = 1, col =2)
    fig.update_xaxes(row= 1, col =1,
                        title_text= f"Detections on {resample_time} interval",
                        fixedrange= True)
    fig.update_xaxes(row= 1, col =2,
                        title_text= f"Time",
                        fixedrange= True)                          
        
    fig.update_yaxes(visible=True, autorange="reversed", ticks="inside", tickson="boundaries", ticklen=10000,
                     showgrid=True)
    fig.update_layout(xaxis_ticks="inside",
                      margin=dict(l=0, r=0, t=50, b=0))
# container=st.container()
# config={'displayModelBar': False}
    st.plotly_chart(fig, use_container_width=True)  # , config=config)

# cols3,cols4=st.columns((1,1))
# 
# extract_date=Date_Slider
# 
# audio_file = open('/home/*/BirdSongs/Extracted/By_Date/2022-03-22/Yellow-streaked_Greenbul/Yellow-streaked_Greenbul-77-2022-03-22-birdnet-15:04:28.mp3', 'rb')
# audio_bytes = audio_file.read()
# cols4.audio(audio_bytes, format='audio/mp3')
