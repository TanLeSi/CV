import streamlit as st
import pandas as pd
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

# sales_record = pd.read_excel(DATA_SOURCE / 'sales_records.xlsx')
@st.experimental_memo
def get_sales_record():
    country_sales = {each_country: pd.read_excel(DATA_SOURCE / 'sales_records.xlsx', sheet_name=each_country) for each_country in COUNTRY_LIST}
    return country_sales

country_sales = get_sales_record()



selected_product = st.text_input('**Enter an article number**',placeholder= "e.g. 11525, 10844, 11167, ...", key='product_input')
@st.experimental_memo
def display_chart(article_no: int):
    for each_country in COUNTRY_LIST:
        sales_report = country_sales[each_country]
        sales_report = sales_report[sales_report['article_no']==article_no]
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

if st.session_state['product_input']:
    display_chart(article_no= int(selected_product))
else:
    st.stop()