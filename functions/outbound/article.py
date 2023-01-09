import pandas as pd
import numpy as np


class Article:
    def __init__(self, article_no, WHS: pd.DataFrame) -> None:
        self.article_no = article_no
        self.WHS = WHS
        self.WHS = self.get_rel_WHS()
        self.get_L0_quantity()
        self.pure_L0 = False
        self.L0_rest = -1
        self.default_L0 = self.get_default_L0()
        self.L0_taken = False
       

    def get_rel_WHS(self):
        rel_WHS = self.WHS[self.WHS['article_no'] == self.article_no]
        return rel_WHS


    def check_CEZ(self):
        factory = self.PDB['factory'].values[0]
        status = self.PDB['status'].values[0]
        CEZ_exception = [11017]
        if (factory in ['CEZ', 'CEZ_BLNK', 'Perixx SZ', 'Perixx DE', 'Saluc']
             or status == 'CONS'
             or self.article_no in CEZ_exception
             or 1048576 in self.INV['storage_unit'].unique()):
            return True
        else: 
            return False


    def get_L0_quantity(self):
        self.L0_quantity = -9999
        if self.WHS is not None:
            check_L0 =  self.WHS.loc[(self.WHS['default_article_no'] == self.article_no) & (self.WHS['quantity_single'] >= 0)] # check if there is a default place for this article
            if len(check_L0)>0:
                self.L0_quantity = check_L0.quantity_single.values[0]
            

    def get_WHS_code(self, row: pd.DataFrame):
        result = row['section'] + '-'+ str(int(row['number'])) + '-' + row['level'] + '-' + row['side']
        if type(result) == str:
            return result
        else:    
            return result.values[0]


    def check_sufficient_L0(self, quantity: int):
        if self.L0_quantity >= quantity:
            return True
        else:
            return False

    def get_sum_quantity_need(self, SAP_object):
        self.sum_quantity_need = SAP_object.SAP_sum.loc[SAP_object.SAP_sum['ItemCode'] == self.article_no, 'Qty'].values[0]*-1

    
    def get_movement(self, WHS: pd.DataFrame):
        movement = pd.merge(self.WHS, WHS[['id','quantity_single']], how= 'left', left_on= 'id', right_on= 'id')
        assert isinstance(movement, pd.DataFrame)
        movement = movement[movement['quantity_single_x'] != movement['quantity_single_y']]
        movement['diff'] = movement['quantity_single_y']-movement['quantity_single_x']
        movement = movement[movement['default_article_no'] != self.article_no]
        movement.sort_values(by= 'diff', inplace= True)
        movement.reset_index(drop= True, inplace= True)
        least_moved_quantity, switch_pos= pd.DataFrame(columns= movement.columns), []
        cumulative_diff = 0
        for index, row in movement.iterrows():
            cumulative_diff += row['diff']
            if cumulative_diff >= self.L0_quantity:
                break
            least_moved_quantity.loc[index] = row
            switch_pos.append(self.get_WHS_code(row= row))
            self.L0_quantity -= row['diff']
        least_moved_quantity.reset_index(drop= True, inplace= True)
        return least_moved_quantity, switch_pos
    

    def get_default_L0(self):
        if type(self.WHS) == pd.DataFrame:
            default_L0 = self.WHS[self.WHS['default_article_no']==self.article_no]
            if len(default_L0) == 0:
                return pd.DataFrame()
            else:
                return default_L0

    def replace_movement(self, SAP:pd.DataFrame, switch_position: list):
        rel_SAP = SAP[SAP['ItemCode']==self.article_no]
        if len(self.default_L0) != 0:
            default_L0 = self.get_WHS_code(row= self.default_L0)
            for index, row in rel_SAP.iterrows():
                if row['ItemCode'] != self.article_no:
                    continue
                original_movement = row['Outbound_status']
                for each in switch_position:
                    if each in original_movement:
                        original_movement = original_movement.replace(f'{each}', f'{default_L0}')
                    SAP.loc[index, 'Outbound_status'] = original_movement


    def replace_quantity(self, least_moved_quantity: pd.DataFrame):
        if len(least_moved_quantity) > 0:
            for index, row in least_moved_quantity.iterrows():
                self.WHS.loc[self.WHS['id'] == row['id'], 'quantity_single'] += row['diff']
                self.WHS.loc[self.WHS['default_article_no']==self.article_no, 'quantity_single'] -= row['diff']

    

