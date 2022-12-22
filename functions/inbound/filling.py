from textwrap import fill
import pandas as pd
from article import Article
from string import ascii_uppercase
import config_py
import mysql.connector
from sqlalchemy import create_engine
import math
rm_port = config_py.port
rm_dbname = config_py.dbname
rm_host = config_py.host
rm_user = config_py.user
rm_password = config_py.password
rm_mydb = create_engine('mysql+pymysql://' + rm_user + ':' + rm_password +  '@' + rm_host + ':' + str(rm_port) + '/' + rm_dbname, echo=False) 

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
    pass
    