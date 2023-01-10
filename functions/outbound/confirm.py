import sys, datetime, pickle
import pandas as pd
from string import ascii_uppercase
from pathlib import Path
from functions.outbound.sap import Sap
from functions.outbound.article import Article
# from sap import Sap
# from article import Article

CURRENT_DIR = Path.cwd()
DATA_SOURCE = CURRENT_DIR / 'assets' / "data_source"
# DATA_SOURCE = CURRENT_DIR.parents[1] / 'assets' / "data_source"

today = pd.Timestamp.today()

outbound_temp = pd.read_csv(DATA_SOURCE / 'Warehouse_outbound_DUS_pending.csv')
WHS = pd.read_csv(DATA_SOURCE / 'Warehouse_StorageUnit_DUS.csv')
PDB = pd.read_csv(DATA_SOURCE / 'product_database.csv')

def syn_WHS(article: Article, WHS_global: pd.DataFrame):
    for index_WHS, row_WHS in article.WHS.iterrows():
        WHS_id = WHS_global.loc[WHS_global['id'] == row_WHS.id, 'id'].values[0]
        WHS_global.loc[WHS_global['id']== WHS_id, 'quantity_single'] = row_WHS['quantity_single']
        if WHS_global.loc[WHS_global['id']== WHS_id, 'quantity_single'].values[0] == 0:
            WHS_global.loc[WHS_global['id']== WHS_id, 'article_no'] = None
        
def main():
    WHS_old = pd.read_csv(DATA_SOURCE / 'Warehouse_StorageUnit_DUS.csv')
    article_object_file = open("article_objects.pickle","rb")
    article_list = pickle.load(article_object_file)
    article_object_file.close()

    for key, value in article_list.items():
        current_article = value
        assert isinstance(current_article, Article) # pull each article object out from assign
        if type(current_article.WHS) == pd.DataFrame:
            syn_WHS(article= current_article, WHS_global= WHS) # syn WHS from article object with WHS global


    WHS.loc[(WHS['quantity_single'] == 0) & (WHS['default_article_no'].isnull()),'article_no'] = None

    WHS_diff = pd.merge(WHS_old, WHS[['id', 'quantity_single']], how='left', left_on= 'id', right_on= 'id')
    WHS_diff = WHS_diff[WHS_diff['quantity_single_x'] != WHS_diff['quantity_single_y']] # check difference between WHS before and WHS after
    WHS_diff['Qty_diff'] = WHS_diff['quantity_single_x']-WHS_diff['quantity_single_y']
    WHS_diff['WHS_Code'] = WHS_diff['section'].astype(str)  + WHS_diff['number'].astype(str) + '-' + WHS_diff['level'].astype(str).str.replace('l','L')+ '->' + WHS_diff['side'].astype(str).str.replace('None','FULL')

    WHS_diff = pd.merge(WHS_diff,PDB[['article_no','carton_cbm', 'qnt_box']], how='left', left_on= 'article_no', right_on='article_no')
    WHS_diff = WHS_diff[['article_no','Qty_diff','WHS_Code','section','number','level','side','carton_cbm','qnt_box','quantity_single_x','single_quantity_max']]
    WHS_diff = WHS_diff.rename(columns ={'carton_cbm':'CBM', 'quantity_single_x':'quantity_single'})
    WHS_diff = WHS_diff.sort_values(by=['section','level','side'])
    WHS_diff.reset_index(drop= True, inplace= True)
    WHS_diff['Order_Number'], WHS_diff['Palette_Box'], WHS_diff['packing_box'], WHS_diff['cal_packing'] = '', 0, '', 'Pending'
    WHS_diff['date_shipment_in'] = today.date().isoformat()
    WHS_diff.fillna(0, inplace= True)

    def extract(df: pd.DataFrame):
        """return dataframe of L0, L12 and CEZ"""
        L0 = df[df['level'] == 'l0']
        L12 = df[df['level'].isin(['l1', 'l2'])]
        CEZ = df[df['section'] == 'Z']
        return L0, L12, CEZ


    L0, L12, CEZ = extract(df= WHS_diff)


    def arrange(df: pd.DataFrame):
        """arrange by A asscending B descending etc."""
        df['section_temp'] = df['section']
        for each in ascii_uppercase: # putting the shelves in order: A-ascending, B-descending
            if each == 'M':
                break        
            if each == 'A':
                sub_df = df[df['section'] == each]
                sub_df = sub_df.sort_values(by= ['number'])
            else:
                sub_sub_df = df[df['section'] == each]
                if each in ['B','D','F','G','H','J','L']:
                    sub_sub_df = sub_sub_df.sort_values(by= ['number'], ascending= False)
                else: 
                    sub_sub_df = sub_sub_df.sort_values(by= ['number'], ascending= True)
                sub_df = pd.concat([sub_df, sub_sub_df])
        return sub_df

                
    L0 = arrange(df= L0)
    L12 = arrange(df= L12)


    def pallete_arrange_new(df: pd.DataFrame):
        df.reset_index(drop= True, inplace= True)
        df['box_quantity'] = df['Qty_diff']/df['qnt_box']
        box_on_pallet, pallete, pallete_index, index, mix_counter = 0, 0, 1, 0, 0
        while index < len(df):
            while box_on_pallet < 20:
                pallete += 1 # number of entries from WHS_diff
                current_row = df.loc[index]
                if current_row['CBM'] > 0.076:
                    box_on_pallet += current_row['box_quantity']*1.3
                elif current_row['CBM'] < 0.036:
                    box_on_pallet += current_row['box_quantity']*0.75
                else:
                    box_on_pallet += current_row['box_quantity']
                if ((box_on_pallet > 14.0) and (pallete == 1)): # if there are already more than 14 boxes from 1 entry
                    df.loc[index, 'Palette_Box'] = pallete_index
                    pallete = 0
                    index +=1
                    break

                if int(current_row['Qty_diff']) % int(current_row['qnt_box']) != 0:
                    mix_counter += 1
                df.loc[index,'Palette_Box'] = pallete_index
                index += 1

                if box_on_pallet >= 20 or mix_counter > 5:
                    pallete = 0
                    index -= 1
                    break
                
                if index  == len(df): 
                    break
            box_on_pallet = 0
            pallete_index += 1 
            mix_counter = 0       
        return df, pallete_index


    L0, L0_index  = pallete_arrange_new(df= L0)
    CEZ['Palette_Box'] = L0_index
    L12, L12_index = pallete_arrange_new(df= L12)
    L12['Palette_Box'] += L0_index -1
    WHS_diff = pd.concat([L0,CEZ,L12])
    WHS_diff = WHS_diff.reset_index(drop= True)
    WHS_diff['packing_box'] = WHS_diff['qnt_box']
    WHS_diff = WHS_diff.drop(['section_temp'], axis= 1)
    WHS_diff = WHS_diff[['article_no','Qty_diff','WHS_Code','section','number','level','side','date_shipment_in','Order_Number','CBM','Palette_Box','packing_box']]
    now = datetime.datetime.now()
    WHS_diff = WHS_diff[['article_no','Qty_diff','WHS_Code','section','number','level','side','date_shipment_in','Order_Number','CBM','Palette_Box','packing_box']]
    WHS_diff['Document_Number'] = now.strftime("%Y-%m-%d-%H-%M")    


    WHS_diff.to_csv(DATA_SOURCE / 'Warehouse_outbound_DUS_packing.csv')

# main()