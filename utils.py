import streamlit as st
from st_aggrid import AgGrid, GridUpdateMode, ColumnsAutoSizeMode
from st_aggrid.grid_options_builder import GridOptionsBuilder

def create_AgGrid(df, button_key= 0):
    gd = GridOptionsBuilder.from_dataframe(df)
    gd.configure_pagination(enabled= True, paginationAutoPageSize= False, paginationPageSize= 20)
    sel_mode = st.radio('Selection Type', options= ['single'], index= 0, key= f"{button_key} + 'sel'")
    gd.configure_selection(selection_mode= sel_mode, use_checkbox= True, pre_selected_rows= [0])

    gridoptions = gd.build()
    grid_table = AgGrid(df, gridOptions= gridoptions,
                        # update_on= ['selectionChanged', 'columnValueChanged'],
                        theme= 'balham',
                        fit_columns_on_grid_load= True,
                        key= button_key,
                        reload_data= True,
                        columns_auto_size_mode= ColumnsAutoSizeMode.FIT_CONTENTS
                        )
    sel_row = grid_table['selected_rows']
    return grid_table, sel_row