import sys
import pandas as pd
from functions.inbound.article import Article
from functions.inbound.filling import fill_CEZ, fill_L0, fill_L12, prepare_space_default
import streamlit as st
pd.options.mode.chained_assignment = None

# @st.cache(allow_output_mutation= True)
def create_article_instance(inbound_rows: pd.DataFrame):
    result = {}
    for index, inbound_row in inbound_rows.iterrows():
        result[f"{inbound_row['article_no']}"] = Article(
            article_no= inbound_row['article_no'],
            sum_quantity= inbound_row['sum_quantity'],
            qnt_box= inbound_row['qnt_box'],
            full_qty= inbound_row['full_quantity'],
            individual_pieces= inbound_row['individual_pieces'],
            Full_pal_qty= inbound_row['Full_qty'],
            Half_pal_qty= inbound_row['Half_qty'],
            Quarter_pal_qty= inbound_row['Quarter_qty'],
            default_id = inbound_row['default_id']
        )
    return result

def calculate_inbound(inbound_pending: pd.DataFrame, WHS: pd.DataFrame, article_instances: dict):
    L0_default = WHS[(WHS['default_article_no']>0) & (~WHS['default_article_no'].isna())]
    L0_default = prepare_space_default(article_nos=article_instances, default_rows= L0_default)
    empty_L12 = WHS[(WHS['quantity_single']==0) & (WHS['level'].isin(('l1','l2'))) & (WHS['purpose']=='Normal')  & (WHS['storage_unit_size_h']!=0)]
    empty_L12 = empty_L12.assign(
        height_factor = round(empty_L12['storage_unit_size_h']/1.8,2),
        filled = False
    )
    article_instances = create_article_instance(inbound_rows=inbound_pending)

    for index, inbound_row in inbound_pending.iterrows():
        current_article = article_instances[f"{inbound_row['article_no']}"]
        assert isinstance(current_article, Article)
        L0_section = fill_L0(article_instance= current_article, default_rows= L0_default)
        L12_places = fill_L12(L12_places= empty_L12,
                            L0_section=L0_section,
                            article_instance= current_article)
        # print(current_article.article_no, current_article.filled_place)

    df = pd.DataFrame()
    for key, value in article_instances.items():
        temp_df = pd.DataFrame.from_dict(value.filled_place)
        temp_df['article_no'] = key
        df = pd.concat([df, temp_df], ignore_index= True)
    return df




# if len(inbound_assign['storage_unit'].unique()) != len(inbound_assign['storage_unit']):
#     print("duplicated WHS id")
# else:
#     print("no duplicate")

# if inbound_assign['quantity'].sum() != inbound_pending['sum_quantity'].sum:
#     print("quantities don't match")
#     for each_article in inbound_assign['article_no'].unique():
#         if inbound_assign.loc[inbound_assign['article_no']==each_article,'quantity'].sum() != inbound_pending.loc[inbound_pending['article_no']==each_article,'sum_quantity'].sum():
#             print(each_article)