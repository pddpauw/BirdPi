import os
import datetime
from datetime import date, timedelta
from astral import LocationInfo
from astral.sun import sun
import sqlite3
from sqlite3 import Connection
import pandas as pd
import os
import tzlocal

# Open most recent Configuration and grab DB_PWD as a python variable
userDir = os.path.expanduser('~')
with open(userDir + '/BirdNET-Pi/scripts/thisrun.txt', 'r') as f:
    this_run = f.readlines()
    lat = str(str(str([i for i in this_run if i.startswith('LAT')]).split('=')[1]).split('\\')[0])
    lon = str(str(str([i for i in this_run if i.startswith('LON')]).split('=')[1]).split('\\')[0])


lat = float(lat)
lon = float(lon)

continent_place = tzlocal.get_localzone_name()

city = LocationInfo(continent_place, continent_place, continent_place,lat,lon)


start_date = datetime.date(2020,1,1)
end_date = datetime.date(2030,1,1)

my_city= city.observer
my_timezone = city.timezone

def daterange(start_date, end_date):
    for n in range(int((end_date - start_date).days)):
        yield start_date + timedelta(n)


def sundatata(city, date, timezone):
    s = sun(city, date, timezone)
    return(s)

current_date = start_date
df=pd.DataFrame(columns = ['date','dawn', 'sunrise', 'noon', 'sunset', 'dusk'])

df_date=[]
df_dawn =[]
df_sunrise=[]
df_noon=[]
df_sunset =[]
df_dusk =[]

for single_date in daterange(start_date, end_date):
       
    s = sun(my_city, single_date, tzinfo= my_timezone)
    df_date.append(single_date.strftime('%d-%m-%Y'))
    df_dawn.append(s['dawn'].time().strftime('%H:%M'))
    df_sunrise.append(s['sunrise'].time().strftime('%H:%M'))
    df_noon.append(s['noon'].time().strftime('%H:%M'))
    df_sunset.append(s['sunset'].time().strftime('%H:%M'))
    df_dusk.append(s['dusk'].time().strftime('%H:%M'))    


df['date']=df_date
df['dawn']=df_dawn
df['sunrise']=df_sunrise
df['noon'] = df_noon
df['sunset']=df_sunset
df['dusk'] = df_dusk

userDir = os.path.expanduser('~')
URI_SQLITE_DB = userDir + '/BirdNET-Pi/scripts/birds.db'
def get_connection(path: str):
    return sqlite3.connect(path, check_same_thread=False)

conn = get_connection(URI_SQLITE_DB)
c = conn.cursor()
c.execute('CREATE TABLE IF NOT EXISTS daylight (date,dawn, sunrise, noon, sunset, dusk)')
conn.commit()

df.to_sql('daylight', conn, if_exists = 'replace', index=False)