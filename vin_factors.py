from xml.dom.expatbuilder import theDOMImplementation
from pandas.core.frame import DataFrame
import streamlit as st
import numpy as np
import pandas as pd
import requests
import json


def load_data():
    data = pd.read_parquet('vin_factors.parquet')

    col = data.pop('VIN')
    data.insert(loc= 0 , column= 'VIN', value= col)
        
        
    col = data.pop('ModelYear')
    data.insert(loc= 1 , column= 'ModelYear', value= col)

    col = data.pop('Make')
    data.insert(loc= 2 , column= 'Make', value= col)

    col = data.pop('Model')
    data.insert(loc= 3 , column= 'Model', value= col)

    col = data.pop('Trim')
    data.insert(loc= 4 , column= 'Trim', value= col)

    col = data.pop('Series')
    data.insert(loc= 5 , column= 'Series', value= col)

    col = data.pop('BodyClass')
    data.insert(loc= 6 , column= 'BodyClass', value= col)


    data.ModelYear = pd.to_numeric(data.ModelYear, downcast='integer', errors='ignore')

    return data
data = load_data()


st.image('loop.png')
st.title('Vin Decoder')

option = st.radio(label='Select your desired function?', options=('Decode', 'Lookup'))

if option == 'Decode':
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
            more = pd.DataFrame()
            more['Keys'] = list(result['Results'][0].keys())
            more['Values'] = list(result['Results'][0].values())

            st.dataframe(more)
        

        try:
            data_results = data[(data.VIN.str[:3] == vin[:3]) & (data.Make == make) & (data.ModelYear == int(year))].reset_index(drop=True)
            if len(data_results) == 0:
                data_results = data[(data.VIN.str[:3] == vin[:3]) & (data.Make == make)].reset_index(drop=True)
                if len(data_results) == 0:
                    data_results = data[(data.VIN.str[:3] == vin[:3])].reset_index(drop=True)
                    if len(data_results) == 0:
                        data_results = data[(data.Make == make) & (data.ModelYear == int(year))].reset_index(drop=True)
                        if len(data_results) == 0:
                            data_results = data[(data.Make == make)]
                            if len(data_results) == 0:
                                data_results = data[(data.ModelYear == int(year)) & (data.BodyClass == body_class)].reset_index(drop=True)
                                st.write('Very Weak Match')
                            else:
                                st.write('Weak Match')
                        else:
                            st.write('Match')
                    else:
                        st.write('Ok Match')
                else:
                    st.write('Strong Match')
            else:
                st.write('Very Strong Match')
           
        


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


elif option == 'Lookup':
    Key = []
    Key_selected = []

    select_years = (sorted(data[~data.ModelYear.isna()].ModelYear.unique()))
    select_years.append('Any')

    year_selected = st.selectbox('Year', select_years, index= len(select_years) -1)

    if year_selected != 'Any':
        select_make = (sorted(data[(~data.Make.isna()) & (data.ModelYear == year_selected)].Make.unique()))
        select_make.append('Any')
    else:
        select_make = (sorted(data[(~data.Make.isna())].Make.unique()))
        select_make.append('Any')


    make_selected = st.selectbox('Make', select_make, index= len(select_make) -1)

   
    
    if  make_selected != 'Any' and year_selected != 'Any':
        select_model = (sorted(data[(data.Make.str.contains(make_selected)) & (~data.Model.isna()) & (data.ModelYear == year_selected)].Model.unique()))
        select_model.append('Any')

    elif make_selected != 'Any':
        select_model = (sorted(data[(data.Make.str.contains(make_selected)) & (~data.Model.isna())].Model.unique()))
        select_model.append('Any')
    
    else:
        select_model = (sorted(data[(~data.Model.isna())].Model.unique()))
        select_model.append('Any')

    model_selected = st.selectbox('Model', select_model, index= len(select_model) -1)


    if year_selected != 'Any':
        Key.append('ModelYear')
        Key_selected.append(year_selected)


    if make_selected != "Any":
        Key.append('Make')
        Key_selected.append(make_selected)

    if model_selected != 'Any':
        Key.append('Model')
        Key_selected.append(model_selected)

    data.ModelYear = pd.to_numeric(data.ModelYear, errors='ignore')
    
    if len(Key) == 1:
        st.dataframe(data[(data[Key[0]] == Key_selected[0])])
    elif len(Key) == 2:
        st.dataframe(data[(data[Key[0]] == Key_selected[0]) & (data[Key[1]] == Key_selected[1])])
    elif len(Key) == 3:
        st.dataframe(data[(data[Key[0]] == Key_selected[0]) & (data[Key[1]] == Key_selected[1]) & (data[Key[2]] == Key_selected[2])]) 
    else:
        st.dataframe(data[:10000])


    







        

    

    




