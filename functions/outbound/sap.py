import pandas as pd
import numpy as np
from functions.outbound.article import Article
# from article import Article

class Sap:
    def __init__(self, SAP: pd.DataFrame):
        self.SAP = SAP
        self.SAP_sum = self.get_SAP_sum()


    def get_SAP_sum(self):
        """SAP_sum group all entries according to article_no and sum the quantity"""
        self.SAP['ItemCode'] = self.SAP['ItemCode'].astype(int)
        # get summation of each article going out
        SAP_sum = self.SAP.groupby(['ItemCode'])['Qty'].sum().to_frame()
        SAP_sum.reset_index(inplace=True)
        SAP_sum['loading_status'] = 'Pending'
        return SAP_sum   


    def check_pure_L0(self, article: Article) -> None:
        """Turn pure_L0 artribute of class Article to True if 
        for an article can be taken purely from L0 """
        article.pure_L0 = False
        qnt_sum = self.SAP.loc[self.SAP['ItemCode'] == article.article_no, 'Qty_temp'].sum()
        if qnt_sum <= article.L0_quantity and not article.L0_taken:
            article.pure_L0 = True


    
    def handle_pure_L0(self, article: Article, quantity, index_SAP, SAP: pd.DataFrame) -> None:
        """take care of pure L0 entries"""
        default_level_0 = article.WHS[article.WHS['default_article_no'] == article.article_no]
        if len(default_level_0) > 0:
            l0_id = default_level_0['id'].values[0]
            article.WHS.loc[article.WHS['id'] == l0_id, 'quantity_single'] -= quantity
            article.L0_quantity -= quantity
            article.sum_quantity_need -= quantity
            # article.L0_taken = True
            whs_code = article.get_WHS_code(row= default_level_0)
            SAP.loc[index_SAP,'storage_unit'] += str(l0_id) + ','
            SAP.loc[index_SAP,'WHS_Code'] += whs_code + '->Q[' + str(quantity) + '];'            
            SAP.loc[index_SAP,'Qty_temp'] -= quantity  
            if SAP.loc[index_SAP,'Qty_temp'] == 0:
                SAP.loc[index_SAP,'loading_status'] =  'Awaiting_Confirmed'


    def get_L0_rest(self, article: Article, SAP: pd.DataFrame) -> None:
        """return the quantity of individual piece of an article based on the remaining quantity
        after considering CEZ and pure L0"""
        if article.L0_rest < 0: #default value is -1. This makes sure each article_no will only be checked for L0_rest 1 time
            SAP_qnt = SAP[SAP['ItemCode'] == article.article_no]['Qty_temp'].sum()
            box_qnt = SAP.loc[SAP['ItemCode'] == article.article_no, 'qnt_box'].values[0]
            rest_l0 = 0
            if (int(SAP_qnt) > box_qnt) and (int(SAP_qnt) % int(box_qnt) != 0) or (SAP_qnt < box_qnt):
                rest_l0 = SAP_qnt - np.floor(SAP_qnt/box_qnt)*box_qnt
                article.L0_rest = rest_l0
            else:
                article.L0_rest = 0
        else:
            article.L0_rest = 0


            
                
    def handle_mix(self, article: Article, quantity, index_SAP, SAP: pd.DataFrame) -> None:
        """take care of articles that need both L0 and L12, or CEZ"""
        level_12 = article.WHS[(article.WHS['default_article_no'] != article.article_no) & (article.WHS['quantity_single'] > 0)]
        for index_l12, row_l12 in level_12.iterrows():
            if quantity <= article.WHS.loc[index_l12, 'quantity_single']:
                article.WHS.loc[index_l12, 'quantity_single'] -= quantity
                whs_code = article.get_WHS_code(row= row_l12)
                SAP.loc[index_SAP,'storage_unit'] += str(row_l12['id']) + ','
                SAP.loc[index_SAP,'WHS_Code'] += whs_code + '->Q[' + str(quantity) + '];'            
                SAP.loc[index_SAP,'Qty_temp'] -= quantity 
            else:
                quantity -= row_l12['quantity_single']
                article.WHS.loc[index_l12, 'quantity_single'] = 0
                whs_code = article.get_WHS_code(row= row_l12)
                SAP.loc[index_SAP,'storage_unit'] += str(row_l12['id']) + ','
                SAP.loc[index_SAP,'WHS_Code'] += whs_code + '->Q[' + str(row_l12['quantity_single']) + '];'            
                SAP.loc[index_SAP,'Qty_temp'] -= row_l12['quantity_single']
            article.sum_quantity_need -= quantity
            if SAP.loc[index_SAP,'Qty_temp'] == 0:
                SAP.loc[index_SAP,'loading_status'] =  'Awaiting_Confirmed'
                break    

        
       
        
                    
        
        



        
