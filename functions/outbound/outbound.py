# from functions.outbound.sap import Sap
# from functions.outbound.article import Article
from sap import Sap
from article import Article
import pandas as pd
pd.options.mode.chained_assignment = None
import numpy as np
import sys, os
import pickle
from pathlib import Path

CURRENT_DIR = Path.cwd()
DATA_SOURCE = CURRENT_DIR / 'assets' / "data_source"
# DATA_SOURCE = CURRENT_DIR.parents[1] / 'assets' / "data_source"


WHS = pd.read_csv(DATA_SOURCE / "Warehouse_StorageUnit_DUS.csv")
SAP_total = pd.read_csv(DATA_SOURCE / "Warehouse_outbound_DUS_hist.csv")

def main(doc_nos: list):
    SAP = SAP_total[SAP_total['Document_Number'].isin(doc_nos)]
    SAP = SAP.assign(
        ItemCode = SAP['ItemCode'].astype(int),
        Qty_temp = -SAP['Qty'],
        storage_unit = '',
        WHS_Code = ''
    )
    SAP_inverse = SAP_total[~SAP_total.Document_Number.isin(doc_nos)]
    SAP.sort_values(by=['ItemCode', 'Qty_temp'],ascending= (True,False) ,inplace= True)
    SAP_object = Sap(SAP= SAP)   

    article_list = {}

    for index, row in SAP.iterrows():
        print(row['ItemCode'])
        if row['loading_status'] == 'Pending':
            if str(row['ItemCode']) not in list(article_list.keys()):
                current_article = Article(row['ItemCode'], WHS= WHS)
                current_article.get_sum_quantity_need(SAP_object= SAP_object)
                article_list[str(row['ItemCode'])] = current_article
                        
            SAP_object.check_pure_L0(article= current_article)
            #handel pure L0
            if current_article.pure_L0:
                SAP_object.handle_pure_L0(article= current_article, quantity= SAP.loc[index, 'Qty_temp'], index_SAP= index, SAP= SAP)

            #handel mix 
            else:
                #first take care of the individual pieces
                SAP_object.get_L0_rest(article= current_article, SAP= SAP)
                if current_article.L0_rest > 0 and current_article.check_sufficient_L0(quantity= current_article.L0_rest):
                    SAP_object.handle_pure_L0(article= current_article, quantity= current_article.L0_rest, index_SAP= index, SAP= SAP)
                    current_article.L0_rest = 0
                    current_article.L0_taken = True
                elif current_article.L0_rest > 0 and not current_article.check_sufficient_L0(quantity= current_article.L0_rest):
                    SAP.loc[SAP['ItemCode'] == row['ItemCode'], 'loading_status'] = f'Not enough L0 for {row["ItemCode"]}: {current_article.L0_rest}pcs , please refill first'
                    continue
                    # pass
                # then take the full boxes from L12
                # if current_article.sum_quantity_need < current_article.L0_quantity and int(current_article.sum_quantity_need) % int(current_article.PDB['qnt_box']) == 0:
                #     SAP_object.handle_pure_L0(article= current_article, quantity= SAP.loc[index, 'Qty_temp'], index_SAP= index, SAP= SAP)
                # else:
                SAP_object.handle_mix(article= current_article, quantity= SAP.loc[index, 'Qty_temp'], index_SAP= index, SAP= SAP)
                # if L12 runs out then take rest from L0, the rest of the full boxes should be enough in L0 cause check_0_inv already checked           
                if SAP.loc[index, 'Qty_temp'] > 0:
                    SAP_object.check_pure_L0(article= current_article, WHS= current_article.WHS)
                    #### temporary fix ####
                    if current_article.check_sufficient_L0(quantity= SAP.loc[index, 'Qty_temp']):
                    ## followings are backup##
                    ##if current_article.pure_L0:##
                        SAP_object.handle_pure_L0(article= current_article, quantity= SAP.loc[index, 'Qty_temp'], index_SAP= index, SAP= SAP)
                    else: # if L0 not enough for the rest, requires further inspection
                        SAP.loc[index, 'loading_status'] = 'Not enough INV 101'
        # print(row['id'])

    for key, value in article_list.items():
        assert isinstance(value, Article)
        if 'Not' in SAP.loc[SAP['ItemCode'] == value.article_no, 'loading_status'].unique()[0]:
            continue
        least_moved_quantity, switch_pos = value.get_movement(WHS= WHS)
        if len(switch_pos) > 0:
            value.replace_movement(SAP= SAP, switch_position= switch_pos)
        if len(least_moved_quantity) > 0:
            value.replace_quantity(least_moved_quantity= least_moved_quantity)

    article_object_file = open(CURRENT_DIR / "article_objects.pickle","wb")
    pickle.dump(article_list, article_object_file)
    pickle.dump(SAP_object, article_object_file)
    article_object_file.close()
    SAP = pd.concat([SAP,SAP_inverse])
    SAP = SAP.drop(columns=['Qty_temp'])
    SAP = SAP.reset_index(drop=True)
    SAP.to_csv(DATA_SOURCE /"Warehouse_outbound_DUS_pending.csv", index= False)
    print('finish')

# main([2281858])