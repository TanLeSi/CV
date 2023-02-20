import streamlit as st
from pathlib import Path
import sys
import numpy as np
import pandas as pd
from datetime import datetime
import plotly.graph_objects as go
from utils import create_AgGrid

CURRENT_DIR = Path.cwd()
IMAGE_FOLDER = CURRENT_DIR / 'assets' /'images'
CSS_FOLDER = CURRENT_DIR / 'styling'
DATA_SOURCE = CURRENT_DIR / 'assets' / 'data_source'
BOX_VERTICES_INDEX = np.array([
    [7, 0, 0, 0, 4, 4, 6, 6, 4, 0, 3, 2],
    [3, 4, 1, 2, 5, 6, 5, 2, 0, 1, 6, 3],
    [0, 7, 2, 3, 6, 7, 1, 1, 5, 5, 7, 6]])

from pathlib import Path
import numpy as np
import pandas as pd
import sys
import numpy as np
import plotly.graph_objects as go
import streamlit as st

class Box:
    def __init__(self,length, width, height):
        self.length = length #+ PUFFER
        self.width = width #+ PUFFER
        self.height = height #+ PUFFER
        self.dimension = [self.length, self.width, self.height]
        self.create_Box()
        
    def create_Box(self):
        A = np.array([0, self.height, self.length])
        B = np.array([self.width, self.height, self.length])
        C = np.array([self.width, 0, self.length])
        D = np.array([0, 0, self.length])
        E = np.array([0, self.height,0])
        F = np.array([self.width, self.height,0])
        G = np.array([self.width, 0, 0])
        H = np.array([0, 0, 0])        
        self.vertices = np.array([A, B, C, D, E, F, G, H])
        return self

class MoveBox:

    def translate(self, mesh: np.array, translate_matrix= np.array([0.,0.,0.])):
        return mesh + translate_matrix

    def flip_right(self, mesh: np.array):
        x_move = max(mesh[:,0])
        y_move = max(mesh[:,1])
        translation_matrix = np.array([-x_move/2,-y_move/2,0])
        mesh = self.translate(mesh, translation_matrix)
        rotation_matrix = np.array([[np.cos(np.pi/2),-np.sin(np.pi/2),0],
                                    [np.sin(np.pi/2),np.cos(np.pi/2),0],
                                    [0,0,1]])
        mesh = np.matmul(mesh,rotation_matrix)
        translation_matrix = np.matmul(translation_matrix,rotation_matrix)
        mesh += np.abs(translation_matrix)
        return np.around(mesh, decimals= 1)


    def turn_right(self, mesh: np.array):
        z_move = max(mesh[:,0])        
        translation_matrix = np.array([0, 0, z_move])
        rotation_matrix = np.array([[np.cos(np.pi/2), 0 , -np.sin(np.pi/2)],
                                    [0, 1 , 0],
                                    [np.sin(np.pi/2), 0, np.cos(np.pi/2)]])
        mesh = np.matmul(mesh,rotation_matrix)
        mesh += translation_matrix
        return np.around(mesh, decimals= 1)

class Palette:

    empty_result= {
        'length_count': 0,
        'height_count': 0,
        'left_height_count': 0,
        'right_height_count': 0,
        'left_length_count': 0,
        'top_rest': 0,
        'sum_box': 0
    }

    def __init__(self):
        self.length = 119.5 + 3
        self.width = 80 + 2
        self.thickness = 14.4
        self.height = 200 - 5 - self.thickness
        

    def same2(self,box: Box, length= False):       
        height_count, length_count = 0, 0
        if np.floor(self.width/box.width) != 2:
            return Palette.empty_result

        else:
            height_count = np.floor(self.height/box.height)  
            if length:            
                length_count = np.floor(self.length/box.length)
            else:
                length_count = 2    
            height_rest = self.height - height_count*box.height
            top_rest, top_rest_max = 0, 0
            if height_rest > box.length or height_rest > box.width:
                top_rest = np.floor(self.width/box.length) * np.floor(self.length/box.height)
                top_rest_max = top_rest
            
                top_rest = np.floor(self.width/box.height) * np.floor(self.length/box.length)
                if top_rest > top_rest_max:
                    top_rest_max = top_rest                
            else:
                top_rest_max = 0
            if top_rest_max > 5:
                top_rest_max = 0

            return  {
                'length_count': length_count,
                'height_count': height_count,
                'left_height_count': 0,
                'right_height_count': 0,
                'left_length_count': 0,
                'top_rest': int(top_rest_max),
                'sum_box': length_count*2*height_count+top_rest_max
            }


    def WH_Sym(self,box1: Box,box2: Box):
        right_height_count, left_height_count = 0, 0
                
        if (box1.width + box2.width <= self.width) and np.floor(self.length/box1.length) == 2:
                left_height_count = np.floor(self.height/box1.height)
                right_height_count = np.floor(self.height/box2.height)
                return {
                    'length_count': 0,
                    'height_count': 0,
                    'left_height_count': left_height_count,
                    'right_height_count': right_height_count,
                    'left_length_count': 0,
                    'top_rest': 0,
                    'sum_box': 2*(left_height_count + right_height_count)
                }
        return Palette.empty_result

                

    def LH_LW_Asym(self,box_L2: Box,box2: Box):
        left_length_count, left_height_count = 0, 0

        if (box_L2.width + box2.width <= self.width) and np.floor(self.length/box2.length) == 2:
            left_height_count = np.floor(self.height/box_L2.height)
            left_length_count = np.floor(self.length/box_L2.length)

            height_rest = self.height - left_height_count*box_L2.height
            top_rest_max = 0
            if height_rest > box2.width:
                top_rest_max = 2*np.floor(height_rest/box2.width)       
            return {
                'length_count': 0,
                'height_count': 0,
                'left_height_count': left_height_count,
                'right_height_count': 0,
                'left_length_count': left_length_count,
                'top_rest': int(top_rest_max),
                'sum_box': (left_length_count + 2) * left_height_count + top_rest_max
            }
        return Palette.empty_result


def create_boxes(length: float, width: float, height: float):
    move_module = MoveBox()
    box_W2 = Box(length, width, height)
    new_shape = move_module.flip_right(mesh= box_W2.vertices)
    box_H2 = Box(length= np.max(new_shape[:,2]),
             width= np.max(new_shape[:,0]),
             height= np.max(new_shape[:,1]))
    new_shape= move_module.turn_right(box_H2.vertices)
    box_L2H = Box(length= np.max(new_shape[:,2]),
             width= np.max(new_shape[:,0]),
             height= np.max(new_shape[:,1]))
    new_shape = move_module.turn_right(box_W2.vertices)
    box_L2W = Box(length= np.max(new_shape[:,2]),
             width= np.max(new_shape[:,0]),
             height= np.max(new_shape[:,1]))
    return box_W2, box_H2, box_L2W, box_L2H

@st.cache_data
def calculate_box_arrange(input_df: pd.DataFrame):
    result = pd.DataFrame()
    max_way = dict()
    for index, row in input_df.iterrows():
        if row['carton_height_cm']*row['carton_length_cm']*row['carton_width_cm'] == 0:
            print(f'{row.article_no} has zero dimension')
            continue
        pallete = Palette()
        box_W2, box_H2, box_L2W, box_L2H = create_boxes(length= row['carton_length_cm'],
            width= row['carton_width_cm'],
            height= row['carton_height_cm'])

        W2 = pallete.same2(box= box_W2)
        if W2['top_rest'] == 0:
            W2['way'] = 'W2'
        else:
            W2['way'] = f"W2 top {W2['top_rest']}"   
        if W2['length_count'] > 2:
            W2['sum_box'] = 0
        W2 = pd.DataFrame.from_dict([W2])

        H2 = pallete.same2(box= box_H2)
        if H2['top_rest'] == 0:
            H2['way'] = 'H2'
        else:
            H2['way'] = f"H2 top {H2['top_rest']}"        
        H2 = pd.DataFrame.from_dict([H2])
        
        L2H = pallete.same2(box= box_L2W, length= True)
        if L2H['top_rest'] == 0:
            L2H['way'] = 'L2H'
        else:
            L2H['way'] = f"L2H top {L2H['top_rest']}"        
        L2H = pd.DataFrame.from_dict([L2H])
        
        L2W = pallete.same2(box= box_L2H, length= True)
        if L2W['top_rest'] == 0:
            L2W['way'] = 'L2W'
        else:
            L2W['way'] = f"L2W top {L2W['top_rest']}"        
        L2W = pd.DataFrame.from_dict([L2W])
        
        WH_Sym = pallete.WH_Sym(box1=box_W2, box2= box_H2)
        WH_Sym['way'] = 'WH_Sym'
        WH_Sym = pd.DataFrame.from_dict([WH_Sym])
        
        LH_Asym = pallete.LH_LW_Asym(box_L2= box_L2H, box2= box_H2)
        LH_Asym['way'] = 'LH_Asym'
        LH_Asym = pd.DataFrame.from_dict([LH_Asym])
        
        LW_Asym = pallete.LH_LW_Asym(box_L2= box_L2W, box2= box_W2)
        if LW_Asym['top_rest'] == 0:
            LW_Asym['way'] = 'LW_Asym'
        else:
            LW_Asym['way'] = f"LW_Asym top {LW_Asym['top_rest']}"
        
        LW_Asym = pd.DataFrame.from_dict([LW_Asym])
        
        temp = pd.concat([W2,H2,L2H,L2W,WH_Sym,LH_Asym,LW_Asym], ignore_index= True)
        temp['article_no'] = row['article_no']
        max_way[f"{row['article_no']}"] = temp.loc[temp['sum_box'] == temp['sum_box'].max(), 'way'].values[0]
        result = pd.concat([result, temp], ignore_index= True)
    result = result.assign(
        article_no = result.article_no.astype(int),
        length_count = result.length_count.astype(int),
        height_count = result.height_count.astype(int),
        left_height_count = result.left_height_count.astype(int),
        right_height_count = result.right_height_count.astype(int),
        left_length_count = result.left_length_count.astype(int),
        sum_box = result.sum_box.astype(int),
        top_rest = result.top_rest.astype(int)
    ).drop_duplicates(['article_no', 'way'])
    return result, max_way

def create_plot_data(grid: dict, box_plot: Box):
    _move_tools = MoveBox()
    current_length_count, mesh_plot = 1, []
    current_mesh = box_plot.vertices
    straight_translate_matrix = np.array([0,0,box_plot.length])
    change_layer_matrix = np.array([0, box_plot.height, -(grid['length_count']-1)*box_plot.length])
    for i in range(2,grid["length_count"]*grid['height_count']+2):
        mesh_plot.append(
        go.Mesh3d(
            x=current_mesh[:,0],
            y=current_mesh[:,1],
            z=current_mesh[:,2],
            i = BOX_VERTICES_INDEX[0,:],
            j = BOX_VERTICES_INDEX[1,:],
            k = BOX_VERTICES_INDEX[2,:],
            showscale=True))
        if current_length_count == grid['length_count']:
            current_length_count = 1
            # straight_translate_matrix += np.array([1,1,-1])
            current_mesh = _move_tools.translate(
                mesh= current_mesh,
                translate_matrix= change_layer_matrix
            )
            continue        
        current_mesh = _move_tools.translate(
            mesh= current_mesh,
            translate_matrix= straight_translate_matrix
        )
        current_length_count += 1
    return mesh_plot

def create_palette_mesh(pal_length: float, pal_width: float, pal_height: float):
    palette = Box(pal_length, pal_width, -pal_height)
    palette_under = go.Mesh3d(
        x=palette.vertices[:,0],
        y=palette.vertices[:,1],
        z=palette.vertices[:,2],
        i = BOX_VERTICES_INDEX[0,:],
        j = BOX_VERTICES_INDEX[1,:],
        k = BOX_VERTICES_INDEX[2,:],
        showscale=True)
    # change palette to a plank at the top
    palette.vertices[:,1] = Palette().height
    palette_up = go.Mesh3d(
        x=palette.vertices[:,0],
        y=palette.vertices[:,1],
        z=palette.vertices[:,2],
        i = BOX_VERTICES_INDEX[0,:],
        j = BOX_VERTICES_INDEX[1,:],    
        k = BOX_VERTICES_INDEX[2,:],
        showscale=True)
    return [palette_under, palette_up]

@st.cache_data
def plot_box_arrangement(article_info: pd.DataFrame, key: str, count_info: pd.DataFrame):
    box_dict = {
        "box_W2":"",
        "box_H2":"",
        "box_L2W":"",
        "box_L2H":"",
    }
    box_dict['box_W2'], box_dict['box_H2'], box_dict["box_L2H"], box_dict["box_L2W"] = create_boxes(length= article_info['carton_length_cm'].values[0],
            width= article_info['carton_width_cm'].values[0],
            height= article_info['carton_height_cm'].values[0])
    # palette mesh
    pal = Palette()
    move_tools = MoveBox()
    palette_mesh = create_palette_mesh(pal_length=pal.length, pal_width=pal.width, pal_height= pal.thickness)
    count_info = count_info[count_info['way'] == key]
    if '2' in key:
        right_box = box_dict[f"box_{key}"]
        right_count = {"length_count": count_info.length_count.values[0], "height_count": count_info.height_count.values[0]}
        right_side = create_plot_data(grid= right_count, box_plot= right_box)
        right_box.vertices = move_tools.translate(mesh=right_box.vertices, translate_matrix=np.array([right_box.width, 0., 0.]))
        left_side = create_plot_data(grid= right_count, box_plot= right_box)
    elif key == "WH_Sym":
        right_box = box_dict["box_W2"]      
        left_box = box_dict["box_H2"]
        left_box.vertices = move_tools.translate(mesh=left_box.vertices, translate_matrix=np.array([right_box.width, 0., 0.]))
        right_count = {"length_count": 2, "height_count": count_info.left_height_count.values[0]}
        right_side = create_plot_data(grid= right_count, box_plot= right_box)
        left_count = {"length_count": 2, "height_count": count_info.right_height_count.values[0]}
        left_side = create_plot_data(grid= left_count, box_plot= left_box)
    elif key == "LH_Asym":
        right_box = box_dict["box_H2"]      
        left_box = box_dict["box_L2W"]
        left_box.vertices = move_tools.translate(mesh=left_box.vertices, translate_matrix=np.array([right_box.width, 0., 0.]))
        right_count = {"length_count": 2, "height_count": count_info.left_height_count.values[0]}
        right_side = create_plot_data(grid= right_count, box_plot= right_box)
        left_count = {"length_count": count_info.left_length_count.values[0], "height_count": count_info.left_height_count.values[0]}
        left_side = create_plot_data(grid= left_count, box_plot= left_box)
    elif key == "LW_Asym":
        right_box = box_dict["box_W2"]      
        left_box = box_dict["box_L2H"]
        left_box.vertices = move_tools.translate(mesh=left_box.vertices, translate_matrix=np.array([right_box.width, 0., 0.]))
        right_count = {"length_count": 2, "height_count": count_info.left_height_count.values[0]}
        right_side = create_plot_data(grid= right_count, box_plot= right_box)
        left_count = {"length_count": count_info.left_length_count.values[0], "height_count": count_info.left_height_count.values[0]}
        left_side = create_plot_data(grid= left_count, box_plot= left_box)
    palette_mesh.extend(right_side)
    palette_mesh.extend(left_side)

    return palette_mesh

st.markdown('<p style="text-align:center;font-size:40px;font-weight: bold">View pallet arrangement </p>', unsafe_allow_html= True)

with open(CSS_FOLDER/'main.css') as css_file:
    st.markdown(f"<style>{css_file.read()}</style>", unsafe_allow_html=True)

with st.expander(f"Function description:", expanded= True):
    st.markdown("""
        <p>
        This is a function for an ERP web application for an e-commerce seller. In this particular example, the seller needs to determine and visualizing the most efficient way to
        organize a product on a pallet such that the maximum quantity is achieved without compromising the workflow of other tasks. 

        The interactive graphs below show how the cartons of each product is organize in 7 different pre-determined ways. The maximum quantity and orientation is marked red in the table above the graphs.

        Because of security reasons, all of the data used for this demonstration are randomly self-created and stored in a simple csv file.
        In real case, the data should be gathered from a database using SQL.
        </p>
    """, unsafe_allow_html= True)
    
INBOUND = pd.read_csv(DATA_SOURCE / "sum_inbound.csv")
format_dict = {
    'carton_length_cm':"{:.1f}",
    'carton_width_cm':"{:.1f}",
    'carton_height_cm':"{:.1f}",
    'gross_weight':"{:.2f}",
}
with st.expander("inbound_summary", expanded= False):
    df_return, selected_row = create_AgGrid(df=INBOUND, selection_mode= False)
    st.download_button(
            label= f'sum_inbound',
            data = INBOUND.assign(
                new_carton_length_cm= INBOUND['carton_length_cm'],
                new_carton_width_cm= INBOUND['carton_width_cm'],
                new_carton_height_cm= INBOUND['carton_height_cm'],
                new_qnt_box= INBOUND['qnt_box']
            ).to_csv(index= False).encode('utf-8'),
            file_name= f'sum_inbound.csv',
            mime='csv'
        )

result_arrange, max_arrange = calculate_box_arrange(input_df= INBOUND)
result_max_only = result_arrange.sort_values(by=['sum_box'], ascending= False).drop_duplicates(['article_no'])
# result_max_only = pd.merge(left= INBOUND[['article_no','model','qnt_box', 'status']].drop_duplicates(['article_no']), right= result_max_only, how='left', left_on = 'article_no', right_on='article_no')

with st.expander("view arrangement on pallete", expanded= True):
    df_return, selected_row = create_AgGrid(result_max_only, button_key= "max_arrange", selection_mode= True)
    st.download_button(
            label= f'Download box arrangement',
            data = result_max_only.to_csv(index= False).encode('utf-8'),
            file_name= f'box_arrangement.csv',
            mime='csv'
        )
    selected_article = int(selected_row[0]['article_no'])

    def highlight_max(df: pd.Series, threshold: float):
        if df.sum_box == threshold:
            return ['background-color: red'] * len(df)
        else:
            return ['background-color: black'] * len(df)

    # arrange_selected = pd.merge(left= INBOUND[INBOUND['article_no']==selected_article][['article_no','model']].drop_duplicates(['article_no']),
    #                             right= result_arrange[result_arrange['article_no'] == selected_article],
    #                             how='left', left_on = 'article_no', right_on='article_no')
    arrange_selected = result_arrange[result_arrange['article_no'] == selected_article]
    st.table(arrange_selected.style.apply(highlight_max, threshold= arrange_selected['sum_box'].max(),axis=1))
    st.write(f'Test new dimension and qnt_box of {selected_article}')
    

    actual_column, test_column, view_test_column = st.columns(3)
    with test_column:
        dimension_dict = INBOUND[INBOUND['article_no']==selected_article].to_dict(orient='records')[0]
        test_form = st.form('test_product_dimension')
        test_length = test_form.text_input(label= f'test carton length of {selected_article}', key= 'length', value= dimension_dict['carton_length_cm'])
        test_width = test_form.text_input(label= f'test carton width of {selected_article}', key= 'width', value= dimension_dict['carton_width_cm'])
        test_height= test_form.text_input(label= f'test carton height of {selected_article}', key= 'height', value= dimension_dict['carton_height_cm'])
        test_submitted = test_form.form_submit_button('Test new dimensions')
        try:
            test_length = float(test_length)
            test_width = float(test_width)
            test_height = float(test_height)
        except:
            st.error("dimension and qnt_box must be numbers")
            st.stop()
        temp_df = pd.DataFrame.from_dict([{
            'article_no': int(selected_article),
            'carton_length_cm': test_length,
            'carton_width_cm': test_width,
            'carton_height_cm': test_height,
        }])
        # if test_submitted:
        #     st.table(st.session_state["test_arrange"])
        #     st.table(arrange_selected[st.session_state['test_arrange'].columns].compare(st.session_state["test_arrange"]))
    with actual_column:     
        view_way = st.radio(horizontal= True, options = result_arrange[result_arrange['article_no'] == selected_article].way, label="")
        mesh_data = plot_box_arrangement(
            article_info= INBOUND[INBOUND['article_no']==selected_article],
            key= view_way,
            count_info= result_arrange[result_arrange['article_no'] == selected_article]
        )
        fig_arrangement = go.Figure(data=mesh_data)
        fig_arrangement.update_scenes(aspectmode= "data")
        camera = dict(
            up=dict(x=0, y=1, z=0),
            center=dict(x=0, y=0, z=0),
            eye=dict(x=0, y=0, z=4)
        )
        fig_arrangement.update_layout(scene_camera= camera)
        st.plotly_chart(fig_arrangement, use_container_width= True)
        # fig_arrangement.show()
    with view_test_column:
        test_arrange, test_max_arrange = calculate_box_arrange(input_df= temp_df)
        st.session_state['test_arrange'] = test_arrange
        # st.table(test_arrange.style.apply(highlight_max, threshold= test_arrange['sum_box'].max(),axis=1))
        test_way = st.radio(horizontal= True, options = result_arrange[result_arrange['article_no'] == selected_article].way, label="View test arrangement")
        test_mesh_data = plot_box_arrangement(
            article_info= temp_df,
            key= test_way,
            count_info= test_arrange
        )
        fig_test_arrangement = go.Figure(data=test_mesh_data)
        fig_test_arrangement.update_scenes(aspectmode= "data")
        fig_test_arrangement.update_layout(scene_camera= camera)
        st.plotly_chart(fig_test_arrangement, use_container_width= True)