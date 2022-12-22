import pandas as pd
from functions.inbound.article import Article
from string import ascii_uppercase
import math
import streamlit as st

def prepare_space_default(article_nos: dict, default_rows: pd.DataFrame):
    default_rows['empty_space'] = default_rows['single_quantity_max'] - default_rows['quantity_single']
    for key, each_article in article_nos.items():
        assert isinstance(each_article, Article)
        default_row = default_rows[default_rows['default_article_no'] == each_article.article_no ]
        if default_row.shape[0] != 1:
            print(f"{each_article.article_no} has {default_row.shape[0]} default place(s)")
        if default_row['empty_space'].values < each_article.individual_pieces + each_article.qnt_box:
            default_rows.loc[default_rows['default_article_no']==each_article.article_no,'single_quantity_max'] = default_row['quantity_single'] + 2*each_article.qnt_box
    return default_rows

def fill_L0(article_instance: Article, default_rows: pd.DataFrame):
    rel_default_row = default_rows[default_rows['default_article_no']==article_instance.article_no]
    if rel_default_row.shape[0]:
        if rel_default_row['empty_space'].values[0] > article_instance.sum_quantity:
            fillable_qty = article_instance.sum_quantity
        else:
            fillable_qty = (rel_default_row['single_quantity_max']-rel_default_row['quantity_single']).values[0] 
            fillable_qty = int(fillable_qty) // article_instance.qnt_box * article_instance.qnt_box + article_instance.individual_pieces
        article_instance.sum_quantity -= fillable_qty  
        article_instance.filled_place['ids'].append(rel_default_row["id"].values[0])   
        article_instance.filled_place['qty'].append(fillable_qty)
        return rel_default_row['section'].values[0]
    else:
        return 'E'

def sort_section(section: str):
    index = ascii_uppercase.index(section)
    result = {}
    distance = 1
    for i in range(1, 26):
        try:
            if not result.get(ascii_uppercase[index + i]):
                result[ascii_uppercase[index + i]] = distance
        except:
            pass
        try:
            if not result.get(ascii_uppercase[index - i]):
                result[ascii_uppercase[index - i]] = distance
        except:
            pass
        distance += 1
    result[section] = 0
    return result

def fill_L12(L12_places: pd.DataFrame, L0_section: str, article_instance: Article):
    section_sorted = sort_section(L0_section)
    L12_places['sort_section'] = L12_places['section'].apply(lambda x: section_sorted[x])    
    L12_places.reset_index(drop= True, inplace= True)
    pallet_needed = math.ceil(article_instance.sum_quantity / article_instance.Full_pal_qty)
    empty_ids = L12_places[L12_places['filled']==False].sort_values(by=['sort_section','section'])['id'].values
    counter = 0
    while article_instance.sum_quantity > 0:
        whs_id = empty_ids[counter]
        height_factor = L12_places.loc[L12_places['id'] == whs_id, 'height_factor'].values[0]
        fillable_qty = math.floor((article_instance.Full_pal_qty/article_instance.qnt_box)*height_factor)*article_instance.qnt_box
        if article_instance.sum_quantity > fillable_qty:
            article_instance.filled_place['qty'].append(fillable_qty)
            article_instance.sum_quantity -= fillable_qty
        else:
            article_instance.filled_place['qty'].append(article_instance.sum_quantity)
            article_instance.sum_quantity = 0
        article_instance.filled_place['ids'].append(whs_id)   
        L12_places.loc[L12_places['id'] == whs_id, 'filled'] = True
        counter += 1
    return L12_places

def fill_CEZ(CEZ: pd.DataFrame, article_instance: Article):
    article_instance.filled_place['ids'].append(1048576)
    article_instance.filled_place['qty'].append(article_instance.full_qty)


if __name__ == "__main__":
    def create_article_instance(inbound_rows: pd.DataFrame):
        result = {}
        for index, inbound_row in inbound_rows.iterrows():
            result[f"{inbound_row['article_no']}"] = Article(
                article_no= inbound_row['article_no'],
                status= inbound_row['status'],
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

    from pathlib import Path
    CURRENT_DIR = Path.cwd()
    DATA_SOURCE = CURRENT_DIR / 'assets' / 'data_source'
    WHS = pd.read_csv(DATA_SOURCE/'Warehouse_StorageUnit_DUS.csv')
    L0_default = WHS[(WHS['default_article_no']>0) & (~WHS['default_article_no'].isna())]
    inbound_pending = pd.read_csv(DATA_SOURCE/'po_delivery_static.csv')
    article_instances = create_article_instance(inbound_rows= inbound_pending)
    L0_default = prepare_space_default(article_nos= article_instances, default_rows= L0_default)