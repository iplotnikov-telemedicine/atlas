from geopy.exc import GeocoderTimedOut
from geopy.geocoders import Nominatim
import os
import pandas as pd
import streamlit as st
os.environ['http_proxy'] = "http://10.2.176.162:8080" 
os.environ['https_proxy'] = "http://10.2.176.162:8080" 


def findGeocode(area):
    try:
        geolocator = Nominatim(user_agent="streamlit")
        return geolocator.geocode(area)
    except GeocoderTimedOut:
        return findGeocode(area) 


def get_lat_and_long(area):
    loc = findGeocode(area)
    return loc.latitude, loc.longitude

@st.experimental_memo
def get_lat_long_df(branch_name):
    geo_area = branch_name.replace(' NEW','')
    lat, lon = get_lat_and_long(geo_area)
    return pd.DataFrame({'city':[geo_area], 'lat':lat, 'lon':lon})