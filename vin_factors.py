from xml.dom.expatbuilder import theDOMImplementation
from pandas.core.frame import DataFrame
import streamlit as st
import numpy as np
import pandas as pd
import requests
import json


def load_data():
    data = pd.read_parquet('vin_factors.parquet')
    return data
data = load_data()


st.image('loop.png')
st.title('Vin Decoder')
vin = st.text_input('Enter VIN')


if len(vin) == 17:
    url = 'https://vpic.nhtsa.dot.gov/api/vehicles/DecodeVINValuesBatch/'
    post_fields = {'format': 'json', 'data': vin}
    r = requests.post(url, data=post_fields)
    result = json.loads(r.text)

    make = result['Results'][0]['Make']
    year  =  result['Results'][0]['ModelYear']
    body_class = result['Results'][0]['BodyClass']
    model =result['Results'][0]['Model']
    drive_type = result['Results'][0]['DriveType']
    series = result['Results'][0]['Series']
    trim = result['Results'][0]['Trim']
    vehicle_type = result['Results'][0]['VehicleType']


    st.write(f'''#### Vehicle Type: {vehicle_type}''')
    st.write(f'''#### Year: {year}''')
    st.write(f'''#### Make: {make}''')
    st.write(f'''#### Model: {model}''')
    st.write(f'''#### Trim: {trim}''')
    st.write(f'''#### Series: {series}''')
    st.write(f'''#### Body Class: {body_class}''')
    
    print_results = st.empty()

    if st.checkbox('Show more info'):
        more = pd.DataFrame(columns=['Keys','Values'])
        more['Keys'] = list(result['Results'][0].keys())
        more['Values'] = list(result['Results'][0].values())

        st.dataframe(more)
    
    data.ModelYear = pd.to_numeric(data.ModelYear, errors='ignore')

    try:
        data_results = data[(data.VIN.str[:3] == vin[:3]) & (data.Make.str.contains(make)) & (data.ModelYear == int(year))].reset_index(drop=True)
        if len(data_results) == 0:
            data_results = data[(data.Make.str.contains(make)) & (data.ModelYear == int(year))].reset_index(drop=True)  
            if len(data_results) == 0:
                data_results = data[(data.Make.str.contains(make))].reset_index(drop=True)

        for i in data_results.columns:
            data_results[i] = pd.to_numeric(data_results[i], errors='ignore')

        data_results['match_count'] = 0
        data_results['match_on'] = ''
        for i in range(len(data_results)):
            for column in data_results.drop(columns=['VIN','BI','PD','COLL','COMP','MEDPAY','PIP','UMUIM','UMPD','LOAN','LUXURY','match_count','match_on']).columns:
                if column in ['DisplacementCC', 'DisplacementCI','DisplacementL', 'Doors','EngineCycles','EngineCylinders','EngineHP','EngineHP_to', 'EngineKW']:
                    try:
                        convert = float(result['Results'][0][column])
                    except:
                        convert = result['Results'][0][column]
                    if data_results[column][i] == convert:
                        data_results['match_count'][i] = data_results['match_count'][i] + 1
                        data_results['match_on'][i] = data_results['match_on'][i] + ' ' + column
                else:

                    if data_results[column][i] == result['Results'][0][column]:
                        data_results['match_count'][i] = data_results['match_count'][i] + 1
                        data_results['match_on'][i] = data_results['match_on'][i] + ' ' + column    
        data_results.ModelYear = data_results.ModelYear.astype(int)
     
        data_results = data_results.dropna(axis=1, thresh = 1)
        data_results = data_results.sort_values('match_count', ascending=False).reset_index(drop=True)
        
        col = data_results.pop('match_count')
        data_results.insert(loc= 0 , column= 'match_count', value= col)

        st.dataframe(data_results)
    except:
        st.write('''# No Factors on file''')
        







            

    

    




