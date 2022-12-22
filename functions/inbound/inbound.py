from email.policy import default
from multiprocessing.spawn import prepare
import sys
import pandas as pd
import config_py
import mysql.connector
from sqlalchemy import create_engine
from article import Article
from filling import fill_CEZ, fill_L0, fill_L12, prepare_space_default
rm_port = config_py.port
rm_dbname = config_py.dbname
rm_host = config_py.host
rm_user = config_py.user
rm_password = config_py.password
rm_mydb = create_engine('mysql+pymysql://' + rm_user + ':' + rm_password +  '@' + rm_host + ':' + str(rm_port) + '/' + rm_dbname, echo=False) 

mydb = mysql.connector.connect(
    host = rm_host,
    database = rm_dbname,
    user = rm_user,
    password = rm_password,
    port = rm_port
)
mycursor = mydb.cursor()
pd.options.mode.chained_assignment = None

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

select_query = f"""
    select *
    from Warehouse_inbound_DUS_pending where ETA = '2022-12-14' group by article_no
"""
inbound_muster = pd.read_sql_query(select_query, con= rm_mydb)
inbound_muster['article_no'] = inbound_muster['article_no'].astype(int)

select_query = """
    select inbound.article_no, sum(inbound.Qty) as sum_quantity,
    (sum(inbound.Qty) - mod(sum(inbound.Qty),PDB.qnt_box)) as full_quantity, mod(sum(inbound.Qty),PDB.qnt_box) as individual_pieces,
    PDB.qnt_box, PDB.model, PDB.status, PDB.factory, PDSA.Full_qty, PDSA.Half_qty, PDSA.Quarter_qty, WHS.id as default_id
    from po_delivery_static inbound
    left join product_database PDB on PDB.article_no = inbound.article_no
    left join product_database_storage_assign PDSA on PDSA.article_no = inbound.article_no
    left join Warehouse_StorageUnit_DUS WHS on WHS.default_article_no = inbound.article_no
    where inbound.ETA = '2022-12-14' and inbound.destination = 0
    group by inbound.article_no
"""
inbound_pending = pd.read_sql_query(select_query, con= rm_mydb)
inbound_pending = inbound_pending.assign(
    article_no = inbound_pending['article_no'].astype(int)
)
select_query = """
    select * from Warehouse_StorageUnit_DUS 
    where (default_article_no > 0 and default_article_no is not null)
"""
L0_default = pd.read_sql_query(select_query, con= rm_mydb).fillna(0)
L0_default= L0_default.assign(
    article_no = L0_default['article_no'].astype(int)
)

select_query = """
    select *, round(storage_unit_size_h/1.8,2) as height_factor from Warehouse_StorageUnit_DUS 
    where (quantity_single = 0 and level in ('l1','l2') and purpose = 'Normal' and storage_unit_size_h != 0)
"""
empty_L12 = pd.read_sql_query(select_query, con= rm_mydb)
empty_L12['filled'] = False


article_instances = create_article_instance(inbound_rows=inbound_pending)
L0_default = prepare_space_default(article_nos=article_instances, default_rows= L0_default)

for index, inbound_row in inbound_pending.iterrows():
    current_article = article_instances[f"{inbound_row['article_no']}"]
    # current_article.filled_place = {}
    assert isinstance(current_article, Article)
    print(current_article.article_no)
    print(inbound_row)
    if inbound_row['factory'] == 'CEZ':
        fill_CEZ(CEZ= inbound_row, article_instance= current_article)
    else:
        L0_section = fill_L0(article_instance= current_article, default_rows= L0_default)
        L12_places = fill_L12(L12_places= empty_L12,
                            L0_section=L0_section,
                            article_instance= current_article)
    # print(current_article.article_no, current_article.filled_place)

WHS = pd.read_sql("Warehouse_StorageUnit_DUS", con= rm_mydb)
WHS = WHS[['id', 'section', 'number','level', 'side', 'quantity_single', 'default_article_no', 'single_quantity_max']]


df = pd.DataFrame()
for key, value in article_instances.items():
    temp_df = pd.DataFrame.from_dict(value.filled_place)
    temp_df['article_no'] = int(key)
    df = pd.concat([df, temp_df], ignore_index= True)


inbound_assign = pd.merge(left= df, right= inbound_muster, how='left', on= 'article_no')
temp_article_nos = inbound_assign['article_no'].values
inbound_assign = inbound_assign.assign(
    storage_unit = inbound_assign.ids,
    quantity = inbound_assign.qty,
    loading_status = 'Awaiting_Confirmed'
    ).drop(['ids','qty','article_no'], axis= 1)

inbound_assign.insert(2, 'article_no', temp_article_nos)
inbound_assign.to_csv("test_inbound.csv", index= False)
# inbound_assign = pd.merge(left= inbound_assign[['qty','article_no','quantity','storage_unit']], right= WHS, how='left', left_on='storage_unit', right_on='id').sort_values(by='article_no')
# inbound_assign.to_csv('inbound_assign.csv', index= False)


if len(inbound_assign['storage_unit'].unique()) != len(inbound_assign['storage_unit']):
    print("duplicated WHS id")
else:
    print("no duplicate")

if inbound_assign['quantity'].sum() != inbound_pending['sum_quantity'].sum:
    print("quantities don't match")
    for each_article in inbound_assign['article_no'].unique():
        if inbound_assign.loc[inbound_assign['article_no']==each_article,'quantity'].sum() != inbound_pending.loc[inbound_pending['article_no']==each_article,'sum_quantity'].sum():
            print(each_article)