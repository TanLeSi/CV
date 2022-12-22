import streamlit as st
import pandas as pd
import base64
from pathlib import Path
from utils import create_AgGrid
from functions import inbound

CURRENT_DIR = Path.cwd()
IMAGE_FOLDER = CURRENT_DIR / 'assets' /'images'
CSS_FOLDER = CURRENT_DIR / 'styling'
DATA_SOURCE = CURRENT_DIR / 'assets' / 'data_source'

@st.cache
def get_WHS():
    WHS = pd.read_csv(DATA_SOURCE/'Warehouse_StorageUnit_DUS.csv')
    return WHS



st.markdown('<h1 style="text-align:center">Assign Inbound</h1>', unsafe_allow_html= True)

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
    """, unsafe_allow_html= True)

WHS = get_WHS()

with st.expander("Raw data"):
    st.header("Inbound products")
    st.table(pd.read_csv(DATA_SOURCE/'po_delivery_static.csv'))
    df_return, selected_row = create_AgGrid(df=get_WHS())


