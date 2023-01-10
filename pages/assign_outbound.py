import streamlit as st
import pandas as pd
from pathlib import Path
from utils import create_AgGrid
from st_aggrid import AgGrid, GridUpdateMode, ColumnsAutoSizeMode
import time
from functions.outbound.outbound import main as assign_main
from functions.outbound.confirm import main as confirm_main

CURRENT_DIR = Path.cwd()
IMAGE_FOLDER = CURRENT_DIR / 'assets' /'images'
CSS_FOLDER = CURRENT_DIR / 'styling'
DATA_SOURCE = CURRENT_DIR / 'assets' / 'data_source'
COUNTRY_LIST = ['AU', 'CA', 'DE', 'ES', 'FR', 'IT', 'JP', 'UK', 'USA']
VIEW_OPTION =  ["View based on MOI","View based on markets","View based on article_no"]

st.markdown('<p style="text-align:center;font-size:40px;font-weight: bold">Assign Outbound</p>', unsafe_allow_html= True)

with open(CSS_FOLDER/'main.css') as css_file:
    st.markdown(f"<style>{css_file.read()}</style>", unsafe_allow_html=True)

with st.expander("Function description", expanded= False):
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
        The logistic department will receive daily shipments from sales team, which contains only information about the products and their quantities that need to be shipped. For example:<br>
        Shipment 2280197 contains:
        <ul>
            <li>11525: 40 pcs</li>
            <li>10844: 160 pcs</li>
            <li>10789: 30 pcs</li>
        </ul>        
        </p>

        <p>
        Since the shipments don't have any information about the location of each product in the warehouse, this function will help the logistic department to identify the location of products from shipping-ready orders.
        </p>

        <p>
        When identifying the locations of products from a shipment, positions on the ground floors must always have priority to ones from higher levels, as taking products from ground floor requires the least amount
        of labor and time. If the required quantities exceed that of ground floor positions currently hold, higher level locations will be considered.
        </p>
        <p>
        Because of security reasons, all of the data used for this demonstration are randomly self-created and stored in a simple csv file.
        In real case, the data should be gathered from a database using SQL.
        </p>

    """, unsafe_allow_html= True)

st.write("---")

def create_checkbox(labels: list, buttons_on_1_row: int):
    counter = 0
    check_box_archiv = {}
    for each in labels:
        if counter % buttons_on_1_row == 0:
            a = st.columns(buttons_on_1_row)
            counter = 0
        with a[counter]:
            check_box_archiv[f"{each}"] = st.checkbox(f"{each}")
        counter += 1
    return check_box_archiv

def get_selected_button(checkboxes: dict):
    selected_doc_nos = [int(key) for key, value in checkboxes.items() if value == True]
    selected_checkboxes = outbound[outbound['Document_Number'].isin(selected_doc_nos)].index.values
    selected_checkboxes = list(map(int,selected_checkboxes))
    time.sleep(1)
    return selected_checkboxes, selected_doc_nos

def reset_data(df: pd.DataFrame):
    df = df.assign(
        loading_status ='Pending',
        storage_unit ='',
        WHS_Code ='',
    ).drop(['article_no','carton_cbm', 'qnt_box'], axis= 1)
    return df

outbound = pd.read_csv(DATA_SOURCE / "Warehouse_outbound_DUS_hist.csv").sort_values("Document_Number").reset_index(drop= True)
checkboxes = create_checkbox(labels= outbound[outbound['loading_status']=="Pending"].Document_Number.unique(), buttons_on_1_row= 6)
selected_checkboxes, selected_doc_nos = get_selected_button(checkboxes)

if 'selected_checkboxes' not in st.session_state:
    st.session_state['selected_checkboxes'] = selected_checkboxes
st.session_state['selected_checkboxes'] = selected_checkboxes
st.write(st.session_state.selected_checkboxes)

gridOptions = {
        # enable Master / Detail
        "masterDetail": True,
        "rowSelection": "multiple",
        "pagination": False,
        "preSelectedRows": selected_checkboxes,
        # the first Column is configured to use agGroupCellRenderer
        "columnDefs": [
            {
                "field": "Document_Number",
                "checkboxSelection": True,
            },
            {"field": "Posting_Date"},
            {"field": "ItemCode"},
            {"field": "Qty"},
            {"field": "loading_status"},
            {"field": "storage_unit"},
            {"field": "WHS_Code"},
        ],
        "defaultColDef": {
            "filter": True,
            "sortable": True,
        },
        # provide Detail Cell Renderer Params
        
        }

custom_css = {
    ".ag-cell-value":{"font-size":"18px !important"},
    ".ag-header-cell-text":{"color":"red", "font-weight": "bold"},
    ".ag-header-cell":{"background-color":"white"},
}

grid_table = AgGrid(
    outbound,
    gridOptions=gridOptions,
    height=500,
    custom_css= custom_css,
    allow_unsafe_jscode=True,
    reload_data= True,
    update_on=['cellValueChanged'],
    columns_auto_size_mode= ColumnsAutoSizeMode.FIT_ALL_COLUMNS_TO_VIEW,
    key= 'test'
)

sel_row = grid_table['selected_rows']

assign_side, confirm_side, reset_side = st.columns(3)

with assign_side:
    assign_button = st.button("Book selected shipments")
if assign_button:
    assign_main(selected_doc_nos)

with confirm_side:
    confirm_button = st.button("Confirm booked shipments")
if confirm_button:
    confirm_main()

with reset_side:
    reset_button = st.button("Reset data")
if reset_button:
    outbound = reset_data(outbound)
    outbound.to_csv(DATA_SOURCE / 'Warehouse_outbound_DUS_hist.csv', index= False)
    st.experimental_rerun()
