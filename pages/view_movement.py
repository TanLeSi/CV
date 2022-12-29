import streamlit as st
import pandas as pd
import base64, json
from pathlib import Path
from utils import create_AgGrid
from functions.inbound import inbound
from functions.inbound.article import Article
from st_aggrid import AgGrid, GridOptionsBuilder, JsCode, GridUpdateMode

CURRENT_DIR = Path.cwd()
IMAGE_FOLDER = CURRENT_DIR / 'assets' /'images'
CSS_FOLDER = CURRENT_DIR / 'styling'
DATA_SOURCE = CURRENT_DIR / 'assets' / 'data_source'
COUNTRY_LIST = ['AU', 'CA', 'DE', 'ES', 'FR', 'IT', 'JP', 'UK', 'USA']
MOI = 10

st.markdown('<p style="text-align:center;font-size:40px;font-weight: bold">View movement </p>', unsafe_allow_html= True)

with open(CSS_FOLDER/'main.css') as css_file:
    st.markdown(f"<style>{css_file.read()}</style>", unsafe_allow_html=True)

with st.expander("Function description", expanded= True):
    st.markdown(f"""
        <p>
        This is a function for an ERP web application for an e-commerce seller. In this particular example, the seller have his products sold via Amazon Marketplace.
        There are several markets across the world, for example: the USA, Japan, Germany, etc. 

        Bacause of the diverse variety of the products, large quantities to be sold and shipped to different countries, there is the need for an easy way to 
        visualize and keep track of the movement of all products in order to later on make a correspond decision on restocking more good selling prodcuts 
        in the warehouse or removing slow-selling products from the warehouse/market. 
        
        Because of security reasons, all of the data used for this demonstration are randomly self-created and stored in a simple csv file.
        In real case, the data should be gathered from a database using SQL.
        </p>

    """, unsafe_allow_html= True)

# def mod_stock(stock_planner: pd.DataFrame):
#     stock_planner['inventory_quantity'] = stock_planner['inventory_quantity'].astype(int)
#     stock_planner['MOI'] = stock_planner['MOI'].astype(float)
#     stock_planner['selling_price'] = stock_planner['selling_price'].round(2)
#     stock_planner['inventory_value'] = stock_planner['inventory_value'].round(2)
#     return stock_planner

# def get_stock_planner(country_code: str):
#     select_query = f"""
#         select stock.sku, stock.article_no, stock.selling_price, stock.inv_amz as inventory_quantity, stock.selling_price*stock.inv_amz as inventory_value, stock.w4 +stock.w3 +stock.w2 +stock.w1 as 4_weeks_sales,
#             PDB.status, PDB.factory,  stock.inv_amz_2w12 as MOI, stock.PO, stock.ETA, '{country_code}' as country
#         from stock_planner_temp_{country_code} stock
#         left join product_database PDB 
#         on PDB.article_no = stock.article_no
#         where 1
#     """
#     stock_planner = pd.read_sql_query(select_query, con= rm_mydb)
#     stock_planner = mod_stock(stock_planner= stock_planner)
#     return stock_planner

# def create_download_button(df: pd.DataFrame, download_header: str, file_name: str, button_key= 0, selection_mode= False):
#     df_return, selected_row_std = create_AgGrid(df, button_key= button_key, selection_mode= selection_mode)
#     st.download_button(
#             label= f'{download_header}',
#             data = pd.DataFrame.from_dict(df_return['data']).to_csv(index= False).encode('utf-8'),
#             file_name= f'{file_name}.csv',
#             mime='csv'
#         )
        
# @st.cache(hash_funcs={sqlalchemy.engine.base.Engine: id})
# def get_info_article(article_no: int):
#     stock_all = pd.DataFrame()
#     for each_country in COUNTRY_LIST:
#         select_query = f"""
#             select stock.sku, stock.article_no, stock.selling_price, stock.inv_amz as inventory_quantity, stock.selling_price*stock.inv_amz as inventory_value, stock.w4 +stock.w3 +stock.w2 +stock.w1 as 4_weeks_sales,
#                 PDB.status, PDB.factory,  stock.inv_amz_2w12 as MOI, stock.PO, stock.ETA, '{each_country}' as country
#             from stock_planner_temp_{each_country} stock
#             left join product_database PDB 
#             on PDB.article_no = stock.article_no
#             where stock.article_no = {article_no}
#         """
#         each_stock = pd.read_sql_query(select_query, con= rm_mydb)
#         stock_all = pd.concat([stock_all,each_stock], ignore_index= True)
#     return mod_stock(stock_all)

def mod_stock(stock_planner: pd.DataFrame):
    stock_planner['inventory_quantity'] = stock_planner['inventory_quantity'].astype(int)
    stock_planner['MOI'] = stock_planner['MOI'].astype(float)
    stock_planner['selling_price'] = stock_planner['selling_price'].round(2)
    stock_planner['inventory_value'] = stock_planner['inventory_value'].round(2)
    return stock_planner

@st.cache
def get_stock_overview():
    result = pd.read_csv(DATA_SOURCE/'AMZ_INV_all_markets.csv')
    return mod_stock(result)

def handle_operator(operator: str, MOI):
    result = {
        "greater than": f" > {MOI}",
        "less than": f" < {MOI}",
    }
    if type(MOI) == list:
        result['between'] = f" >= {MOI[0]} && {MOI[1]} >="
    return result[operator]

def prepare_data(df: pd.DataFrame, df_MOI: pd.DataFrame):
    df_group = df.groupby(by='article_no', as_index= False).agg({
        'country':'count', 
    }).rename(columns={'country': 'available_in'})

    df_MOI = df_MOI.groupby(by='article_no', as_index= False).agg({
        'country':'count'
    }).rename(columns={'country':'count_MOI'})

    df_group = df_group.merge(right= df_MOI, on= 'article_no')

    def get_info(input: pd.Series, ori_df: pd.DataFrame):
        return ori_df[ori_df.article_no == input.article_no].to_json(orient="records")

    df_group['pivot_data'] = df_group.apply(get_info, ori_df = df, axis= 1)
    df_group['pivot_data'] = df_group['pivot_data'].apply(lambda x: pd.json_normalize(json.loads(x)))
    return df_group

def create_stacked_AgGrid(df, operator, MOI_threshold):
    gridOptions = {
        # enable Master / Detail
        "masterDetail": True,
        "rowSelection": "single",
        "pagination": True,
        "paginationPageSize": 20,
        # the first Column is configured to use agGroupCellRenderer
        "columnDefs": [
            {
                "field": "article_no",
                "cellRenderer": "agGroupCellRenderer",
                "checkboxSelection": True,
            },
            {"field": "available_in", "valueFormatter": "x.toLocaleString() + ' countries'"},
            {"field": "count_MOI", "valueFormatter": "x.toLocaleString() + ' countries'"},
        ],
        "defaultColDef": {
            "filter": True,
            "sortable": True,
        },
        # provide Detail Cell Renderer Params
        "detailCellRendererParams": {
            # provide the Grid Options to use on the Detail Grid
            "detailGridOptions": {
                "pagination": False,
                "columnDefs": [
                    {"field": "article_no", "checkboxSelection": True},
                    {"field": "selling_price"},
                    {"field": "inventory_quantity"},
                    {"field": "inventory_value"},
                    {"field": "4_weeks_sales"},
                    {
                        "field": "MOI", 
                        "cellStyle": JsCode("""
                                        function(params) {
                                            console.log(params);
                                            if (params.value""" + handle_operator(operator, MOI_threshold) + """params.value) {
                                                return {
                                                    'color': 'white',
                                                    'backgroundColor': 'red'
                                                }
                                            }
                                        };
                                    """).js_code
                    },
                    {"field": "country"},
                ],
                "defaultColDef": {
                    "sortable": True,
                    "flex": 1,
                },
            },
            # get the rows for each Detail Grid
            "getDetailRowData": JsCode(
                """function (params) {
                    params.successCallback(params.data.pivot_data);
                }"""
            ).js_code,
        },
    }

    custom_css = {
        ".ag-cell-value":{"font-size":"20px !important"}
    }

    grid_table = AgGrid(
        df,
        gridOptions=gridOptions,
        height=500,
        custom_css= custom_css,
        allow_unsafe_jscode=True,
        update_mode=GridUpdateMode.SELECTION_CHANGED
    )
    sel_row = grid_table['selected_rows']
    return grid_table, sel_row
# def test_int_input(input):
#     try:
#         input = int(input)
#     except:
#         st.warning('MOI must be a number')
#         st.stop()

# def get_MOI_article(article_nos: str):
#     try:
#         article_nos_str = article_nos.split(',')
#     except:
#         article_nos_str = int(article_nos)
#     MOI_article_sum = pd.DataFrame()
#     for each_article in article_nos_str:
#         article_stock = get_info_article(int(each_article))
#         MOI_article_sum = pd.concat([MOI_article_sum, article_stock], ignore_index= True)
#     return MOI_article_sum


st.header('Stock overview')
view_MOI = st.sidebar.checkbox(label="View based on MOI", value= True, key= "MOI")
view_markets = st.sidebar.checkbox(label="View based on markets", key= "markets")
if view_MOI:
    with st.expander('Explanation for using comparison'):
        st.write(r"""
            Stock overview shows articles that have MOI greater/less or between given MOI.
        """)
    stock_overview = get_stock_overview()
    overview_operator = st.radio(
        label= 'Choose operator',
        options= ('greater than', 'less than', 'between')
    )
    if overview_operator == 'between':
        MOI_under = st.text_input('Please type in MOI under threshold',value= 1000)
        MOI_upper = st.text_input('Please type in MOI upper threshold', value= 1000)
        MOI_input = [int(MOI_under), int(MOI_upper)]
        stock_overview_MOI = stock_overview[(stock_overview.MOI>=MOI_input[0]) & (stock_overview.MOI<=MOI_input[1]) ]
    else:
        MOI_input = st.text_input('Please type in MOI threshold', value= 1000)
        MOI_input = int(MOI_input)
        if overview_operator == 'greater than':
            stock_overview_MOI = stock_overview[stock_overview.MOI>MOI_input]
        else:
            stock_overview_MOI = stock_overview[stock_overview.MOI<MOI_input]

    st.write("Choose an article to view it across all markets")
    stock_overview_group = prepare_data(df= stock_overview, df_MOI= stock_overview_MOI)
    df_return, selected_row_std = create_stacked_AgGrid(stock_overview_group,operator= overview_operator ,MOI_threshold=MOI_input)
    


#     st.download_button(
#             label= f'Download overview MOI_{MOI_input}',
#             data = pd.DataFrame.from_dict(df_return['data']).to_csv(index= False).encode('utf-8'),
#             file_name= f'overview_MOI_{MOI_input}.csv',
#             mime='csv'
#         )
#     if selected_row_std[0]:
#         selected_article = selected_row_std[0]['article_no']
#         create_download_button(df= get_MOI_article(selected_article),
#                             download_header= f"Download {selected_article} across all markets",
#                             file_name= f"{selected_article} across all markets",
#                             button_key= "MOI_article")
                            
# if view_markets:
#     view_type = st.radio(
#             label= 'Choose view type:',
#             options= ('by market', 'by article_no')
#         )

#     with st.expander('Explanation for each view type'):
#         st.write(r"""
#             This function provides two ways of viewing MOI of different articles. 
#             1. View by market:\
#                 Enter market to view MOI of all articles in that market. The articles are divide into 4 Category: 
#                 * STD, NEW, CEZ and EOL
#             2. View by article_no:\
#                 Enter article_no to view MOI of te given article_no across all markets.
#         """)

#     if view_type == 'by market':
#         st.write(f"available markets: {', '.join(COUNTRY_LIST)} or type ALL to view all markets")
#         country_code = st.text_input("Please type market/partnered warehouse in", 'ES')
#         if country_code.lower() == 'all':
#             stock_planner_all = pd.DataFrame()
#             for each_country in COUNTRY_LIST:
#                 temp = get_stock_planner(country_code= each_country)
#                 stock_planner_all = pd.concat([stock_planner_all, temp], ignore_index= True)
#             create_download_button(df=stock_planner_all,
#                             download_header=f"Download Amazon Inventory for all markets",
#                             file_name=f"AMZ_INV_all_markets",
#                             button_key=f"AMZ_INV_all")
#             st.stop()
#         if country_code not in COUNTRY_LIST:
#             st.warning(f'{country_code} is not acceptable as a market')
#             st.stop()
#         stock_planner = get_stock_planner(country_code= country_code)

#         # for STD products
#         create_download_button(df=stock_planner[(stock_planner['status'] == 'STD') & (~stock_planner['factory'].isin(['CEZ']))].sort_values(by= 'MOI', ascending= False).reset_index(drop= True),
#                                 download_header=f"Download STD {country_code}",
#                                 file_name=f"STD_of_{country_code}",
#                                 button_key=f"std_{country_code}")


#         # for NEW products
#         create_download_button(df=stock_planner[(stock_planner['status'].isin(['NEW', 'READY'])) & (~stock_planner['factory'].isin(['CEZ']))].sort_values(by= 'MOI', ascending= False).reset_index(drop= True),
#                                 download_header=f"Download NEW {country_code}",
#                                 file_name=f"NEW_of_{country_code}",
#                                 button_key=f"new_{country_code}")


#         # for CEZ products
#         create_download_button(df= stock_planner[stock_planner['factory'].isin(['CEZ'])].sort_values(by= 'MOI', ascending= False).reset_index(drop= True),
#                                 download_header=f"Download CEZ {country_code}",
#                                 file_name=f"CEZ_of_{country_code}",
#                                 button_key=f"cez_{country_code}")

#         # for EOL products
#         create_download_button(df= stock_planner[stock_planner['status'] == 'EOL'].sort_values(by= 'MOI', ascending= False).reset_index(drop= True),
#                                 download_header=f"Download EOL {country_code}",
#                                 file_name=f"EOL_of_{country_code}",
#                                 button_key=f"eol_{country_code}")

#     elif view_type == 'by article_no':
#         article_no_input = st.text_input("Please type article_no in", '11525')
#         # try:
#         #     article_no_input = int(article_no_input)
#         # except:
#         #     st.write("Article_no must be a number!")
#         #     st.stop()
#         create_download_button(df= get_MOI_article(article_nos=article_no_input),
#                             download_header= f"Download {article_no_input} across all markets",
#                             file_name= f"{article_no_input} across all markets",
#                             button_key= "individual_articles")
