import streamlit as st
import pandas as pd
import base64
from pathlib import Path
from utils import create_AgGrid
from functions.inbound import inbound
from functions.inbound.article import Article

CURRENT_DIR = Path.cwd()
IMAGE_FOLDER = CURRENT_DIR / 'assets' /'images'
CSS_FOLDER = CURRENT_DIR / 'styling'
DATA_SOURCE = CURRENT_DIR / 'assets' / 'data_source'

@st.cache
def get_WHS():
    WHS = pd.read_csv(DATA_SOURCE/'Warehouse_StorageUnit_DUS.csv')
    return WHS



st.markdown('<p style="text-align:center;font-size:40px;font-weight: bold">Assign Inbound</p>', unsafe_allow_html= True)

with open(CSS_FOLDER/'main.css') as css_file:
    st.markdown(f"<style>{css_file.read()}</style>", unsafe_allow_html=True)

with st.expander("Function description", expanded= True):
    st.markdown(f"""
        <p>
        This is a function for an ERP web application for a warehouse with high rack storage system. In this particular example, the warehouse has over 
        1000 storage places with different dimensions and at different levels, with "level" referencing to the storey height of a rack, compared to the ground floor
        <ul>
            <li>Ground floor</li>
            <li>Level 1</li>
            <li>Level 2</li>
        </ul>
        </p>

        <p>
        Receiving products from the manufacture is one of the main tasks in a warehouse. Because of the large quantities of the newly arriving products, 
        the process of assigning them to the correct positions in the warehouse, should hence be automated. There are of course a few ground rules thereby to obey:
        <ul>
            <li>Products must always be stored seperately, which means different products are assigned to different locations seperately. There can never be more than 1 type of product
             at the same location in the warehouse</li>
            <li>Each product has it's own unique position on the ground floor. That means, no other product could be stored in that position, even if that postition is currently empty</li>
            <li>Ground floor positions can store individuall pieces (quantities that cannot make up a full box)</li>
            <li>Unlike the ground floor, positions of level 1 and 2 aren't bounded to any product, which means they can store any product seperately, as long as they are empty</li>
            <li>Only full boxes are allowed to be stored on level 1 and 2</li>
        </ul>
        </p>
        <p>
        Because of security reasons, all of the data used for this demonstration are randomly self-created and stored in a simple csv file.
        In real case, the data should be gathered from a database using SQL.
        </p>

    """, unsafe_allow_html= True)

inbound_pending = pd.read_csv(DATA_SOURCE/'po_delivery_static.csv')
WHS = get_WHS()


with st.expander("Raw data"):
    st.markdown("### Inbound products", unsafe_allow_html= True)
    st.table(inbound_pending)
    st.markdown("### Warehouse positions", unsafe_allow_html= True)
    df_return, selected_row = create_AgGrid(df=WHS, selection_mode= False)

calculate_button = st.button("Calculate inbound")
if "calculate" not in st.session_state:
    st.session_state.calculate = False
if calculate_button or st.session_state.calculate:
    st.session_state.calculate = True
    st.session_state.calculate = True
    article_instances = inbound.create_article_instance(inbound_rows=inbound_pending)
    inbound_result = inbound.calculate_inbound(inbound_pending, WHS, article_instances)
    inbound_result = pd.merge(left=inbound_result, right= WHS[['id','section', 'number', 'level', 'side','default_article_no', 'single_quantity_max']], how='left', left_on='ids', right_on='id')
    inbound_result = inbound_result.assign(
        WHS_Code = inbound_result['section'] + inbound_result['number'].astype(str) + '-' + inbound_result['level'].str.capitalize() + '-' + inbound_result['side']
    )
    inbound_result.drop(['ids', 'section', 'number', 'level', 'side'], axis=1, inplace= True)
    inbound_result = inbound_result[['article_no', 'qty', 'id', 'WHS_Code', 'default_article_no', 'single_quantity_max']]
    left_col, right_col = st.columns([3,2])
    with left_col:
        st.write("##### Inbound quantities assigned to correspond positions")
        df_return, selected_row = create_AgGrid(df=inbound_result, button_key= 'inbound_result' ,selection_mode= False)
    with right_col:
        st.write('##### Inbound quantities')
        st.table(inbound_pending[['article_no','sum_quantity','full_quantity','individual_pieces']])