import streamlit as st
import pandas as pd
import numpy as np  
import json, sys
from pathlib import Path
from utils import create_AgGrid
from st_aggrid import AgGrid, JsCode, GridUpdateMode, ColumnsAutoSizeMode
from plotly.subplots import make_subplots
import plotly.graph_objects as go

CURRENT_DIR = Path.cwd()
IMAGE_FOLDER = CURRENT_DIR / 'assets' /'images'
CSS_FOLDER = CURRENT_DIR / 'styling'
DATA_SOURCE = CURRENT_DIR / 'assets' / 'data_source'
COUNTRY_LIST = ['CA', 'DE', 'ES', 'FR', 'IT', 'JP', 'UK', 'USA']

st.markdown('<p style="text-align:center;font-size:40px;font-weight: bold">Sales Records </p>', unsafe_allow_html= True)

with open(CSS_FOLDER/'main.css') as css_file:
    st.markdown(f"<style>{css_file.read()}</style>", unsafe_allow_html=True)

@st.experimental_memo
def get_sales_record():
    # country_sales = {each_country: pd.read_excel(DATA_SOURCE / 'sales_records.xlsx', sheet_name=each_country) for each_country in COUNTRY_LIST}
    # return country_sales
    country_sales = pd.read_excel(DATA_SOURCE / 'sales_records.xlsx', sheet_name= None)
    return pd.concat(country_sales.values())

@st.experimental_memo
def display_chart(df: pd.DataFrame, country_list: list[str]):
    if 'All' in country_list:
        country_list = COUNTRY_LIST
    for each_country in country_list:
        sales_report = df[df['country']==each_country]
        if sales_report.shape[0]:
            fig = go.Figure()

            fig.add_trace(go.Scatter(
                # data_frame= sales_report[sales_report['article_no'] == selected_product],
                x= sales_report['sales_date'],
                y= sales_report['quantity_sold'],
                name= 'sales records',
                hovertemplate="%{y}"
            ))
            fig.add_trace(go.Scatter(
                x= sales_report['sales_date'],
                y= sales_report['quantity_return'],
                name= 'return',
                hovertemplate="%{y}"

            ))
            fig.add_trace(go.Bar(
                x= sales_report['sales_date'],
                y= sales_report['quantity_received'],
                name= 'quantity restock',
                hovertemplate="%{y}"

            ))
            fig.add_trace(go.Bar(
                x= sales_report['sales_date'],
                y= sales_report['afq'],
                name= 'inventory quantity',
                hovertemplate="%{y}"
            ))


            fig.update_xaxes(type='category')
            fig.update_layout(
                title= f"sales records for {selected_product} in {each_country}",
                barmode= 'stack',
                # legend= {'font':{'size':14}})
                font=dict(size=18),
                hovermode="x"
            )
            st.plotly_chart(fig, use_container_width=True)

country_sales = get_sales_record()


selected_product = st.text_input('**Enter an article number**',placeholder= "e.g. 11525, 10844, 11167, ...", key='product_input')
try:
    selected_product = int(selected_product)
except:
    st.info("Article number must be a valid number")
    st.stop()

sales_report = country_sales[country_sales['article_no'] == selected_product]
selected_markets = st.sidebar.multiselect(label= "Choose market to view", options= np.append('All',sales_report.country.unique()), default='All')

if st.session_state['product_input']:
    display_chart(df= sales_report, country_list= selected_markets)
