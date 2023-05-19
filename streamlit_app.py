from io import BytesIO
import win32security
from streamlit_option_menu import option_menu
import streamlit as st
import streamlit.components.v1 as components
from st_aggrid import AgGrid, GridUpdateMode
from st_aggrid.shared import DataReturnMode
from st_aggrid.grid_options_builder import GridOptionsBuilder
import base64
import pandas as pd
import os
import glob
import re
import numpy as np
from datetime import datetime, date
from itertools import cycle, repeat
from styling import *
import sqlite
from oracle import *
from time import sleep
from collections import defaultdict
import market
import chat
import td
from tfs import get_work_items, create_tfs_session
# from st_material_table import st_material_table
# pd.set_option('display.float_format','{:.0f}'.format)
pd.set_option('display.precision', 1)

title = 'atlas'
st.set_page_config(page_title=title,
    page_icon='🌍',
    layout='wide',
    initial_sidebar_state='expanded') #collapsed
    
# from streamlit.report_thread import get_report_ctx
# st.write(get_report_ctx())
# from streamlit.server.server import Server
# session_id = get_report_ctx().session_id
# session_info = Server.get_current()._get_session_info(session_id)
# print(session_id)
# print(session_info)


def get_base64_of_bin_file(bin_file):
    """
    function to read png file 
    ----------
    bin_file: png -> the background image in local folder
    """
    with open(bin_file, 'rb') as f:
        data = f.read()
    return base64.b64encode(data).decode()


def set_png_as_page_bg(image_file):
    """
    function to display png as bg
    ----------
    png_file: png -> the background image in local folder
    """
    bin_str = get_base64_of_bin_file(image_file)
    _, img_ext = os.path.splitext(image_file)
    page_bg_img = '''
    <style>
    section[class="main css-1v3fvcr eknhn3m1"] {
    background-image: url("data:image/%s;base64,%s");
    background-size: cover;
    }
    </style>
    ''' % (img_ext, bin_str)
    
    st.markdown(page_bg_img, unsafe_allow_html=True)
    return


# @st.cache(allow_output_mutation=True)
def local_css(css_file):
    with open(css_file, encoding='utf8') as f:
        css_style = f.read()
    st.markdown('''<style>%s</style>''' % (css_style), unsafe_allow_html=True)


def get_base_tariff(tariff):
    if 'Супер' in tariff:
        base_tariff = tariff.replace("Супер", "Мой")
    elif 'Промо' in tariff:
        base_tariff = tariff.replace("Промо", "")
    else:
        base_tariff = tariff
    base_tariff = re.sub("[0-9]", "", base_tariff)
    base_tariff = base_tariff.strip()
    return base_tariff


@st.experimental_memo(show_spinner=True)
def branch_to_region(branch):
    region = branch
    replace_dict = {
        'Ханты-Мансийск':'ХМАО',
        'Салехард': 'ЯНАО',
        'Ростов-на-Дону':'Ростов',
        ' NEW': '',
        'Великий ': 'В.',
        'Нижний ': 'Н.',
        'Санкт-': 'С.',
    }
    for k, v in replace_dict.items():
        region = region.replace(k, v)
    return region


@st.experimental_memo(show_spinner=True)
def region_to_td_region(region):
    replace_dict = {
        'Абакан': 'Хакасия',
        'Йошкар-Ола': 'Марий Эл',
        'Улан-Удэ': 'Бурятия',
        'Чебоксары': 'Чувашия',
        'Ростов': 'Ростов на Дону',
        'Норильск':	'Красноярск',
        'Краснодар': 'Краснодар и Адыгея'
    }
    for k, v in replace_dict.items():
        region = region.replace(k, v)
    return region


# TABLES_DICT = {'PRODUCT_CHANGES':'PRODUCT_CHANGES','INSTALLMENTS':'INSTALLMENTS'}
OVER_THEME = {'txc_inactive': 'white','menu_background':'#07090a','txc_active':'white','option_active':'#1f2229'}
FONT_FMT = {'font-class':'h2','font-size':'150%'}

SERVERNAME = 'corp.tele2.ru'

CLUSTERS = ['Saint Petersburg', 'Moscow', 'Challenger Elite', 'Challenger',
       'Defender', 'Share hungry']

M = [['Супер разговор 3', 'Супер онлайн 2', 'Супер онлайн+ 1', 'Супер онлайн+ 3', None, 'Классический'],
             ['Супер разговор 2', 'Супер онлайн 1', 'Мой онлайн+', 'Супер онлайн+ 2', None, 'Premium'],
             ['Супер разговор 1', 'Мой онлайн', 'Супер онлайн 3', 'Супер онлайн 4', None, None],
             ['Мой разговор', 'Супер разговор 4', 'Супер разговор 5', 'Супер разговор 6', None, None]
             ]

FEE_CONDITION_TARIFFS = ['Супер онлайн+ 1', 'Супер онлайн+ 3', 'Мой онлайн+', 'Супер онлайн+ 2']

MARKET_COLUMNS = [
    'REGION_NAME', 'CLUSTER_NAME', 'REPORT_DATE', 'OPERATOR', 'TARIFF_TYPE', 'IS_SHELF',
    'TARIFF_NAME', 'FEE_STR', 'FEE_TYPE', 'VOICE_MIN_STR', 'DATA_GB_STR', 'SMS_STR', 'USAGE', 
    'UNLIM', 'INTERNET_EXTRA', 'VOICE_NOTES', 'DATA_NOTES', 'PROMO', 'TARIFF_INDEX'
]

CONSTRUCTOR_PARAMS = [
    'FEE_TYPE', 'IS_SHELF', 'IS_CONVERGENT', 'FEE', 'IS_FEE_DISCOUNT', 'FEE_AFTER_DISCOUNT',
    'VOICE_MIN', 'DATA_GB', 'EXTRA', 'USAGE', 'INTERNET_EXTRA', 
]

TOOLTIP_DICT = {
    'OPERATOR':'Оператор',
    'TARIFF':'Название тарифа',
    'FEE_TYPE':'Метод списания',
    'IS_SHELF':'Полочный',
    'IS_CONVERGENT':'Конвергентный',
    'FEE':'АП',
    'IS_FEE_DISCOUNT':'Есть скидка на АП',
    'FEE_AFTER_DISCOUNT':'АП после скидки',
    'VOICE_MIN':'Пакет минут',
    'DATA_GB':'Пакет data',
    'PROMO': 'Промо',
    'USAGE':'Куда действуют',
    'INTERNET_EXTRA':'Интернет, дополнительно'
}





def check_matrice(M, direction):
    '''
    проверяет значение из предыдущих столбцов, если direction='columns'
    и из предыдущих строк, если direction='rows'
    '''
    if direction == 'rows':
        M = np.transpose(M[::-1])
    elif direction == 'diagonal':
        M = np.fliplr(M)
    elif direction == 'columns':
        pass
    true_list = []
    if direction  in ['rows','columns']:
        for cur_x in range(len(M)):
            for cur_y in range(1, len(M[cur_x])):
                for other_y in range(len(M[cur_x])):
                    if other_y < cur_y:
                        must_be_less = M[cur_x][other_y]
                        must_be_more = M[cur_x][cur_y]
                        if must_be_less and must_be_more:
                            true_list.append(must_be_less < must_be_more)
    elif direction == 'diagonal':
        for cur_x in range(1, len(M)):
            for cur_y in range(1, len(M[cur_x])):
                for n in range(1, len(M)):
                    if cur_x >= n and cur_y >= n:
                        must_be_less = M[cur_x][cur_y]
                        must_be_more = M[cur_x - n][cur_y - n]
                        if must_be_less and must_be_more:
                            true_list.append(must_be_less < must_be_more)
    return all(true_list)


# def check_fee(dict=dict()):
#     temp_M = [row[0:4] for row in M]
#     for row_num, row in enumerate(temp_M):
#         for col_num, tar in enumerate(row):
#             if dict:
#                 if tar in dict:
#                     temp_M[row_num][col_num] = dict.get(tar)
#             elif tar == st.session_state.TARIFF:
#                 temp_M[row_num][col_num] = st.session_state['FEE']
#             else:
#                 temp_M[row_num][col_num] = st.session_state['FEE_M'][row_num][col_num]
#     return all([check_matrice(temp_M, direction='columns'),
#         check_matrice(temp_M, direction='rows'),
#         check_matrice(temp_M, direction='diagonal')])


def check_if_accept_changes(branch=None):
    '''
    проверяет, можно ли фиксировать изменения по пакетам и АП
    '''
    check_dict = {}
    for check_metric in ['FEE', 'DATA_GB', 'VOICE_MIN']:
        temp_M = [row[0:4] for row in M]
        for row_num, row in enumerate(temp_M):
            for col_num, tar in enumerate(row):
                if tar == st.session_state.TARIFF:
                    temp_M[row_num][col_num] = st.session_state[check_metric]
                else:
                    temp_M[row_num][col_num] = st.session_state[f'{check_metric}_M'][row_num][col_num]
        # проверяем соблюдение условий в матрице
        if check_metric == 'FEE':
            # if branch != 'Самара NEW':
            check_dict[check_metric] = all([check_matrice(temp_M, direction='columns'),
                                            check_matrice(temp_M, direction='rows'),
                                            check_matrice(temp_M, direction='diagonal')])
        elif check_metric == 'DATA_GB':
            check_dict[check_metric] = check_matrice(temp_M, direction='rows')
        elif check_metric == 'VOICE_MIN':
            check_dict[check_metric] = check_matrice(temp_M, direction='columns')
    return check_dict
    

SO_PLUS_BRANCHES = [
    'Владивосток',
    'Салехард',
    'Саратов',
    'Сахалин',
    'Биробиджан',
    'Оренбург',
    'Чебоксары',
    'Камчатка',
    'Пенза',
    'Калуга',
    'Волгоград',
    'Абакан',
    'Ульяновск',
    'Киров',
    'Псков',
    'Москва',
]

M16 = [row[:4] for row in M]
M16_list =  [val for sublist in M16 for val in sublist]
COLUMNS_TO_RENDER = ['OPERATOR', 'TARIFF', 'FEE_TYPE', 'FEE', 'FEE_AFTER_DISCOUNT',
                'DATA_GB', 'VOICE_MIN', 'USAGE', 'INTERNET_EXTRA', 'ACTION']

if 'inst_periods' not in st.session_state: st.session_state.inst_periods = list(range(1, 31))
if 'is_constructor' not in st.session_state: st.session_state.is_constructor = False
if 'sidebar_id' not in st.session_state: st.session_state.sidebar_id = None
if 'scenario_name' not in st.session_state: st.session_state.scenario_name = None
if 'constructor' not in st.session_state: st.session_state.constructor = dict()
if 'action_record' not in st.session_state: st.session_state.action_record = dict()
if 'tele2_tariffs' not in st.session_state: st.session_state.tele2_tariffs = list()
if 'Оператор' not in st.session_state: st.session_state['Оператор'] = 'Tele2'
if 'BRANCH_NAME' not in st.session_state: st.session_state.BRANCH_NAME = 'Абакан NEW'
if 'REGION_NAME' not in st.session_state: st.session_state.REGION_NAME = branch_to_region(st.session_state.BRANCH_NAME)
if 'market_view' not in st.session_state: st.session_state.market_view = 'main'
if 'main_page_id' not in st.session_state: st.session_state.main_page_id = 'Рынок'


def check_one_row(tar1, tar2):
    for row in M16:
        if tar1 in row and tar2 in row:
            return True
    return False


def check_one_column(tar1, tar2):
    temp_M = np.transpose(M16)
    for row in temp_M:
        if tar1 in row and tar2 in row:
            return True
    return False    



curdir = os.path.dirname(os.path.realpath(__file__)) + '\\'
css_file = os.path.join(curdir, r'style.css')
local_css(css_file)


def update_launch_name():
    st.session_state.LAUNCH_NAME = st.session_state.SEL_LAUNCH_NAME


def get_back_to_branches():
    st.session_state.TARIFF = None
    st.session_state.sidebar_id = None
    if 'region_scenario' in st.session_state:
        del st.session_state.region_scenario


def get_back_to_scenarios():
    st.session_state.market_view = 'main'
    st.session_state.sidebar_id = 'Список сценариев'
    if 'region_scenario' in st.session_state:
        del st.session_state.region_scenario


def cancel_edit():
    st.session_state.dic_copy_from = None
    st.session_state.is_tariff_copying = False
    st.session_state.TARIFF = None


if 'TARIFF' not in st.session_state: st.session_state.TARIFF = None
if 'USERNAME' not in st.session_state: st.session_state.USERNAME = None
if 'show_what' not in st.session_state: st.session_state.show_what = 'matrice'
if 'branch_index' not in st.session_state: st.session_state.branch_index = 0
if 'scenarios' not in st.session_state: st.session_state.scenarios = list()


data_gb_options = [0, 1, 2, 3, 5, 6, 7, 8, 10, 12, 15, 20, 25, 30, 35, 40, 45, 50, 60]
voice_min_options = [0,100,150,200,250,300,350,400,450,500,550,600,650,700,800,900,1000,1500,2000,3000]

def convert_to_excel(df, drop_index=False):
    """ возвращает xlsx-объект для скачивания"""
    output = BytesIO()
    writer = pd.ExcelWriter(output, engine='xlsxwriter')
    df.reset_index(inplace=True, drop=drop_index)
    df.to_excel(writer, sheet_name='Sheet1', startrow=1, header=False, index=False)
    workbook = writer.book
    worksheet = writer.sheets['Sheet1']
    (max_row, max_col) = df.shape
    column_settings = [{'header': column} for column in df.columns]
    worksheet.add_table(0, 0, max_row, max_col - 1, {'columns': column_settings})
    worksheet.set_column(0, max_col - 1, 12)
    writer.save()
    processed_data = output.getvalue()
    return processed_data


def get_table_download_link(df, short_name, drop_index=False):
    """ возвращает кликабельную ссылку для скачивания checklists.xlsx"""
    val = convert_to_excel(df, drop_index=drop_index)
    b64 = base64.b64encode(val)  # val looks like b'...'
    href = f'''<a style="color: #00aae5;" href="data:application/octet-stream;base64,{b64.decode()}" 
        download="{short_name}.xlsx">Скачать таблицу</a>'''
    return href



# def get_df(conn, dicts, columns, index_columns=None):
#     df = pd.DataFrame(columns=columns)
#     # dtype = {k:v for k,v in get_dtypes(conn, table).items() if k in df.columns}
#     # df = df.astype(dtype, errors='ignore')
#     df = pd.concat([df, pd.DataFrame.from_records([dic for dic in dicts])])
#         # df.append(dic, ignore_index=True, sort=False)
#     st.session_state.repr_dic = sqlite.get_repr_dic(conn)
#     if index_columns:
#         df.set_index(index_columns, inplace=True)
#     df.rename(index=str,
#         columns={col_name: st.session_state.repr_dic.get(col_name, f'Столбец {col_num}') for col_num, col_name in enumerate(df.columns)}, 
#         inplace=True)
#     # df.rename(columns, axis=1, inplace=True)
#     return df



# @st.cache(allow_output_mutation=True)
def set_up_main_page(conn, show='matrice'):

    # st.radio('', options=['Рынок', 'Запуск', 'Чек-лист', 'Комментарии', 'Справочники'], key='main_page_id', on_change=get_back_to_branches)
    # st.write('')

    def populate_matrice(matrice, direction):
        if direction == 'columns':
            matrice = np.transpose(matrice)
        for row_num, row in enumerate(matrice):
            for value in row:
                if value: matrice[row_num] = list(repeat(value, len(row)))
        if direction == 'columns':
            matrice = np.transpose(matrice).tolist()
        return matrice

        
    def get_matrice(metric, records):
        matrice = [row[0:4] for row in M]
        fee_dic = dict()
        for record in records:
            fee_dic.update({record['TARIFF'] : record[metric]})
        for row_num, row in enumerate(matrice):
            for col_num, tar in enumerate(row):
                matrice[row_num][col_num] = fee_dic.get(tar, None)
        return matrice


    def send_for_setup():
        for table in ['PRODUCT_CHANGES', 'INSTALLMENTS']:
            records = sqlite.get_product_changes(
                conn, table, st.session_state.PRODUCT_CLUSTER_NAME, st.session_state.LAUNCH_NAME
            )
            with st.spinner(text=f'Меняю актуальность для старых записей в {table} ...'):
                update(table, st.session_state.PRODUCT_CLUSTER_NAME, st.session_state.LAUNCH_NAME)
            with st.spinner(text=f'Добавляю новые записи в {table} ...'):
                insert(table, records) 
            

    def show_send_cluster_for_setup(cluster, launch_name):
        some_branches_completed = sqlite.get_not_empty_branches(conn, cluster, launch_name)
        if st.session_state.PRODUCT_CLUSTER_NAME != '(All)':
            if some_branches_completed:
                if st.session_state.cluster_status != 'setup':
                    btn_text = f'Отправить {st.session_state.PRODUCT_CLUSTER_NAME} в настройку 🔧'
                else:
                    btn_text = f'Повторно отправить {st.session_state.PRODUCT_CLUSTER_NAME} в настройку 🔧'
                cols = st.columns([3, 1.5, 3])
                send_for_setup_btn = cols[1].button(btn_text, help='Отправить тарифы в хранилище для настройки')
                if send_for_setup_btn:
                    try:
                        send_for_setup()
                    except Exception as e:
                        print(e)
                        st.error('Что-то пошло не так')
                        st.stop()
                    else:
                        for branch in some_branches_completed:
                            st.session_state.BRANCH_NAME = branch
                            sqlite.add_branch_status(conn, st.session_state, status='setup')
                        with st.balloons():
                            sleep(2)
                        st.experimental_rerun()
        else:
            if some_branches_completed:
                st.info('Для отправки изменений в настройку выберите конкретный кластер')


    def reject_branch():
        sqlite.add_branch_status(conn, st.session_state, status='rejected')
        # st.experimental_rerun()


    def show_rejecting_branch():
        st.markdown('&nbsp;')
        cols = st.columns([6, 2, 6])
        cols[1].button('Вернуть бранч на доработку 👩🏼‍🏫', on_click=reject_branch)


    def show_send_branch_for_approval():
        st.markdown('&nbsp;')
        if st.session_state.actual_tariffs:
            cols = st.columns([6, 2, 6])
            send_branch_status_btn = cols[1].button('Отправить на согласование 🐾')
            if send_branch_status_btn:
                try:
                    sqlite.add_branch_status(conn, st.session_state, status='sent')
                except Exception as e:
                    print(e)
                    st.error('Что-то пошло не так')
                    st.stop()
                else:
                    with st.balloons():
                        sleep(2)
                    st.experimental_rerun()
        else:
            st.info('Cохраните хотя бы один тариф в рамках текущего проекта, чтобы отправить на согласование') 


    def show_send_or_reject(user_rights):
        if user_rights.get('IS_OWNER'):
            if st.session_state.branch_status in ('sent','setup'):
                show_rejecting_branch()
        elif user_rights.get('IS_INITIATOR'):
            if st.session_state.branch_status not in ('sent','setup'):
                show_send_branch_for_approval()

       
    def edit_tar(tar):
        if 'all_reg' in st.session_state:
            del st.session_state.all_reg
        st.session_state.TARIFF = tar

   
    

    if st.session_state.main_page_id == 'Запуск':
        # st.map(get_lat_long_df(st.session_state.BRANCH_NAME), zoom=8, use_container_width=False)
        
        stylize_header(st.session_state.BRANCH_NAME)
        st.write('')
        

        def show_last_branch_status():
            st.markdown('&nbsp;')
            status_time, username = sqlite.get_branch_status_meta(conn, st.session_state.BRANCH_NAME, st.session_state.LAUNCH_NAME)
            # st.session_state.branch_status
            if st.session_state.branch_status == 'setup':
                st.info(f'Отправлено в настройку {status_time} пользователем {username} 🔧')
            if st.session_state.branch_status == 'sent':
                st.success(f'Отправлено на согласование {status_time} пользователем {username} 🕑')
            elif st.session_state.branch_status == 'rejected':
                st.success(f'Отправлено на доработку {status_time} пользователем {username} 🕑')
            elif st.session_state.branch_status == 'editing':
                st.success(f'Взято в работу {status_time} пользователем {username} ✍️')

        
        
        def generate_sim_matrice(records):
            # if st.session_state.BRANCH_NAME in ('Санкт-Петербург', 'Санкт-Петербург NEW'):
            #     M[-1][-1] = 'Мой онлайн+ Промо'
            # if st.session_state.BRANCH_NAME.replace(' NEW','') in SO_PLUS_BRANCHES:
            #     M[-1][-1] = 'Супер онлайн+'
            ALL_TARIFFS = [value for sublist in M for value in sublist if value]
            for row_num, row in enumerate(M):
                main_cols = st.columns([1, 2, 2, 2, 2, 0.5, 2])
                gb = next((v for v in st.session_state.DATA_GB_M[row_num] if v is not None), None)
                with main_cols[0]:
                    stylize_gb(f'{str(int(gb))} Гб' if gb else '&nbsp;')
                for col_num, tar in enumerate(row, start=1):
                    if tar in ALL_TARIFFS:
                        rec = next((rec for rec in records if rec['TARIFF'] == tar), {'TARIFF':tar})
                        # base_tar = get_base_tariff(tar)
                        is_valid = rec.get('IS_VALID', True)
                        is_lightened = rec.get('IS_THIS_LAUNCH', False)
                        with main_cols[col_num].container():
                            with st.form(key=f'{tar}'):
                                tar_name = rec.get('TARIFF_NAME')
                                if tar == st.session_state.TARIFF:
                                    sim = draw_sim(row_num, col_num, (tar_name if tar_name else tar), rec, selected=False, valid=is_valid, is_lightened=is_lightened)
                                    st.markdown(sim, unsafe_allow_html=True)
                                    st.form_submit_button('', on_click=cancel_edit)
                                else:
                                    sim = draw_sim(row_num, col_num, (tar_name if tar_name else tar), rec, selected=True, valid=is_valid, is_lightened=is_lightened)
                                    st.markdown(sim, unsafe_allow_html=True)
                                    st.form_submit_button('', on_click=edit_tar, args=(tar, ))
                        # elif base_tar != tar:
                        #     base_rec = next((base_rec for base_rec in records if base_rec['TARIFF'] == base_tar), {'TARIFF':base_tar})
                        #     if base_rec:
                        #         with main_cols[col_num].container():
                        #             with st.form(key=f'{tar}'):
                        #                 if tar == st.session_state.TARIFF:
                        #                     draw_sim(row_num, col_num, tar, rec, selected=False, valid=is_valid, is_lightened=is_lightened)
                        #                     st.form_submit_button('', on_click=cancel_edit)
                        #                 else:
                        #                     draw_sim(row_num, col_num, tar, rec, selected=True, valid=is_valid, is_lightened=is_lightened)
                        #                     st.form_submit_button('', on_click=edit_tar, args=(tar, ))
                        #     else:
                        #         with main_cols[col_num].container():
                        #             draw_sim(row_num, col_num, tar, rec, locked=True)
                    else:
                        pass
                        # main_cols[col_num].markdown('&nbsp;')
            VOICE_MIN_M_tr = np.transpose(st.session_state.VOICE_MIN_M)
            for col_num, row in enumerate(VOICE_MIN_M_tr):
                voice = next((v for v in row if v is not None), None)
                with main_cols[col_num + 1]:
                    stylize_voice(f'{str(int(voice))} мин' if voice else '&nbsp;')


        def add_validation(records):
            fee_dict = dict()
            for rec in records:
                tariff = rec.get('TARIFF')
                if tariff in FEE_CONDITION_TARIFFS:
                    fee_dict[tariff] = rec.get('FEE', 0)
            tariffs_count = sum([x != 0 for x in fee_dict.values()])
            if tariffs_count == 4:
                fee_diff = (fee_dict['Супер онлайн+ 1'] + fee_dict['Супер онлайн+ 2']) - (fee_dict['Мой онлайн+'] + fee_dict['Супер онлайн+ 3'])
            else:
                fee_diff = 0
            for rec in records:
                rec['IS_THIS_LAUNCH'] = (True if rec.get('LAUNCH_NAME') == st.session_state.LAUNCH_NAME else False)
                tariff = rec.get('TARIFF')
                if fee_diff != 0 and tariff in FEE_CONDITION_TARIFFS:
                    rec['IS_VALID'] = False
                else:
                    rec['IS_VALID'] = True
            return records


        # ПОЛУЧАЕМ АКТУАЛЬНЫЕ ЗАПИСИ
        st.session_state.records = sqlite.get_records_by_branch(conn,
            st.session_state.LAUNCH_NAME, 
            st.session_state.launch_type, 
            st.session_state.BRANCH_NAME
        )
        st.session_state.records = add_validation(st.session_state.records)
        # st.session_state.records
        st.session_state.this_launch_records = [rec for rec in st.session_state.records if rec.get('IS_THIS_LAUNCH')]
        # st.session_state.this_launch_records


        # ПОЛУЧАЕМ МАТРИЦЫ АП И ПАКЕТОВ
        st.session_state.FEE_M = get_matrice('FEE', st.session_state.this_launch_records)
        st.session_state.VOICE_MIN_M = populate_matrice(
            get_matrice('VOICE_MIN', st.session_state.this_launch_records), direction='columns')
        st.session_state.DATA_GB_M = populate_matrice(
            get_matrice('DATA_GB', st.session_state.this_launch_records), direction='rows')

        # СТРОИМ МАТРИЦУ
        # st.markdown('&nbsp;')
        if not st.session_state.LAUNCH_NAME:
            st.markdown('''<p style="text-align: center; color: #758586">Нет активных запусков 😟</p>''', unsafe_allow_html=True)
        else:
            with st.container():
                generate_sim_matrice(st.session_state.records)
                # st.session_state.this_launch_records
                show_send_or_reject(st.session_state.user_rights)
                show_last_branch_status()

    elif st.session_state.main_page_id == 'Рынок':

        def get_files(folder_path):
            files = glob.glob(folder_path + '\Формат данных*.xlsx')
            files.sort(key=lambda x: os.path.getmtime(x), reverse=True)
            return iter(files)
            

        @st.experimental_memo(show_spinner=False)
        def get_date_from_filename(filename):
            max_date_str = os.path.splitext(filename)[0].split('_')[-1]
            max_date = datetime.strptime(max_date_str, "%d.%m.%y").date()
            return date.strftime(max_date, "%Y-%m-%d")


        @st.experimental_memo(show_spinner=False)
        def get_df_by_path(path):
            df = pd.read_excel(path, sheet_name='Свод', usecols='A:S', names=MARKET_COLUMNS)
            df['REPORT_DATE'] = df['REPORT_DATE'].astype(str)
            df = df.reindex(columns = list(df.columns),  fill_value = np.NaN).where((pd.notnull(df)), None)
            return df


        with st.container():
            header = st.session_state.BRANCH_NAME
            if 'region_scenario' in st.session_state: header += f''': {st.session_state.scenario_name}'''
            stylize_header(header)
                

        with st.spinner(text='Проверяю актуальность данных рынка...'):
            folder_path = r'\\corp.tele2.ru\plm_cluster\All\Формы мониторинга\Формат данных'
            files = glob.glob(folder_path + '\Формат данных*.xlsx')
            files_dict = {}
            for file in files:
                files_dict[file] = datetime.fromtimestamp(os.path.getmtime(file)).strftime('%Y-%m-%d %H:%M:%S') 
            local_max_time = max(files_dict.values())
            base_max_time = sqlite.get_market_max_date_time(conn)
            if local_max_time > base_max_time:
                latest_file = max(files_dict, key = files_dict.get)
                try:
                    market_df = get_df_by_path(latest_file)
                    market_df['DATE_TIME'] = local_max_time
                except PermissionError:
                    st.session_state.market_time = base_max_time
                else:
                    with st.spinner(text='Загружаю актуальные данные рынка...'):
                        sqlite.update_market(conn, market_df)
                    st.session_state.market_time = local_max_time
            else:
                st.session_state.market_time = local_max_time

        with st.spinner(text='Готовлю рыночную матрицу...'):
            st.session_state.region_market = sqlite.get_region_market_df(conn, st.session_state.REGION_NAME)        
        

        st.session_state.td_session = td.get_db_connection(date.today())
        td_region = region_to_td_region(st.session_state.REGION_NAME)
        
        with st.spinner(text='Загружаю продажи и миграции...'):
            with st.expander('SALES MIX & MIGRATIONS MIX'):
                st.write('')
                td.show_charts(st.session_state.td_session, td_region, 200)
                
        def format_operator(operator):
            dict = {'Tele2': 'T2', 'Мегафон': 'MGF', 'МТС': 'MTS', 'билайн': 'BEE', 'Мотив': 'MOT', 'Летай': 'LET'}
            if st.session_state.shares:
                return f'{dict.get(operator, operator)} ({st.session_state.shares.get(operator, 0):.1%})'
            else:
                return f'{dict.get(operator, operator)}'


        if not st.session_state.region_market.empty:
            with st.spinner(text='Загружаю доли рынка...'):
                st.session_state.shares = td.get_shares(st.session_state.td_session, td_region)
            operators = st.session_state.region_market['OPERATOR'].unique()
            cols = st.columns([3,0.2,0.9,0.9])
            cols[0].multiselect(label='', key='operators', options=operators, default=operators,
                format_func=format_operator
            )  
            cols[2].write('')   
            cols[2].write('')
            cols[2].checkbox('Только полочные', value=1, key='only_shelf')
            cols[3].write('')
            cols[3].write('')
            cols[3].checkbox('C конвергентом', value=1, key='include_convergent')
            

            
            

        if 'region_scenario' in st.session_state:

            def get_data_gb(row):
                if row['EXTRA'] == 'Нет' or not row['EXTRA']:
                    return row['DATA_GB']
                elif row['EXTRA'] == '5 GB':
                    return row['DATA_GB'] + 5
                elif row['EXTRA'] == '10 GB':
                    return row['DATA_GB'] + 10
                elif row['EXTRA'] == '15 GB':
                    return row['DATA_GB'] + 15
                elif row['EXTRA'] == 'Удвоение':
                    return row['DATA_GB'] * 2
                else:
                    return row['DATA_GB']


            df_to_render = st.session_state.region_scenario
            # st.dataframe(df_to_render)
            df_to_render.apply(lambda row: get_data_gb(row), axis=1)
            st.session_state.this_launch_records = [rec for rec in df_to_render[df_to_render['ACTION'] == 'Новый тариф'].to_dict('records')]
            st.session_state.FEE_M = get_matrice('FEE', st.session_state.this_launch_records)
            st.session_state.VOICE_MIN_M = populate_matrice(
                get_matrice('VOICE_MIN', st.session_state.this_launch_records), direction='columns')
            st.session_state.DATA_GB_M = populate_matrice(
                get_matrice('DATA_GB', st.session_state.this_launch_records), direction='rows')
        else:
            df_to_render = st.session_state.region_market
  

        if st.session_state.only_shelf:
            df_to_render = df_to_render[df_to_render['IS_SHELF'] == 1]
        if not st.session_state.include_convergent:
            df_to_render = df_to_render[df_to_render['IS_CONVERGENT'] == 0]
        df_to_render = df_to_render[df_to_render['OPERATOR'].isin(st.session_state.operators)]
        
        # st.dataframe(df_to_render)
        if df_to_render.empty:
            st.markdown('''<p style="text-align: center; font-family: Source Sans Pro; color: #373839">
                Бранч не найден 😟</p>''', unsafe_allow_html=True)
        else:
            st.markdown(f'''<p style="vertical-align: bottom; color: #515358;
                font-size: 12px; font-family: Tele2 TextSans; margin-bottom: 0;">
                Время обновления данных: {st.session_state.market_time}
            </p>''', unsafe_allow_html=True)
            components.html(
                market.render_market(df_to_render, TOOLTIP_DICT),
                height=900, 
                scrolling=False
            )

    elif st.session_state.main_page_id == 'Чек-лист':
        
        def show_last_cluster_status():
            # st.markdown('&nbsp;')
            status_time, username = sqlite.get_cluster_status_meta(conn, st.session_state.PRODUCT_CLUSTER_NAME, st.session_state.LAUNCH_NAME)
            if st.session_state.cluster_status == 'setup':
                st.info(f'Отправлено в настройку {status_time} пользователем {username} 🔧')
            if st.session_state.cluster_status == 'sent':
                if st.session_state.user_rights.get('IS_INITIATOR'):
                    st.success(f'Отправлено на согласование {status_time} пользователем {username} 🕑')
            elif st.session_state.cluster_status == 'rejected':
                if st.session_state.user_rights.get('IS_OWNER'):
                    st.success(f'Отправлено на доработку {status_time} пользователем {username} 🕑')


        branch_name_col, right_upper_col = st.columns([4, 6])
        with branch_name_col:
            stylize_header(st.session_state.PRODUCT_CLUSTER_NAME)

        checklists = ['Тарифные параметры','Рассрочки']
        if st.session_state.user_rights.get('IS_OWNER'): checklists.extend(['Микропакеты', 'Сборки'])
        right_upper_col.radio('', key='table_to_show', options=checklists)

        if st.session_state.table_to_show == 'Тарифные параметры':
            with st.spinner(text=f'Формирую чек-лист с тарифными параметрами {st.session_state.PRODUCT_CLUSTER_NAME}...'):
                product_changes = sqlite.get_this_launch_records(conn,
                    'PRODUCT_CHANGES',
                    st.session_state.PRODUCT_CLUSTER_NAME, 
                    st.session_state.LAUNCH_NAME
                )
                df = pd.DataFrame.from_records(product_changes)
                repr_dic = sqlite.get_repr_dic(conn)
                df.columns = [repr_dic.get(col, col) for col in df.columns]
                if not df.empty:
                    df1 = df.astype(str)
                    df1.replace({'None': '', 'nan': ''}, inplace=True)
                    # print(df1.to_records(index=False)[0])
                    gb = GridOptionsBuilder.from_dataframe(df1)
                    for col in ['Проект', 'Бранч', 'Тариф']:
                        gb.configure_column(col, pinned='left')
                    gb.configure_default_column(filterable=True, sortable=True, value=True)
                    gridOptions = gb.build()
                    AgGrid(df1, height=550, gridOptions=gridOptions,  reload_data=False,
                        enable_enterprise_modules=False, editable=False, allow_unsafe_jscode=True, 
                        theme='streamlit', key=f'product_changes {st.session_state.PRODUCT_CLUSTER_NAME}'
                    )
                    st.markdown(get_table_download_link(
                        df, f'Чек-лист {st.session_state.PRODUCT_CLUSTER_NAME}', drop_index=False), 
                        unsafe_allow_html=True)
                    st.markdown('&nbsp;')
                else:
                    st.markdown('''<p style="text-align: center; color: #758586">Здесь отображаются данные, внесенные в разделе "Запуск"</p>
                        ''', unsafe_allow_html=True)
        elif st.session_state.table_to_show == 'Рассрочки':
            with st.spinner(text=f'Формирую чек-лист с рассрочками {st.session_state.PRODUCT_CLUSTER_NAME}...'):
                installments = sqlite.get_this_launch_records(conn, 'INSTALLMENTS', st.session_state.PRODUCT_CLUSTER_NAME, st.session_state.LAUNCH_NAME)
                df = pd.DataFrame.from_records(installments)
                repr_dic = sqlite.get_repr_dic(conn)
                df.columns = [repr_dic.get(col, col) for col in df.columns]
                if not df.empty:
                    df1 = df.astype(str)
                    df1.replace({'None': '', 'nan': ''}, inplace=True)
                    # print(df1.to_records(index=False)[0])
                    gb = GridOptionsBuilder.from_dataframe(df1)
                    for col in ['Проект', 'Бранч', 'Тариф', 'Тип рассрочки', 'Со скидкой/без скидки']:
                        gb.configure_column(col, pinned='left')
                    gb.configure_default_column(filterable=True, sortable=True, value=True)
                    gridOptions = gb.build()
                    AgGrid(df1, height=550, gridOptions=gridOptions,  reload_data=False,
                        enable_enterprise_modules=False, editable=False, allow_unsafe_jscode=True, 
                        theme='streamlit', key=f'installments {st.session_state.PRODUCT_CLUSTER_NAME}'
                    )
                    st.markdown(get_table_download_link(
                        df, f'Рассрочки {st.session_state.PRODUCT_CLUSTER_NAME}', drop_index=False), 
                        unsafe_allow_html=True)
                    st.markdown('&nbsp;')
                else:
                    st.markdown('''<p style="text-align: center; color: #758586">Здесь отображаются данные, внесенные в разделе "Запуск"</p>
                        ''', unsafe_allow_html=True)


    
        # elif st.session_state.table_to_show == 'Настройки':
        #     with st.spinner(text=f'Формирую чек-лист с настройками {st.session_state.PRODUCT_CLUSTER_NAME}...'):
        #         df = get_pce_df(st.session_state.LAUNCH_NAME, st.session_state.PRODUCT_CLUSTER_NAME)
        #         cols_dict = dict()
        #         for col in df.columns:
        #             if '_ID' in col: cols_dict[col] = '{:,.2f}'.format
        #         if not df.empty:
        #             df = df.loc[:,~df.columns.duplicated()]
        #             st.dataframe(df.style.format(formatter=None, na_rep='-'), height=900)
        #             st.markdown(get_table_download_link(
        #                 df, f'Настройки {st.session_state.PRODUCT_CLUSTER_NAME}', drop_index=True), 
        #             unsafe_allow_html=True)
        #         else:
        #             st.info('Нет актуальных настроек для текущего проекта')
        
        elif st.session_state.table_to_show == 'Микропакеты':
            with st.spinner(text=f'Формирую чек-лист с микропакетами {st.session_state.PRODUCT_CLUSTER_NAME}...'):
                df = get_micro_df(st.session_state.LAUNCH_NAME, st.session_state.PRODUCT_CLUSTER_NAME)
                if not df.empty:
                    df1 = df.astype(str)
                    df1.replace({'None': '', 'nan': ''}, inplace=True)
                    for col in df1.columns:
                        df1[col] = df1[col].str.replace('.0', ' ', regex=False)
                    # print(df1.to_records(index=False)[0])
                    gb = GridOptionsBuilder.from_dataframe(df1)
                    for col in ['LAUNCH_NAME', 'BRANCH_NAME', 'Группа']:
                        gb.configure_column(col, pinned='left')
                    gb.configure_default_column(filterable=True, sortable=True, value=True)
                    gridOptions = gb.build()
                    AgGrid(df1, height=550, gridOptions=gridOptions,  reload_data=False,
                        enable_enterprise_modules=False, editable=False, allow_unsafe_jscode=True, 
                        theme='streamlit', key=f'product_micro {st.session_state.PRODUCT_CLUSTER_NAME}'
                    )
                    st.markdown(get_table_download_link(
                        df, f'Микропакеты {st.session_state.PRODUCT_CLUSTER_NAME}', drop_index=False), 
                        unsafe_allow_html=True)
                    st.markdown('&nbsp;')
                else:
                    st.info('Нет сформированных микропакетов для текущего проекта')
        
        elif st.session_state.table_to_show == 'Сборки':
            with st.spinner(text=f'Формирую чек-лист со сборками {st.session_state.PRODUCT_CLUSTER_NAME}...'):
                df = get_assemblings_df(st.session_state.LAUNCH_NAME, st.session_state.PRODUCT_CLUSTER_NAME)
                if not df.empty:
                    df1 = df.astype(str)
                    df1.replace({'None': '', 'nan': ''}, inplace=True)
                    for col in df1.columns:
                        df1[col] = df1[col].str.replace('.0', ' ', regex=False)
                    gb = GridOptionsBuilder.from_dataframe(df1)
                    for col in ['LAUNCH_NAME', 'BRANCH_NAME', 'Тариф']:
                        gb.configure_column(col, pinned='left')
                    gb.configure_default_column(filterable=True, sortable=True, value=True)
                    gridOptions = gb.build()
                    AgGrid(df1, height=550, gridOptions=gridOptions,  reload_data=False,
                        enable_enterprise_modules=False, editable=False, allow_unsafe_jscode=True, 
                        theme='streamlit', key=f'product_assembling {st.session_state.PRODUCT_CLUSTER_NAME}'
                    )
                    st.markdown(get_table_download_link(
                        df, f'Сборки {st.session_state.PRODUCT_CLUSTER_NAME}', drop_index=False), 
                        unsafe_allow_html=True)
                    st.markdown('&nbsp;')
                else:
                    st.info('Нет сформированных сборок для текущего проекта')

        show_last_cluster_status()
        if st.session_state.user_rights.get('IS_OWNER') or st.session_state.user_rights.get('IS_TESTER'):
            show_send_cluster_for_setup(st.session_state.PRODUCT_CLUSTER_NAME, st.session_state.LAUNCH_NAME)

    elif st.session_state.main_page_id == 'Комментарии':

        def leave_comment():
            comment = st.session_state.comment.replace(' ', '').replace('\n', '')
            if comment:
                sqlite.add_branch_comment(conn, st.session_state)
                st.session_state.comment = ''
        
        
        messages = sqlite.get_messages_by_branch(conn, st.session_state.BRANCH_NAME)
        components.html(
            chat.render_chat(messages),
            height=450, 
            scrolling=True
        )
        st.text_input('Оставить комментарий: ', value='', key='comment', on_change=leave_comment)        

    elif st.session_state.main_page_id == 'Справочники':
        st.write('')
        df = get_assemling_params()
        df1 = df.astype(str)
        df1.replace({'None': '', 'nan': ''}, inplace=True)
        gb = GridOptionsBuilder.from_dataframe(df1)
        gb.configure_column('PARAM_VALUE', editable=True, wrapText=True, autoHeight=True)
        gb.configure_column('TARIFF', pinned='left')
        gb.configure_column('ROWID', hide=True)
        gb.configure_default_column(filterable=True, sortable=True, value=True)
        gridOptions = gb.build()
        AgGrid(df1,
            height=550,
            gridOptions=gridOptions, 
            reload_data=False,
            enable_enterprise_modules=False, 
            # editable=True,
            allow_unsafe_jscode=True, 
            fit_columns_on_grid_load=True, 
            # data_return_mode=DataReturnMode.AS_INPUT,
            # update_mode=GridUpdateMode.MODEL_CHANGED,
            theme='streamlit',
            key='Ag_1'
        )
        

        if st.session_state.Ag_1:
            df = df[df['PARAM_1'] == 'Специальные предложения']
            # print(df)
            df1 = pd.DataFrame.from_records(st.session_state.Ag_1['rowData'])
            df1 = df1[df1['PARAM_1'] == 'Специальные предложения']
            # print(df1)
            # print(df1.head())
            # print(df.eq(df1))
            # df_new = pd.concat([df, df1]).drop_duplicates(keep=False).to_dict('records')
            # print(df_new)
            # record = pd.concat([df, df1]).drop_duplicates(keep=False).to_dict('records')[-1]
            # print(record)
            # if record:
            #     upd_assembling_params(record.get('PARAM_VALUE'), record.get('ROWID'))
       
    
    
    elif st.session_state.main_page_id == 'Рынок NEW':

        pass
        
        # from menu import component_toggle_buttons

        # if 'counter' not in st.session_state:
        #     st.session_state.counter = 0

        # def run_component(props):
        #     value = component_toggle_buttons(key='toggle_buttons', **props)
        #     return value

        # def handle_event(value):
        #     st.write('Received from component: ', value)


        # st.session_state.counter = st.session_state.counter + 1
        # props = {
        #     'initial_state': {
        #         'group_1_header': 'Choose an option from group 1',
        #         'group_2_header': 'Choose an option from group 2'
        #     },
        #     'counter': st.session_state.counter,
        #     'datetime': str(datetime.now().strftime("%H:%M:%S, %d %b %Y"))
        # }

        # handle_event(run_component(props)) 



def set_up_sidebar(conn, tariff=None, branch=None):

    if st.session_state.user_rights.get('IS_ADMIN'):

        def upd_rights(k):
            st.session_state.user_rights[k] = st.session_state[k]

        with st.expander('Права'):
            admin_rights = dict()
            for k, v in st.session_state.user_rights.items():
                if k not in ['IS_ADMIN', 'USERNAME'] and k.startswith('IS_'):
                    admin_rights[k] = v
                    st.checkbox(k, value=v, key=k, on_change=upd_rights, args=(k, ))
                # elif k == 'CLUSTER':
                #     if st.session_state.user_rights.get('IS_INITIATOR'):
                #         options = CLUSTERS
                #         st.selectbox('Кластер инициатора', options=options, index=0, key=k, on_change=upd_rights, args=(k, ))
                # elif k === 'BFUNCTION':
                #     options = ['(All)'] + CLUSTERS
                #     st.selectbox(k, options=options, index=options.index(v), key=k, on_change=upd_rights, args=(k, ))

   

    def set_up_tariff_form(conn, branch, tariff, launch_name):
        
        dic = sqlite.get_record(conn, branch, tariff, launch_name)
        tar_alias = dic.get('TARIFF_NAME')
        base_tariff = get_base_tariff(tariff)
        base_default_dic = sqlite.get_params_by_default(conn, base_tariff)
        default_dic = sqlite.get_params_by_default(conn, tariff)
        action = dic.get('ACTION')
        st.button('↩ Вернуться', on_click=cancel_edit)
        st.markdown('&nbsp;')
        tariff_col, copy_from_col = st.columns([4,1])
        with tariff_col:
            show_tariff_branch((tar_alias if tar_alias else tariff), branch)
        if tariff in M16_list and not action:
            init_copy_btn = copy_from_col.button('⎘', help="Копировать из тарифа...")
            st.write('')
            if init_copy_btn:
                set_up_copy_tariff()
        st.write('')
            
        
        if st.session_state.TARIFF == 'Классический':
            fee_type = ''
        else:
            if st.session_state.user_rights.get('IS_TESTER'):
                st.session_state.fee_types = ['Плавающий месяц', 'Сутки', '<Свой вариант>']
            else:
                st.session_state.fee_types = ['Плавающий месяц', 'Сутки']
            fee_type_slot = st.empty()
            if st.session_state.is_tariff_copying:
                fee_type_index = st.session_state.fee_types.index(st.session_state.dic_copy_from['FEE_TYPE'])
            elif dic.get('FEE_TYPE'):
                if dic['FEE_TYPE'] not in st.session_state.fee_types:
                    st.session_state.fee_types.insert(0, dic['FEE_TYPE'])
                fee_type_index = st.session_state.fee_types.index(dic['FEE_TYPE'])
            else:
                fee_type_index = 0
            if action:
                fee_type = dic.get('FEE_TYPE')
                custom_param('Тип АП', fee_type)
            else:
                fee_type = fee_type_slot.selectbox('Тип АП', options=st.session_state.fee_types, index=fee_type_index, 
                    help='Используется при расчете рассрочки')
            if fee_type == '<Свой вариант>':
                custom_fee_type = st.number_input(f'Введите кол-во дней периода АП', key='custom_fee_type', min_value=1, max_value=60, value=1, step=1)
                str_custom_fee_type = f'{str(custom_fee_type)} дн'
                st.session_state.FEE_TYPE = str_custom_fee_type   
            else:
                st.session_state.FEE_TYPE = fee_type


        if tariff == 'Безлимит':
            unlim_fee_options = [0, 300, 330, 350, 390, 400, 420, 450, 500, 550, 600, 650, 700, 750, 800, 850, 900,
                                    1000, 1100, 1300]
            if dic['FEE']:
                index = unlim_fee_options.index(dic['FEE'])
            else: index = 0
            if action:
                fee = dic.get('FEE')
                custom_param('АП', dic.get('FEE'))
            else:
                fee = st.selectbox('АП', options=unlim_fee_options, index=index)
            fee_after_discount = None
            is_fee_discount = None
            extra = None
            data_gb = 999
            voice_min = 500
            
            cl_min_price = None 
            tele2_calls_unlim = None
            trpl_name = f'{tariff} {fee}'
            is_cbm_change = 0
            is_mdp = 0
            mdp_base = None
            is_ctn_extender = base_default_dic.get('IS_CTN_EXTENDER', 0)
            ctn_extender_price = base_default_dic.get('CTN_EXTENDER_PRICE')
            is_intercity_extender = base_default_dic.get('IS_INTERCITY_EXTENDER', 0)
            intercity_extender_price = base_default_dic.get('INTERCITY_EXTENDER_PRICE')
            is_madagascar = base_default_dic.get('IS_MADAGASCAR',0)
            is_mvideo = base_default_dic.get('IS_MVIDEO', 0)
            is_bombastic = default_dic.get('IS_BOMBASTIC', 0)
            first_month_fee = None
            following_months_fee = None

        elif tariff == 'Premium':
            unlim_fee_options = [1500, 1800]
            if dic['FEE']:
                index = unlim_fee_options.index(dic['FEE'])
            else: 
                index = 0
            if action:
                fee = dic.get('FEE')
                custom_param('АП', dic.get('FEE'))
            else:
                fee = st.selectbox('АП', options=unlim_fee_options, index=index)
            fee_after_discount = None
            is_fee_discount = None
            extra = None
            data_gb = 60
            voice_min = 2000

            voice_min_col, data_gb_col = st.columns(2)
            with voice_min_col:
                custom_param('Пакет минут', voice_min)
            with data_gb_col:
                custom_param('Пакет Гб', data_gb)
            st.write('')

            is_installment = 0
            cl_min_price = None 
            tele2_calls_unlim = None
            trpl_name = f'{tariff} {fee}'
            is_cbm_change = 0
            is_mdp = 0
            mdp_base = None
            is_inst_mdp = 0
            # inst_mdp_type = None
            is_ctn_extender = base_default_dic.get('IS_CTN_EXTENDER', 0)
            ctn_extender_price = base_default_dic.get('CTN_EXTENDER_PRICE')
            is_intercity_extender = base_default_dic.get('IS_INTERCITY_EXTENDER', 0)
            intercity_extender_price = base_default_dic.get('INTERCITY_EXTENDER_PRICE')
            is_madagascar = base_default_dic.get('IS_MADAGASCAR',0)
            is_mvideo = base_default_dic.get('IS_MVIDEO', 0)
            is_bombastic = default_dic.get('IS_BOMBASTIC', 0)
            first_month_fee = None
            following_months_fee = None

        elif tariff == 'Классический':
            fee = None
            is_fee_discount = None
            price_versions = ['v. 0.3', 'v. 0.4', 'v. 0.5', 'v. 0.6', 'v. 0.7', 'v. 0.8', 'v. 0.9', 'v. 1',
                                'v. 1.1', 'v. 1.2', 'v. 1.3', 'v. 1.4', 'v. 1.5', 'v. 1.6', 'v. 1.7', 'v. 1.8', 'v. 1.9',
                                'v. 2', 'v. 2.5', 'v. 3', 'v. 4']
            if dic['CLASSIC_MINUTE_PRICE']:
                index = price_versions.index(dic.get('CLASSIC_MINUTE_PRICE'))
            else: 
                index = 0
            cl_min_price = st.selectbox('Стоимость минуты на ТП Классический', options=price_versions, index=index)
            unlim_versions = ['Нет', '(ПД) Безлимит на Tele2 v.1', '(ПД) Безлимит на Tele2 v.2',
                                '(ПД) Безлимит на Tele2 v.3', '(ПД) Безлимит на Tele2 v.4', '(ПД) Безлимит на Tele2 v.5']
            if dic['CLASSIC_MINUTE_PRICE']:
                index = unlim_versions.index(dic.get('TELE2_CALLS_UNLIM'))
            else: index = 0
            tele2_calls_unlim = st.selectbox('Безлимит на Tele2', options=unlim_versions, index=index)
            fee = None
            fee_after_discount = None
            extra = None
            data_gb = None
            voice_min = None
            is_installment = 0
            trpl_name = f'{tariff} {cl_min_price}'
            is_cbm_change = 0
            is_mdp = 0
            mdp_base = None
            is_inst_mdp = 0
            # inst_mdp_type = None
            is_ctn_extender = base_default_dic.get('IS_CTN_EXTENDER', 0)
            ctn_extender_price = base_default_dic.get('CTN_EXTENDER_PRICE')
            is_intercity_extender = base_default_dic.get('IS_INTERCITY_EXTENDER', 0)
            intercity_extender_price = base_default_dic.get('INTERCITY_EXTENDER_PRICE')
            is_madagascar = base_default_dic.get('IS_MADAGASCAR',0)
            is_mvideo = base_default_dic.get('IS_MVIDEO', 0)
            is_bombastic = default_dic.get('IS_BOMBASTIC', 0)
            first_month_fee = None
            following_months_fee = None

        elif tariff != 'Классический' and tariff != 'Безлимит':
 
            if st.session_state.is_tariff_copying:
                fee_value = int(st.session_state.dic_copy_from['FEE'])
            elif tariff in FEE_CONDITION_TARIFFS:
                fee_dict = dict()
                for tar in FEE_CONDITION_TARIFFS:
                    if tar == tariff:
                        fee_dict[tar] = dic['FEE'] if dic['FEE'] else 0
                    else:
                        rec = sqlite.get_record(conn, branch, tar, launch_name)
                        fee_dict[tar] = rec.get('FEE') if rec.get('FEE') else 0
                if not dic['FEE'] and sum([x != 0 for x in fee_dict.values()]) == 3:
                    fee_diff = (fee_dict['Супер онлайн+ 1'] + fee_dict['Супер онлайн+ 2']) - (fee_dict['Мой онлайн+'] + fee_dict['Супер онлайн+ 3'])
                else:
                    fee_diff = int(dic['FEE'] if dic['FEE'] else 0)
                fee_value = int(abs(fee_diff))
            else:
                fee_value = int(dic['FEE'] if dic['FEE'] else 0)
            
            if action:
                fee = dic.get('FEE')
                custom_param('АП', fee)
            else:
                fee = st.number_input('АП', min_value=0, max_value=10000, step=10, value=fee_value)
            
            if tariff in FEE_CONDITION_TARIFFS:
                fee_dict[tariff] = fee
                if sum([x != 0 for x in fee_dict.values()]) == 4:
                    fee_diff = (fee_dict['Супер онлайн+ 1'] + fee_dict['Супер онлайн+ 2']) - (fee_dict['Мой онлайн+'] + fee_dict['Супер онлайн+ 3'])
                    if fee_diff != 0:
                        st.error(f'Условие по сумме докупок не выполняется!')
                        st.info(f'''Докупка до Супер Онлайн+ 3 {'меньше' if fee_diff > 0 else 'больше'}
                            суммы докупок младших тарифов на {abs(int(fee_diff))} руб''')
                    else:
                        st.info(f'Условие по сумме докупок выполняется')


            if st.session_state.is_tariff_copying:
                is_fee_discount_value = st.session_state.dic_copy_from['IS_FEE_DISCOUNT']
            elif fee != dic['FEE']:
                is_fee_discount_value = False
            else:
                is_fee_discount_value = (dic['IS_FEE_DISCOUNT'] if dic['IS_FEE_DISCOUNT'] else False)
            is_fee_discount = st.checkbox('Есть скидка на АП', value=is_fee_discount_value)

            if is_fee_discount:
                if st.session_state.is_tariff_copying:
                    fee_after_discount_value = st.session_state.dic_copy_from['FEE_AFTER_DISCOUNT']
                elif dic.get('FEE_AFTER_DISCOUNT'):
                    fee_after_discount_value = dic.get('FEE_AFTER_DISCOUNT')
                else:
                    fee_after_discount_value = 0
                fee_after_discount = st.number_input('АП со скидкой', min_value=0, max_value=int(fee),
                    step=10, value=fee_after_discount_value
                )
            else:
                fee_after_discount = None

            if 'custom_extra_input' not in st.session_state:
                st.session_state.custom_extra_input = False

            if not st.session_state.custom_extra_input:
                if st.session_state.is_tariff_copying:
                    extra_index = st.session_state.extras.index(st.session_state.dic_copy_from['EXTRA'])
                elif dic.get('EXTRA'):
                    if dic['EXTRA'] not in st.session_state.extras:
                        st.session_state.extras.insert(0, dic['EXTRA'])
                    extra_index = st.session_state.extras.index(dic['EXTRA'])
                else: 
                    extra_index = 0
                if action:
                    extra = dic.get('EXTRA')
                    custom_param('Доп пакеты и удвоения', extra)
                else:
                    extra = st.selectbox('Доп пакеты и удвоения', options=st.session_state.extras, index=extra_index)
                if extra == st.session_state.extras[-1]:
                    st.session_state.custom_extra_input = True
                    st.experimental_rerun()
            else:
                extra = None
                with st.expander(label='Доп пакеты и удвоения', expanded=True):
                    custom_extra = st.text_input(f'Введите свой вариант',
                        value=dic.get('CUSTOM_EXTRA',''), key='CUSTOM_EXTRA')
                    cols = st.columns(3)
                    cancel_custom_extra = cols[1].button('Отмена')
                if cancel_custom_extra:
                    st.session_state.custom_extra_input = False
                    st.experimental_rerun()
                st.markdown('&nbsp;')
                if custom_extra:
                    st.session_state.extras.insert(0, custom_extra)
                    st.session_state.custom_extra_input = False
                    st.experimental_rerun()


            # ПАКЕТЫ DATA & VOICE
            voice_min_col, data_gb_col = st.columns(2)

            with voice_min_col:
                if action:
                    voice_min = dic.get('VOICE_MIN')
                    custom_param('Пакет минут', voice_min)
                elif tariff == base_tariff or tariff == 'Супер онлайн+ 3':
                    if st.session_state.is_tariff_copying:
                        voice_min_index = voice_min_options.index(st.session_state.dic_copy_from['VOICE_MIN'])
                    elif dic['VOICE_MIN']:
                        voice_min_index = voice_min_options.index(dic['VOICE_MIN'])
                    else: 
                        voice_min_index = 0
                    voice_min = voice_min_col.selectbox('Пакет минут', options=voice_min_options, index=voice_min_index)
                else:  
                    for tar in st.session_state.actual_tariffs:
                        if check_one_column(st.session_state.TARIFF, tar):
                            rec = sqlite.get_record(conn, branch, tar, launch_name)
                            voice_min = rec.get('VOICE_MIN')
                            custom_param('Пакет минут', voice_min)
                            break
                    else:
                        if st.session_state.is_tariff_copying:
                            voice_min_index = voice_min_options.index(st.session_state.dic_copy_from['VOICE_MIN'])
                        elif dic['VOICE_MIN']:
                            voice_min_index = voice_min_options.index(dic['VOICE_MIN'])
                        else: 
                            voice_min_index = 0
                        voice_min = voice_min_col.selectbox('Пакет минут', options=voice_min_options, index=voice_min_index)

            with data_gb_col:
                if action:
                    data_gb = dic.get('DATA_GB')
                    custom_param('Пакет Гб', data_gb)
                elif tariff == base_tariff or tariff == 'Супер онлайн+ 3':
                    if st.session_state.is_tariff_copying:
                        data_gb_index = data_gb_options.index(st.session_state.dic_copy_from['DATA_GB'])
                    elif dic['DATA_GB']:
                        data_gb_index = data_gb_options.index(dic['DATA_GB'])
                    else: 
                        data_gb_index = 0
                    data_gb = data_gb_col.selectbox('Пакет Гб', options=data_gb_options, index=data_gb_index)
                else:
                    for tar in st.session_state.actual_tariffs:
                        if check_one_row(st.session_state.TARIFF, tar):
                            rec = sqlite.get_record(conn, branch, tar, launch_name)
                            data_gb = rec['DATA_GB']
                            custom_param('Пакет Гб', data_gb)
                            break
                    else:
                        if st.session_state.is_tariff_copying:
                            data_gb_index = data_gb_options.index(st.session_state.dic_copy_from['DATA_GB'])
                        elif dic['DATA_GB']:
                            data_gb_index = data_gb_options.index(dic['DATA_GB'])
                        else: 
                            data_gb_index = 0
                        data_gb = data_gb_col.selectbox('Пакет Гб', options=data_gb_options, index=data_gb_index)
                        
            st.write('')
    
            if st.session_state.user_rights.get('IS_OWNER'):
                is_ctn_extender_value = dic.get('IS_CTN_EXTENDER', 0)
                is_ctn_extender = st.checkbox('Пакет Гб', value=is_ctn_extender_value)
            else:
                is_ctn_extender = base_default_dic.get('IS_CTN_EXTENDER', 0)
                custom_checkbox('Пакет Гб', is_ctn_extender)
            if is_ctn_extender:
                ctn_extender_price = base_default_dic.get('CTN_EXTENDER_PRICE')
                custom_param('Цена расширителя ГТС', int(ctn_extender_price))
            else:
                ctn_extender_price = None
            
            if st.session_state.user_rights.get('IS_TESTER'):
                is_intercity_extender_value = dic.get('IS_INTERCITY_EXTENDER', 0)
                is_intercity_extender = st.checkbox('Нужен расширитель МГ', value=is_intercity_extender_value)
            else:
                is_intercity_extender = base_default_dic.get('IS_INTERCITY_EXTENDER', 0)
                custom_checkbox('Нужен расширитель МГ', is_intercity_extender)
            if is_intercity_extender:
                if tariff == 'Мой онлайн':
                    mo_fee = fee
                    mo_plus_fee = sqlite.get_record(conn, branch, 'Мой онлайн+', launch_name).get('FEE')
                    if mo_plus_fee:
                        if mo_fee:
                            intercity_extender_price = mo_plus_fee - mo_fee
                            if intercity_extender_price <= 50:
                                intercity_extender_price = 50
                            elif intercity_extender_price <= 100:
                                intercity_extender_price = 100
                            elif intercity_extender_price <= 150:
                                intercity_extender_price = 150
                            else:
                                intercity_extender_price = 200
                        else:
                            intercity_extender_price = None
                            st.info('Для расчета цены на расширитель МГ сперва заполните АП') 
                            return
                    else:
                        intercity_extender_price = None
                        st.info('Для расчета цены на расширитель МГ сперва заполните Мой онлайн+')
                        return
                elif base_tariff != tariff and base_tariff == 'Мой онлайн':
                    intercity_extender_price = sqlite.get_record(conn, branch, base_tariff, launch_name).get('INTERCITY_EXTENDER_PRICE')
                    if not intercity_extender_price:
                        st.info('Для расчета цены на расширитель МГ сперва заполните Мой онлайн')
                        return
                else:
                    intercity_extender_price = base_default_dic.get('INTERCITY_EXTENDER_PRICE')
                if intercity_extender_price:
                    custom_param('Цена расширителя МГ', int(intercity_extender_price))
            else:
                intercity_extender_price = None


            is_madagascar_label = 'Нужен T&B Мадагаскар (14 дней)'
            if st.session_state.user_rights.get('IS_TESTER'):
                is_madagascar_value = dic.get('IS_MADAGASCAR', 0)
                is_madagascar = st.checkbox(is_madagascar_label, value=is_madagascar_value)
            else:
                if base_tariff == tariff:
                    is_madagascar = default_dic.get('IS_MADAGASCAR',0)
                    custom_checkbox(is_madagascar_label, is_madagascar)
                else:
                    if base_default_dic.get('IS_MADAGASCAR', 0):
                        if st.session_state.is_tariff_copying:
                            is_madagascar_value = st.session_state.dic_copy_from['IS_MADAGASCAR']
                        else: 
                            is_madagascar_value = dic.get('IS_MADAGASCAR', 0)
                        is_madagascar = st.checkbox(is_madagascar_label, value=is_madagascar_value)
                    else:
                        is_madagascar = 0
                        custom_checkbox(is_madagascar_label, is_madagascar) 


            is_mvideo_label = 'Нужен T&B МВидео (7 дней)'
            if st.session_state.user_rights.get('IS_TESTER'):
                is_mvideo_value = dic.get('IS_MVIDEO', 0)
                is_mvideo = st.checkbox(is_mvideo_label, value=is_mvideo_value)
            else:
                if base_tariff == tariff:
                    is_mvideo = default_dic.get('IS_MVIDEO',0)
                    custom_checkbox(is_mvideo_label, is_mvideo)
                else:
                    if base_default_dic.get('IS_MVIDEO', 0):
                        if st.session_state.is_tariff_copying:
                            is_mvideo_value = st.session_state.dic_copy_from['IS_MVIDEO']
                        else: 
                            is_mvideo_value = dic.get('IS_MVIDEO', 0)
                        is_mvideo = st.checkbox(is_mvideo_label, value=is_mvideo_value)
                    else:
                        is_mvideo = 0
                        custom_checkbox(is_mvideo_label, is_mvideo)
            

            is_bombastic_label = 'Нужны Бомбические цены'
            if st.session_state.user_rights.get('IS_TESTER'):
                is_bombastic_value = dic.get('IS_BOMBASTIC', 0)
                is_bombastic = st.checkbox(is_bombastic_label, value=is_bombastic_value)
            else:
                if base_tariff == tariff:
                    is_bombastic = default_dic.get('IS_BOMBASTIC', 0)
                    custom_checkbox(is_bombastic_label, is_bombastic)
                else:
                    if base_default_dic.get('IS_BOMBASTIC', 0):
                        if st.session_state.is_tariff_copying:
                            is_bombastic_value = st.session_state.dic_copy_from['IS_BOMBASTIC']
                        else: 
                            is_bombastic_value = dic.get('IS_BOMBASTIC', 0)
                        is_bombastic = st.checkbox(is_bombastic_label, value=is_bombastic_value)
                    else:
                        is_bombastic = 0
                        custom_checkbox(is_bombastic_label, is_bombastic)


            if st.session_state.is_tariff_copying:
                is_cbm_change_value = st.session_state.dic_copy_from['IS_CBM_CHANGE']
            else: 
                is_cbm_change_value = dic.get('IS_CBM_CHANGE', 0)
            is_cbm_change = st.checkbox('Нужна смена на акционные', value=is_cbm_change_value)
            

            if is_cbm_change:
                if is_fee_discount:
                    first_month_fee = st.selectbox('АП в первый месяц', [fee, fee_after_discount])
                    following_months_fee = fee_after_discount
                    custom_param('АП со второго месяца', following_months_fee)   
                else:
                    first_month_fee = fee
                    following_months_fee = fee
                    custom_param('АП в первый месяц', first_month_fee)
                    custom_param('АП со второго месяца', following_months_fee)
            else:
                first_month_fee = None
                following_months_fee = None

            if st.session_state.is_tariff_copying:
                is_mdp_value = st.session_state.dic_copy_from['IS_MDP']
            else: 
                is_mdp_value = dic.get('IS_MDP', 0)
            is_mdp = st.checkbox('Нужен МАП', value=is_mdp_value)
            if is_mdp:
                if is_fee_discount:
                    mdp_base_type_value = dic.get('MDP_BASE', 0)
                    if mdp_base_type_value == fee:
                        mdp_base_type_index = 0
                    else:
                        mdp_base_type_index = 1
                    mdp_base_type = st.radio('МАП в размере', options=['АП', 'АП со скидкой'], index=mdp_base_type_index)
                    if mdp_base_type == 'АП':
                        mdp_base = fee
                    elif mdp_base_type == 'АП со скидкой':
                        mdp_base = fee_after_discount
                    else:
                        mdp_base = None
                    st.write('')
                else:
                    mdp_base = fee
            else:
                mdp_base = None
            cl_min_price = None 
            tele2_calls_unlim = None
            trpl_name = f'{tariff} ({branch})'


            if st.session_state.user_rights.get('IS_TESTER'):
                is_installment_value = dic.get('IS_INSTALLMENT', 0)
                is_installment = st.checkbox('Нужна рассрочка', value=is_installment_value)
            else:
                if base_tariff != tariff:
                    if st.session_state.is_tariff_copying:
                        is_installment_value = st.session_state.dic_copy_from.get('IS_INSTALLMENT', 0)
                    else: 
                        is_installment_value = dic.get('IS_INSTALLMENT', 0)
                    is_installment = st.checkbox('Нужна рассрочка', value=is_installment_value)
                else:
                    is_installment = base_default_dic.get('IS_INSTALLMENT', 0)
                    custom_checkbox('Нужна рассрочка', is_installment)
        
            if is_installment:
                inst_periods = (dic.get('INSTALLMENT_PERIODS') if dic.get('INSTALLMENT_PERIODS') else '5,10,15')
                default_list = [int(per) for per in inst_periods.split(',')]
                if st.session_state.user_rights.get('IS_TESTER'):
                    st.multiselect('Типы рассрочек', key='sel_inst_periods',
                        options=set(st.session_state.inst_periods + default_list),
                        default=sorted(default_list)
                    )
                else:
                    st.session_state.sel_inst_periods = default_list
                installment_periods = ','.join(str(inst) for inst in st.session_state.sel_inst_periods)
                if not st.session_state.sel_inst_periods:
                    st.error('Введите хотя бы один тип рассрочки')
                is_inst_mdp_value = dic.get('IS_INST_MDP', 0)
                is_inst_mdp = st.checkbox('Нужен МАП на рассрочку', value=is_inst_mdp_value)
                if is_inst_mdp:
                    inst_mdp_base_options = [100, 150, 200]
                    inst_mdp_base_value = dic.get('INST_MDP_BASE')
                    if inst_mdp_base_value:
                        if inst_mdp_base_value not in inst_mdp_base_options:
                            inst_mdp_base_options.append(inst_mdp_base_value)
                        inst_mdp_base_index = inst_mdp_base_options.index(inst_mdp_base_value)
                    else:
                        inst_mdp_base_index = 0
                    inst_mdp_base = st.selectbox('База для МАП', options=inst_mdp_base_options, index=inst_mdp_base_index)
                else:
                    inst_mdp_base = None
            else:
                installment_periods = None
                is_inst_mdp = 0
                inst_mdp_base = None
            st.session_state['INSTALLMENT_PERIODS'] = installment_periods
            st.session_state['IS_INST_MDP'] = is_inst_mdp
            st.session_state['INST_MDP_BASE'] = inst_mdp_base
        if 'IS_INST_MDP' not in st.session_state: st.session_state['IS_INST_MDP'] = 0


        sms = base_default_dic.get('SMS', 0)
        if sms:
            st.session_state.SMS = sms
        else:
            st.session_state.SMS = 0
        if st.session_state.SMS > 0:
            sms_directions = ['по региону', 'по России']
            if tariff not in ['Безлимит', 'Везде онлайн', 'Premium']:
                if dic.get('SMS_DIRECTION'):
                    sms_dir_index = sms_directions.index(dic.get('SMS_DIRECTION', sms_directions[0]))
                else:
                    sms_dir_index = 0
                sms_dir = st.radio('Направление пакета SMS', options=sms_directions, index=sms_dir_index)
                st.session_state['SMS_DIRECTION'] = sms_dir
                
        if tariff == 'Безлимит':
            extra_sms = default_dic.get('EXTRA_SMS')
            custom_param('Доп пакет SMS', extra_sms)  
            extra_min = default_dic.get('EXTRA_MIN')
            custom_param('Доп пакет минут', extra_min) 
        else:
            extra_sms = None 
            extra_min = None
        extra_gb = None

        if st.session_state.is_tariff_copying:
            regional_value = st.session_state.dic_copy_from.get('REGIONAL', '')
        else: 
            regional_value = dic.get('REGIONAL', '')
        if not regional_value: regional_value = ''
        
        regional = dic.get('REGIONAL')
        if 'all_reg' not in st.session_state:
            if regional:
                st.session_state.all_reg = regional.split("; ")
            else:
                st.session_state.all_reg = []

        def add_reg():
            if 'reg_to_add' in st.session_state:
                if st.session_state.reg_to_add != '<Выберите TFS>':
                    st.session_state.all_reg.append(st.session_state.reg_to_add)

        def del_reg(reg):
            if reg in st.session_state.all_reg:
                st.session_state.all_reg.remove(reg)

        st.write('')
        st.header('Региональные акции')
        if not st.session_state.all_reg:
            st.caption('Здесь пока ничего нет. Добавьте региональные акции из результатов поиска')
            regional = ''
        else:    
            for reg in st.session_state.all_reg:
                with st.form(f'{reg}'):
                    st.write('')  
                    cols = st.columns([5, 1, 0.2])
                    cols[0].markdown(f'''<p style="overflow: hidden; font-size: 1vw; font_weight: bold;
                        margin-bottom: 5px;">{reg}</p>''', unsafe_allow_html=True)
                    cols[1].form_submit_button('❌', on_click=del_reg, args=(reg, ), help='Удалить')
                    st.write('')
            regional = '; '.join(st.session_state.all_reg)
        st.write('')
        
        search = st.text_input('Поиск по TFS', key='search_text')
        wit_list = []
        if search:
            if 'tfs_session' not in st.session_state:
                st.session_state.tfs_session = create_tfs_session()
            try:
                work_items = get_work_items(st.session_state.tfs_session, st.session_state.search_text)
            except Exception as e:
                print(e)
                st.error('Что-то пошло не так')
            else:
                if not work_items:
                    st.info('Не найдено ни одного результата. Попробуйте переформулировать запрос')
                else:
                    if len(work_items) > 30:
                        st.info('Найдено слишком много результатов. Попробуйте уточнить запрос')
                    else:
                        wit_list = ['<Выберите TFS>'] + [f"{item['WorkItemId']} {item['Title']}" for item in work_items]
                        wit_list = [wit for wit in wit_list if wit not in st.session_state.all_reg]
                        st.selectbox(label='Результаты поиска', help='Выберите из списка, чтобы добавить',
                            options=wit_list, key='reg_to_add', on_change=add_reg) 

        if st.session_state.is_tariff_copying:
            comments_value = st.session_state.dic_copy_from.get('COMMENTS', '')
        else: 
            comments_value = dic.get('COMMENTS', '')
        if not comments_value: comments_value = ''
        
        comments = st.text_area('Комментарии',
            value=comments_value, 
            max_chars=512,
            help='Пример: Мой помощник за 0 руб'
        )

        if is_fee_discount and tariff != base_tariff:
            base_rec = sqlite.get_record(conn, branch, base_tariff, launch_name)
            if fee_after_discount == base_rec.get('FEE'):
                discount_type = 'Скидка 100% на микро'
            else:
                discount_type = 'Скидка на ОТУ и микро'
        else:
            discount_type = None

        st.session_state['DISCOUNT_TYPE'] = discount_type
        st.session_state['IS_INSTALLMENT'] = is_installment
        st.session_state['IS_CBM_CHANGE'] = is_cbm_change
        st.session_state['IS_MDP'] = is_mdp
        st.session_state['MDP_BASE'] = mdp_base
        st.session_state['EXTRA'] = extra
        st.session_state['EXTRA_SMS'] = extra_sms
        st.session_state['EXTRA_MIN'] = extra_min
        st.session_state['EXTRA_GB'] = extra_gb
        st.session_state['REGIONAL'] = regional
        st.session_state['FEE'] = fee
        st.session_state['IS_FEE_DISCOUNT'] = is_fee_discount
        st.session_state['FEE_AFTER_DISCOUNT'] = fee_after_discount
        st.session_state['DATA_GB'] = data_gb
        st.session_state['VOICE_MIN'] = voice_min
        st.session_state['INTERCITY_INCLUDED'] = base_default_dic.get('INTERCITY_INCLUDED', 'Нет')
        st.session_state['IS_INTERCITY_EXTENDER'] = is_intercity_extender
        st.session_state['INTERCITY_EXTENDER_PRICE'] = intercity_extender_price
        st.session_state['CLASSIC_MINUTE_PRICE'] = cl_min_price
        st.session_state['TELE2_CALLS_UNLIM'] = tele2_calls_unlim      
        st.session_state['TRPL_NAME'] = trpl_name
        st.session_state['IS_CTN_EXTENDER'] = is_ctn_extender
        st.session_state['CTN_EXTENDER_PRICE'] = ctn_extender_price
        st.session_state['IS_BOMBASTIC'] = is_bombastic
        st.session_state['FIRST_MONTH_FEE'] = first_month_fee
        st.session_state['FOLLOWING_MONTHS_FEE'] = following_months_fee
        st.session_state['ACTION'] = action
        st.session_state['IS_MADAGASCAR'] = is_madagascar
        st.session_state['COMMENTS'] = comments
        
        
        if is_madagascar:
            st.session_state.MADAGASCAR_FEE = 0
            if voice_min:
                st.session_state.MADAGASCAR_MIN = voice_min/2
            if data_gb:
                st.session_state.MADAGASCAR_GB = data_gb/2
        else:
            st.session_state.MADAGASCAR_FEE = None
            st.session_state.MADAGASCAR_MIN = None
            st.session_state.MADAGASCAR_GB = None


        st.session_state.IS_MVIDEO = is_mvideo
        if is_mvideo:
            st.session_state.MVIDEO_FEE = 0
            if voice_min:
                st.session_state.MVIDEO_MIN = voice_min
            if data_gb:
                st.session_state.MVIDEO_GB = data_gb
        else:
            st.session_state.MVIDEO_FEE = None
            st.session_state.MVIDEO_MIN = None
            st.session_state.MVIDEO_GB = None


        st.session_state.IS_BOMBASTIC = is_bombastic
        if is_bombastic:
            if fee_after_discount:
                st.session_state.BOMBASTIC_PRICE = fee_after_discount * 3
            else:
                st.session_state.BOMBASTIC_PRICE = fee * 3
        else:
            st.session_state.BOMBASTIC_PRICE = None



        st.write('')
        error_slot = st.empty()
        
        if not st.session_state.is_editing_allowed:
            st.info('Вы не можете редактировать тариф в рамках этого запуска')
        else:
            if tariff in st.session_state.actual_tariffs: 
                cols = st.columns(2)
                add_btn = cols[0].button('Обновить')
                del_btn = cols[1].button('Удалить')    
            else:
                add_btn = st.button('Сохранить')
                del_btn = None

            if del_btn:
                sqlite.delete_record(conn,
                    st.session_state.LAUNCH_NAME,
                    st.session_state.BRANCH_NAME,
                    tariff
                )

                if st.session_state.branch_status == 'rejected' or not st.session_state.branch_status:
                    sqlite.add_branch_status(conn, st.session_state, status='editing')
                st.session_state.TARIFF = None
                st.session_state.dic_copy_from = None
                st.session_state.is_tariff_copying = False
                st.session_state.main_page_id = 'Запуск'
                st.experimental_rerun()

            if add_btn:
                if tariff != 'Классический' and (data_gb == 0 or voice_min == 0):
                    error_slot.error('Нулевые пакеты для тарифа неприменимы')
                elif fee == 0:
                    error_slot.error('АП не может быть нулевой')
                elif is_fee_discount and fee_after_discount == 0:
                    error_slot.error('АП со скидкой не может быть нулевой')
                else:
                    check_dict = check_if_accept_changes(st.session_state.BRANCH_NAME)
                    if all(check_dict.values()):
                        sqlite.add_record(conn, st.session_state)
                        if st.session_state.branch_status == 'rejected' or not st.session_state.branch_status:
                            sqlite.add_branch_status(conn, st.session_state, status='editing')
                        if tariff == 'Мой онлайн+':
                            mo_dict = sqlite.get_record(conn, branch, 'Мой онлайн', launch_name)
                            mo_fee = mo_dict.get('FEE')
                            mo_plus_fee = fee
                            if mo_fee and mo_plus_fee:
                                mo_dict['INTERCITY_EXTENDER_PRICE'] = mo_plus_fee - mo_fee
                                sqlite.add_record(conn, mo_dict)
                            else:
                                pass
                        for tar in st.session_state.actual_tariffs:
                            if tar != tariff:
                                if check_one_row(tariff, tar):
                                    rec = sqlite.get_record(conn, branch, tar, launch_name)
                                    rec.update({'DATA_GB':st.session_state.DATA_GB})
                                    sqlite.add_record(conn, rec)
                                elif check_one_column(tariff, tar):
                                    rec = sqlite.get_record(conn, branch, tar, launch_name)
                                    rec.update({'VOICE_MIN':st.session_state.VOICE_MIN})
                                    sqlite.add_record(conn, rec)
                        st.session_state.TARIFF = None
                        st.session_state.dic_copy_from = None
                        st.session_state.is_tariff_copying = False
                        st.session_state.main_page_id = 'Запуск'
                        st.experimental_rerun()
                    else:
                        for metric, accept_bool in check_dict.items():
                            if not accept_bool:
                                error_slot.error(f"{st.session_state.repr_dic.get(metric)} не удовлетворяет требованиям матрицы")


    def copy_tariff():
        st.session_state.dic_copy_from = sqlite.get_record(conn,
            st.session_state.BRANCH_NAME, 
            st.session_state.tar_copy_from, 
            st.session_state.LAUNCH_NAME
        )
        st.session_state.is_tariff_copying = True
        # st.experimental_rerun()


    def set_up_copy_tariff():
        tars_to_copy_from = [t for t in st.session_state.actual_tariffs if t != st.session_state.TARIFF and t in M16_list]
        st.selectbox('Выберите тариф', options=tars_to_copy_from, key='tar_copy_from')
        cols = st.columns(2)
        if tars_to_copy_from:
            cols[0].button('Копировать', on_click=copy_tariff)
        cols[1].button('Отменить')


    # _, image_col, _ = st.columns([1, 1, 1])
    # image_col.image('Tele2-PLM-logo.png', width=115)
    # st.markdown('&nbsp;')

    #   ЕСЛИ ВЫБРАН ТАРИФ, РИСУЕМ ТАРИФНЫЕ ПАРАМЕТРЫ
    def set_up_copy_branch():
        
        def copy_branch():
            branch_to = st.session_state.BRANCH_NAME
            branch_from = st.session_state.branch_to_copy_from
            sqlite.duplicate_branch(conn, 
                st.session_state.USERNAME, 
                branch_from,
                branch_to,
                st.session_state.LAUNCH_NAME, 
                st.session_state.LAUNCH_NAME)
            st.session_state.sidebar_id = None
            # st.experimental_rerun()

        def cancel_copy_branch():
            st.session_state.sidebar_id = None
            # st.experimental_rerun()

        not_empty_branches = sqlite.get_not_empty_branches(
            conn, st.session_state.PRODUCT_CLUSTER_NAME, st.session_state.LAUNCH_NAME
        )
        branches_for_copy = [b for b in not_empty_branches if b != st.session_state.BRANCH_NAME and b is not None]
        if branches_for_copy:
            st.selectbox('Копировать из', branches_for_copy, key='branch_to_copy_from')
            custom_param('В', st.session_state.BRANCH_NAME)
            cols = st.columns(2)
            cols[0].button('Копировать ✔', on_click=copy_branch)
            cols[1].button('Отменить ↩', on_click=cancel_copy_branch)
        else:
            with st.spinner(text='Нет доступных для копирования бранчей'):
                sleep(2)
            st.session_state.sidebar_id = None
            st.experimental_rerun()

    if st.session_state.TARIFF:
        set_up_tariff_form(conn,
            st.session_state.BRANCH_NAME, 
            st.session_state.TARIFF,
            st.session_state.LAUNCH_NAME)
        
    elif st.session_state.sidebar_id == 'Копирование бранча':

        def copy_branch(error_slot):
            branch_to = st.session_state.BRANCH_NAME
            branch_from = st.session_state.branch_to_copy_from
            launch_to = st.session_state.LAUNCH_NAME
            launch_from = st.session_state.launch_to_copy_from
            if branch_to == branch_from and launch_to == launch_from:
                with error_slot.error('Матрицы совпадают'):
                    sleep(1)
            else:
                sqlite.duplicate_branch(conn, st.session_state.USERNAME, 
                    branch_from, branch_to, launch_from, launch_to)
                with error_slot.success('Успешно'):
                    sleep(1)
                st.session_state.sidebar_id = None
            del st.session_state.launch_to_copy_from


        def cancel_copy_branch():
            st.session_state.sidebar_id = None

        st.button('↩ Вернуться', on_click=get_back_to_branches)
        st.markdown('&nbsp;')
        st.header('Копирование матрицы')
        if st.session_state.user_rights.get('IS_TESTER'):
            launch_type = st.radio('Выберите тип проекта', options=['test', 'prod'], index=0)
            launches = sqlite.get_launches(conn, launch_type)
            if st.session_state.LAUNCH_NAME in launches:
                launch_index = launches.index(st.session_state.LAUNCH_NAME)
            else:
                launch_index = 0
            launch_name = st.selectbox('Выберите проект',
                options=st.session_state.launches, 
                key='launch_to_copy_from',
                index=launch_index
            )
            not_empty_branches = sqlite.get_not_empty_branches_all(conn, st.session_state.launch_to_copy_from)
        else:
            st.session_state.launch_to_copy_from = st.session_state.LAUNCH_NAME
            not_empty_branches = sqlite.get_not_empty_branches(
                conn, st.session_state.PRODUCT_CLUSTER_NAME, st.session_state.launch_to_copy_from
            )
        error_slot = st.empty()
        if not_empty_branches:
            st.selectbox('Выберите бранч', not_empty_branches, key='branch_to_copy_from')
            cols = st.columns(2)
            cols[1].button('Копировать', on_click=copy_branch, args=(error_slot, ))
            cols[0].button('Отмена', on_click=cancel_copy_branch)
        else:
            st.caption('Нет доступных для копирования бранчей')
              
    elif st.session_state.sidebar_id == 'Очистка бранча':
        
        def clear_branch():
            sqlite.empty_branch(conn, st.session_state.BRANCH_NAME, st.session_state.LAUNCH_NAME)
            st.session_state.sidebar_id = None


        def cancel_clear_branch():
            st.session_state.sidebar_id = None


        st.markdown('''<p style="text-align: center;">
            Вы уверены, что хотите очистить матрицу?</p>
            ''', unsafe_allow_html=True) 
        cols = st.columns(2)
        cols[0].button('Отмена', on_click=cancel_clear_branch)
        cols[1].button('Очистить', on_click=clear_branch)

    elif st.session_state.sidebar_id == 'Список сценариев':

        if 'is_convertion' not in st.session_state:
            st.session_state.is_conversion = False

        def add_new_scenario():
            st.session_state.market_view = 'main'
            if st.session_state.new_scenario_name.replace(' ',''):
                sqlite.add_scenario(conn,
                    st.session_state.USERNAME, 
                    st.session_state.LAUNCH_NAME, 
                    st.session_state.REGION_NAME, 
                    st.session_state.new_scenario_name
                )


        def edit_scenario(scenario_id, scenario_name):
            st.session_state.market_view = 'scenario'
            st.session_state.scenario_id = scenario_id
            st.session_state.scenario_name = scenario_name
            st.session_state.sidebar_id = 'Сценарий'
            show_scenario(scenario_id, scenario_name)


        def init_convert_scenario(scenario_id, scenario_name):
            show_scenario(scenario_id, scenario_name)
            st.session_state.scenario_id = scenario_id
            st.session_state.scenario_name = scenario_name
            st.session_state.is_conversion = True


        def show_scenario(scenario_id, scenario_name):
            st.session_state.scenario_id = scenario_id
            st.session_state.scenario_name = scenario_name
            st.session_state.region_scenario = sqlite.get_region_scenario_df(conn, scenario_id)


        def init_upd_scenario_status(scenario_id, status):
            sqlite.upd_scenario_status(conn, scenario_id, status, st.session_state.USERNAME)


        def convert_into_launch():
            if 'old_scenario_id' in st.session_state:
                sqlite.clear_for_convert(conn, st.session_state.BRANCH_NAME, st.session_state.convert_launch_name)
                sqlite.del_scenario_status(conn, st.session_state.old_scenario_id, 'Передано в запуск')
                del st.session_state.old_scenario_id
            for rec in sqlite.get_actions(conn, st.session_state.scenario_id):
                tariff = rec.get('TARIFF')
                last_rec = sqlite.get_last_record(conn, st.session_state.BRANCH_NAME, tariff, st.session_state.launch_type)
                if not last_rec: 
                    base_tariff = get_base_tariff(tariff)
                    last_rec = sqlite.get_last_record(conn, st.session_state.BRANCH_NAME, base_tariff, st.session_state.launch_type)
                fee_type = rec.get('FEE_TYPE')
                for k, v in {'сут.': 'Сутки', 'мес.': 'Плавающий месяц'}.items():
                    fee_type = fee_type.replace(k, v)
                last_rec.update({
                    'ACTION': rec.get('ACTION'),
                    'LAUNCH_NAME': st.session_state.convert_launch_name,
                    'FEE_TYPE': fee_type,
                    'FEE': rec.get('FEE'),
                    'DATA_GB': rec.get('DATA_GB'),
                    'EXTRA': rec.get('EXTRA', 'Нет'),
                    'VOICE_MIN': rec.get('VOICE_MIN'),
                    'IS_FEE_DISCOUNT': rec.get('IS_FEE_DISCOUNT'),
                    'FEE_AFTER_DISCOUNT': rec.get('FEE_AFTER_DISCOUNT'),
                    'USERNAME': st.session_state.USERNAME
                })
                sqlite.add_record(conn, last_rec)
            sqlite.upd_scenario_status(conn, 
                st.session_state.scenario_id,
                'Передано в запуск', 
                st.session_state.USERNAME, 
                st.session_state.convert_launch_name
            )
            st.session_state.sidebar_id = 'Список сценариев'
            st.session_state.is_conversion = False


        st.button('↩ Вернуться', on_click=get_back_to_branches)
        st.markdown('&nbsp;')
        cols = st.columns([5, 1, 0.2])
        cols[0].header('Сценарии')
        if st.session_state.user_rights.get('IS_INITIATOR'):
            new_scenario_btn = cols[1].button('➕', help='Новый сценарий')
            if new_scenario_btn:
                with st.form('new_scenario_form'):
                    scenario_name = st.text_input('Введите название',
                        key='new_scenario_name', value='')
                    st.write('')
                    cols = st.columns(2)
                    cols[0].form_submit_button('ОК', on_click=add_new_scenario)
                    cols[1].form_submit_button('Отмена')
        st.session_state.scenarios = sqlite.get_scenarios(conn, st.session_state.REGION_NAME)
        if not st.session_state.scenarios:  
            st.caption('Пока нет сохраненных сценариев')
        else:
            st.write('')
            for num, scenario_dict in enumerate(st.session_state.scenarios):  
                # scenario_dict
                status = scenario_dict.get('STATUS')
                scenario_id = scenario_dict.get('SCENARIO_ID')
                scenario_name = scenario_dict.get('SCENARIO_NAME')
                act_max_date_time = scenario_dict.get('ACT_MAX_DATE_TIME')
                status_date_time = scenario_dict.get('STATUS_DATE_TIME')
                is_approver = st.session_state.user_rights.get('IS_APPROVER')
                is_initiator = st.session_state.user_rights.get('IS_INITIATOR')
                
                with st.form(f'{num} {scenario_name}'):
                    st.write('')  
                    cols = st.columns([5, 1, 0.4])
                    cols[0].markdown(f'''<p style="font-size: 1vw; font_weight: bold; margin-bottom: 5px;">
                            {scenario_name}</p>''', unsafe_allow_html=True)
                    cols[1].form_submit_button('👁️', on_click=show_scenario, args=(scenario_id, scenario_name), help='Показать сценарий')
                    st.markdown(f'''<p style="font-size: 0.6vw; color: grey; margin-bottom: 0;">
                        Создан: {scenario_dict.get('USERNAME')} <br>
                        Дата и время: {scenario_dict.get('DATE_TIME')}</p>''', unsafe_allow_html=True)
                    st.write('')
                    if not is_approver and is_initiator and (not status or status == 'Отклонено'):
                        st.form_submit_button('✏️ Редактировать', on_click=edit_scenario, args=(scenario_id, scenario_name), help='Редактировать сценарий')
                    if is_approver:
                        if status == 'На согласовании':
                            st.info(f'''Запрос на согласование от {scenario_dict.get('USERNAME')} {scenario_dict.get('STATUS_DATE_TIME')}''')
                            st.write('')
                            cols = st.columns(2)
                            cols[0].form_submit_button('Согласовать', on_click=init_upd_scenario_status, args=(scenario_id, 'Согласовано'))
                            cols[1].form_submit_button('Отклонить', on_click=init_upd_scenario_status, args=(scenario_id, 'Отклонено'))
                        elif status == 'Согласовано':
                            st.success(f'''Согласовано''')
                            st.form_submit_button('Отмена', on_click=init_upd_scenario_status, args=(scenario_id, 'На согласовании'))
                        elif status == 'Отклонено':
                            st.error(f'Отклонено')
                            st.form_submit_button('Отмена', on_click=init_upd_scenario_status, args=(scenario_id, 'На согласовании'))
                        elif status == 'Передано в запуск':
                            st.success(f'''Передано в запуск {scenario_dict.get('LAUNCH_NAME')} {scenario_dict.get('STATUS_DATE_TIME')}''')
                    elif is_initiator:
                        if not status and act_max_date_time:
                            st.form_submit_button('Отправить на согласование', on_click=init_upd_scenario_status, args=(scenario_id, 'На согласовании'))
                        elif status == 'На согласовании':
                            st.info('На согласовании')
                            st.form_submit_button('Отозвать запрос', on_click=init_upd_scenario_status, args=(scenario_id, None))
                        elif status == 'Согласовано':
                            st.success(f'''Согласовано пользователем {scenario_dict.get('STATUS_USERNAME')} {scenario_dict.get('STATUS_DATE_TIME')}''')
                            convert_slot = st.empty()
                            conv = convert_slot.form_submit_button('Конвертировать в запуск', on_click=init_convert_scenario, args=(scenario_id, scenario_name))
                            if conv:
                                with convert_slot:
                                    custom_param('Бранч', st.session_state.BRANCH_NAME)
                                convert_launches = sqlite.get_available_launches(conn, st.session_state.BRANCH_NAME, st.session_state.launch_type)
                                if convert_launches:
                                    st.selectbox('Выберите запуск', key='convert_launch_name', options=convert_launches)
                                    for rec in st.session_state.scenarios:
                                        if rec.get('LAUNCH_NAME') == st.session_state.convert_launch_name:
                                            if rec.get('STATUS') == 'Передано в запуск':
                                                st.info(f'''Внимание! Конвертация текущего сценария перезапишет
                                                уже сконвертированный в этот запуск сценарий "{rec.get('SCENARIO_NAME')}"
                                                ''')
                                                st.session_state.old_scenario_id = rec.get('SCENARIO_ID')
                                                break
                                    st.form_submit_button('Конвертировать', on_click=convert_into_launch)
                                    st.form_submit_button('Отмена')
                                else:
                                    st.info('Пока нет доступных для конвертации запусков. Обратитесь к инициатору проектов')
                        elif status == 'Отклонено':
                            if act_max_date_time < status_date_time:
                                st.error(f'''Отклонено пользователем {scenario_dict.get('STATUS_USERNAME')} {scenario_dict.get('STATUS_DATE_TIME')}''')
                            else:
                                st.form_submit_button('Отправить на согласование', on_click=init_upd_scenario_status, args=(scenario_id, 'На согласовании')) 
                        elif status == 'Передано в запуск':
                            st.success(f'''Передано в запуск {scenario_dict.get('LAUNCH_NAME')} {scenario_dict.get('STATUS_DATE_TIME')}''')


    elif st.session_state.sidebar_id == 'Сценарий':

        def init_edit_action(tariff):
            st.session_state.action_record = sqlite.get_action_by_tariff(conn, st.session_state.scenario_id, tariff)
            init_constructor()


        def init_delete_action(tariff):
            sqlite.delete_action(conn, st.session_state.scenario_id, tariff)


        def init_constructor():
            st.session_state.sidebar_id = 'Конструктор'
            st.session_state.market_view = 'scenario'


        def init_delete_scenario():
            sqlite.delete_scenario(conn, st.session_state.scenario_id)
            get_back_to_scenarios()


        def init_rename_scenario():
            sqlite.rename_scenario(conn, st.session_state.scenario_name, st.session_state.new_scenario_name)
            st.session_state.scenario_name = st.session_state.new_scenario_name


        st.button('↩ К сценариям', on_click=get_back_to_scenarios)
        st.markdown('&nbsp;')
        cols = st.columns([4, 1, 1, 0.2])
        cols[0].header(st.session_state.scenario_name)
        if not st.session_state.user_rights.get('IS_APPROVER'):
            rename_scenario_btn = cols[1].button('✏️', help='Переименовать сценарий')
            delete_scenario_btn = cols[2].button('❌', help='Удалить сценарий')
            rename_delete_slot = st.empty()
            if rename_scenario_btn:
                with rename_delete_slot.form('rename_scenario_form'):
                    scenario_name = st.text_input('Введите название',
                        key='new_scenario_name', value=st.session_state.scenario_name)
                    st.write('')
                    cols = st.columns(2)
                    cols[0].form_submit_button('ОК', on_click=init_rename_scenario)
                    cols[1].form_submit_button('Отмена')
            if delete_scenario_btn:
                with rename_delete_slot.form('delete_scenario_form'):
                    st.write('Вы уверены?')
                    st.write('')
                    cols = st.columns(2)
                    cols[0].form_submit_button('Да', on_click=init_delete_scenario)
                    cols[1].form_submit_button('Отмена')
        action_records = sqlite.get_actions(conn, st.session_state.scenario_id)
        st.write('')
        st.button('Добавить активность ➕', help='Добавить активность', on_click=init_constructor) 
        if not action_records:
            st.caption('Пока нет сохраненных активностей в этом сценарии')
        else:
            actions_to_render = pd.DataFrame.from_dict(action_records, orient='columns')
            actions_to_render['IS_SCENARIO'] = True
            actions_to_render['OPERATOR'] = 'Tele2'
            for action_record in action_records:
                tariff = action_record.get('TARIFF')
                with st.form(f'{tariff} action'):
                    st.write('')
                    cols = st.columns([4, 1, 1, 0.2])
                    cols[0].markdown(f'''<p style="font-size: 1.2vw; font_weight: bold; margin-bottom: 5px;">
                        {tariff}</p>''', unsafe_allow_html=True)
                    action = action_record.get('ACTION')
                    if action != 'Закрыть':
                        cols[1].form_submit_button('✏️', help='Редактировать активность', on_click=init_edit_action, args=(tariff, ))
                    cols[2].form_submit_button('❌', help='Удалить активность', on_click=init_delete_action, args=(tariff, ))
                    if action == 'Закрыть':
                        cols[0].markdown(f'''<p style = "font-family: Tele2 TextSans; color: #eb4343; margin-bottom: 3px;
                        font-size: 1vw; font-weight: regular;">{action}</p>''', unsafe_allow_html=True)
                        pass
                    elif action == 'Новый тариф':
                        cols[0].markdown(f'''<p style = "font-family: Tele2 TextSans; color: #00b5ef; margin-bottom: 10px;
                        font-size: 1vw; font-weight: regular;">{action}</p>''', unsafe_allow_html=True)
                        st.markdown(f'''<p style="font-size: 0.8vw; color: grey; margin-bottom: 0;">
                                    АП: {str(action_record.get('FEE'))}{'/' + str(action_record.get('FEE_AFTER_DISCOUNT'))
                                    if action_record.get('IS_FEE_DISCOUNT') else ''}</p>''', unsafe_allow_html=True)
                        for param, value in action_record.items():
                            if param in ['FEE_TYPE', 'IS_SHELF', 'IS_CONVERGENT','VOICE_MIN', 'EXTRAS', 'DATA_GB']:
                                st.markdown(f'''<p style="font-size: 0.8vw; color: grey; margin-bottom: 0;">
                                    {TOOLTIP_DICT.get(param, param)}: {value}</p>''', unsafe_allow_html=True)
                    elif action == 'Изменить':
                        market_record = st.session_state.region_market[
                            st.session_state.region_market["TARIFF"] == tariff].to_dict('records')[0]
                        are_there_changes = False
                        for param in CONSTRUCTOR_PARAMS:
                            new_value = action_record.get(param)
                            old_value = market_record.get(param)
                            if old_value != new_value:
                                st.markdown(f'''<p style="font-size: 0.8vw; color: grey; margin-bottom: 0;">
                                    {TOOLTIP_DICT.get(param, param)}: {old_value} → {new_value}</p>''', unsafe_allow_html=True)
                                are_there_changes = True
                        if not are_there_changes:
                            init_delete_action(action_record.get('TARIFF'))
                    st.write('')
        st.session_state.region_scenario = sqlite.get_region_scenario_df(conn, st.session_state.scenario_id)


    elif st.session_state.sidebar_id == 'Конструктор':

        def apply_action():
            sqlite.add_action(conn, st.session_state.constructor)
            st.session_state.action_record.clear()
            st.session_state.constructor.clear()
            st.session_state.sidebar_id = 'Сценарий'


        def check_action(action, record, slot):
            tariff = st.session_state.constructor.get('TARIFF')
            if not tariff:
                with slot.error('Название не может быть пустым'):
                    sleep(2)
                    return
            elif tariff.replace(' ', '') == '':
                with slot.error('Название не может быть пустым'):
                    sleep(2)
                    return
            if action == 'Изменить':
                if all(record.get(param) == st.session_state.constructor.get(param) for param in CONSTRUCTOR_PARAMS):
                    with slot.error('Нет изменений, которые можно применить'):
                        sleep(2)
                        return
                else:
                    apply_action()
            elif action == 'Новый тариф':
                check_dict = check_if_accept_changes()
                if all(check_dict.values()):
                    apply_action()
                else:
                    for metric, accept_bool in check_dict.items():
                        if not accept_bool:
                            with slot.error(f"{st.session_state.repr_dic.get(metric)} не удовлетворяет требованиям матрицы"):
                                sleep(2)
                                return
            else:
                apply_action()
            

        def cancel_action():
            st.session_state.action_record.clear()
            st.session_state.constructor.clear()
            st.session_state.sidebar_id = 'Сценарий'


        def clear_constructor():
            st.session_state.constructor.clear()

        
        custom_param('Текущий сценарий', st.session_state.scenario_name)
        action_options = ['Изменить', 'Закрыть', 'Новый тариф']
        
        if st.session_state.action_record:
            record = st.session_state.action_record
            tariff = record.get('TARIFF')
            custom_param('Тариф', tariff)
            action = record.get('ACTION')
            action_index = action_options.index(action)
            custom_param('Тип активности', action)
        else:
            tariff_index = 0
            tariff_slot = st.empty()
            tele2_tariffs = st.session_state.tele2_tariffs
            if '<Свой вариант>' not in tele2_tariffs: tele2_tariffs.append('<Свой вариант>')
            tariff = tariff_slot.selectbox('Выберите тариф', options=tele2_tariffs, index=tariff_index)
            if tariff == '<Свой вариант>':
                with tariff_slot:
                    custom_param('Тариф', '<Свой вариант>')
                tariff = st.text_input(label='Введите свое название', key='Название тарифа',
                    help='''Будьте внимательны при вводе названия: это название будет использоваться при настройке тарифа.
                    Учтите, что введенное название будет капитализировано по умолчанию.
                ''')
                tariff = tariff.capitalize()
            
            action_index = 0
            action = st.radio('Выберите тип активности', index=action_index, options=action_options, on_change=clear_constructor,
                help='''Выберите "Изменить" для корректировки текущей версии тарифа без изменения АП и основных пакетов.
                Выберите "Новый тариф" при перезапуске портфеля для изменении основных ценовых параметров и пакетов.
                При исключении тарифа из линейки выберите "Закрыть".
                '''
            )

        if tariff in st.session_state.tele2_tariffs:
            record = st.session_state.region_market[st.session_state.region_market["TARIFF"] == tariff].to_dict('records')[0]
        else:
            record = dict()
        st.session_state.constructor['ACTION'] = action
        st.session_state.constructor['TARIFF'] = tariff
        if action == 'Закрыть':
            for param in CONSTRUCTOR_PARAMS:
                value = record.get(param)
                st.session_state.constructor[param] = value
        elif action == 'Изменить':
            # TOOLTIP_DICT
            for param in CONSTRUCTOR_PARAMS:
                value = record.get(param)
                if param == 'FEE_TYPE':
                    st.session_state.constructor[param] = value
                    custom_param(TOOLTIP_DICT[param], value)
                    # options = list(st.session_state.region_market[param].unique())
                    # st.session_state.constructor[param] = st.radio(label=TOOLTIP_DICT[param], key=param, options=options, index=(options.index(value) if value else 0))
                elif param == 'IS_SHELF':
                    st.session_state.constructor[param] = int(st.checkbox(label=TOOLTIP_DICT[param], key=param, value=(value if value else 0)))
                elif param == 'IS_CONVERGENT':
                    st.session_state.constructor[param] = int(st.checkbox(label=TOOLTIP_DICT[param], key=param, value=(value if value else 0)))
                elif param == 'FEE':
                    st.session_state.constructor[param] = value
                    custom_param(TOOLTIP_DICT[param], value)
                    # st.session_state.constructor[param] = st.number_input(label=TOOLTIP_DICT[param], key=param, min_value=0, max_value=10000,
                    # value=(int(value) if value else 0), step=10)
                elif param == 'IS_FEE_DISCOUNT':
                    st.session_state.constructor[param] = int(st.checkbox(label=TOOLTIP_DICT[param], key=param, value=(value if value else 0)))
                elif param == 'FEE_AFTER_DISCOUNT':
                    if st.session_state.constructor.get('IS_FEE_DISCOUNT'):
                        st.session_state.constructor[param] = st.number_input(label=TOOLTIP_DICT[param], key=param,
                                max_value=int(st.session_state.constructor.get('FEE')), step=10, 
                                value=(int(value) if value else 0)
                        )
                    else:
                        st.session_state.constructor[param] = 0
                elif param == 'DATA_GB':
                    st.session_state.constructor[param] = value                
                    custom_param(TOOLTIP_DICT[param], value)
                elif param == 'EXTRA':
                    extras_options = st.session_state.extras[:-1]
                    st.session_state.constructor[param] = st.selectbox('Доп пакеты и удвоения', 
                        options=extras_options, key=param, format_func=(lambda x: 'Нет' if not x else x), index=0
                    )
                elif param  == 'VOICE_MIN':
                    st.session_state.constructor[param] = value
                    custom_param(TOOLTIP_DICT[param], value)
                    # if value and value not in voice_min_options: voice_min_options.append(value)
                    # st.session_state.constructor[param] = st.selectbox(label=TOOLTIP_DICT[param], key=param, options=voice_min_options, 
                            # index=(voice_min_options.index(value) if value else 0))
                elif param == 'USAGE':
                    # options = sorted(list(st.session_state.region_market[param].unique()))
                    # st.session_state.constructor[param] = st.text_area(label=TOOLTIP_DICT[param], key=param, value=(value if value else ''))
                    st.session_state.constructor[param] = value
                    custom_param(TOOLTIP_DICT[param], value)
                elif param == 'INTERNET_EXTRA':
                    # st.session_state.constructor[param] = st.text_area(label=TOOLTIP_DICT[param], key=param, value=(value if value else ''))
                    st.session_state.constructor[param] = value
                    custom_param(TOOLTIP_DICT[param], value)
        elif action == 'Новый тариф':
            for param in CONSTRUCTOR_PARAMS:
                value = record.get(param)
                if param == 'IS_SHELF':
                    st.session_state.constructor[param] = int(st.checkbox(label=TOOLTIP_DICT[param], key=param, value=(value if value else 0)))
                elif param == 'IS_CONVERGENT':
                    st.session_state.constructor[param] = int(st.checkbox(label=TOOLTIP_DICT[param], key=param, value=(value if value else 0)))
                elif param == 'FEE_TYPE':
                    options = list(st.session_state.region_market[param].unique())
                    st.session_state.constructor[param] = st.radio(label=TOOLTIP_DICT[param], key=param, options=options, index=(options.index(value) if value else 0))
                elif param == 'FEE':
                    st.session_state.constructor[param] = st.number_input(label=TOOLTIP_DICT[param], key=param,
                        min_value=0, max_value=10000, value=(int(value) if value else 0), step=10
                    )
                elif param == 'IS_FEE_DISCOUNT':
                    st.session_state.constructor[param] = int(st.checkbox(label=TOOLTIP_DICT[param], key=param, value=(value if value else 0)))
                elif param == 'FEE_AFTER_DISCOUNT':
                    if st.session_state.constructor.get('IS_FEE_DISCOUNT'):
                        st.session_state.constructor[param] = st.number_input(label=TOOLTIP_DICT[param], key=param,
                                max_value=int(st.session_state.constructor['FEE']), step=10, 
                                value=(int(value) if value else 0)
                        )
                    else:
                        st.session_state.constructor[param] = 0
                elif param == 'DATA_GB':
                    data_gb_options.append(999)
                    if value and value not in data_gb_options: data_gb_options.append(value)
                    st.session_state.constructor[param] = st.selectbox(label=TOOLTIP_DICT[param], key=param, options=data_gb_options,
                            index=(data_gb_options.index(value) if value else 0), help='для Безлимита проставлять 999')
                elif param == 'EXTRA':
                    extras_options = st.session_state.extras[:-1]
                    st.session_state.constructor[param] = st.selectbox('Доп пакеты и удвоения', 
                        options=extras_options, key=param, format_func=(lambda x: 'Нет' if not x else x), index=0
                    )
                elif param  == 'VOICE_MIN':
                    if value and value not in voice_min_options: voice_min_options.append(value)
                    st.session_state.constructor[param] = st.selectbox(label=TOOLTIP_DICT[param], key=param, options=voice_min_options, 
                            index=(voice_min_options.index(value) if value else 0))
                elif param == 'USAGE':
                    usage_options = ['', 'All Rus', 'OSS Rus', 'OSS Reg', 'OSS mob Reg', 'All Reg + On-net Rus', 'OSS Reg + On-net Rus']
                    st.session_state.constructor[param] = st.selectbox(label=TOOLTIP_DICT[param], key=param, options=usage_options)
                    # options = sorted(list(st.session_state.region_market[param].unique()))
                    # st.session_state.constructor[param] = st.text_area(label=TOOLTIP_DICT[param], key=param, value=(value if value else ''))
                elif param == 'INTERNET_EXTRA':
                    int_extra_options = ['', '+c/c, месс.', '+c/c, месс., YouTube']
                    st.session_state.constructor[param] = st.selectbox(label=TOOLTIP_DICT[param], key=param, options=int_extra_options)
                    # st.session_state.constructor[param] = st.text_area(label=TOOLTIP_DICT[param], key=param, value=(value if value else ''))
        st.session_state.constructor['SCENARIO_ID'] = st.session_state.scenario_id
        st.session_state.constructor['USERNAME'] = st.session_state.USERNAME
        if action != 'Нет':
            cols = st.columns(2)
            slot = st.empty()
            cols[0].button('Применить', on_click=check_action, args=(action, record, slot))
            cols[1].button('Отмена', on_click=cancel_action)
        else:
            st.button('Отмена', on_click=cancel_action)
        
        
            
    elif st.session_state.sidebar_id == 'Копирование бранча':
        set_up_copy_branch()

    #   ИНАЧЕ РИСУЕМ КЛАСТЕР, БРАНЧ
    else:

        def show_status_notes(rights):
            # st.markdown('&nbsp;')
            # st.markdown(' --- ')
            if rights == 'extended':
                captions_block('✍️ Взято в работу', '✉️ На согласовании', '🕐 На доработке', '🔧 В настройке')   
            elif rights == 'standard':
                captions_block('✍️ Взято в работу', '⛔️ Возвращено на доработку', '🕐 На согласовании', '🔧 Согласовано (в настройке)')
            elif rights == 'test':
                captions_block('✍️ Взято в работу', '🔧 В настройке') 


        def get_marked(option, statuses, rights):
            if statuses.get(option) == 'sent':
                if rights.get('IS_OWNER'):
                    return f'{option} ✉️'
                elif rights.get('IS_INITIATOR'):
                    return f'{option} 🕐'
                else:
                    return option
            elif statuses.get(option) == 'rejected':
                if rights.get('IS_OWNER'):
                    return f'{option} 🕐'
                elif rights.get('IS_INITIATOR'):
                    return f'{option} ⛔️'
                else:
                    return option
            elif statuses.get(option) == 'editing':
                return f'{option} ✍️'
            elif statuses.get(option) == 'setup':
                return f'{option} 🔧'
            else:
                return option


        def update_main_page(what):
            st.session_state.main_page_id = what
        

        if 'LAUNCH_NAME' in st.session_state:
            if st.session_state.LAUNCH_NAME in st.session_state.launches:
                launch_index = st.session_state.launches.index(st.session_state.LAUNCH_NAME)
            else:
                launch_index = 0
        else:
            launch_index = 0
        if st.session_state.main_page_id != 'Рынок':
                # launches = sqlite.get_available_launches(conn, st.session_state.BRANCH_NAME, st.session_state.launch_type)
            st.selectbox('Проект', options=st.session_state.launches, index=launch_index, key='SEL_LAUNCH_NAME', on_change=update_launch_name)
            if st.session_state.LAUNCH_NAME != st.session_state.SEL_LAUNCH_NAME:
                st.session_state.LAUNCH_NAME = st.session_state.SEL_LAUNCH_NAME
            if st.session_state.user_rights.get('IS_OWNER'):
                cols = st.columns(5)
                new_launch_btn = cols[0].button('➕', help='Новый проект')
                new_launch_slot = st.empty()
                if new_launch_btn:
                    def init_add_launch():
                        sqlite.add_launch(conn, st.session_state.new_launch_name, st.session_state.launch_type)
                        st.session_state.LAUNCH_NAME = sqlite.get_last_launch(conn, st.session_state.launch_type)
                    new_launch_slot.text_input('Введите название для проекта', key='new_launch_name', on_change=init_add_launch)
                    st.button('Отмена')
                if st.session_state.LAUNCH_NAME:
                    rename_launch_btn = cols[1].button('✏️', help='Переименовать')
                    if rename_launch_btn:
                        st.markdown(' --- ')
                        def init_rename_launch():
                            sqlite.rename_launch(conn, st.session_state.LAUNCH_NAME, st.session_state.new_launch_name)
                            st.session_state.LAUNCH_NAME = sqlite.get_last_launch(conn, st.session_state.launch_type)
                        st.text_input('Введите название для проекта', key='new_launch_name', on_change=init_rename_launch)
                        st.button('Отмена')
                        st.markdown(' --- ')
                    
                    delete_launch_btn = cols[2].button('❌', help='Удалить')
                    if delete_launch_btn:
                        st.markdown(' --- ')
                        st.info('Внимание, вы пытаетесь удалить текущий проект. Вы уверены?')
                        are_you_sure = st.columns(2)
                        def init_delete_launch():
                            sqlite.delete_launch(conn, st.session_state.LAUNCH_NAME)
                            st.session_state.LAUNCH_NAME = sqlite.get_last_launch(conn, st.session_state.launch_type)
                        are_you_sure[0].button('Удалить', on_click=init_delete_launch)
                        are_you_sure[1].button('Отмена')
                        st.markdown(' --- ')
                    
                    download_statuses_btn = cols[3].button('🧐', help='Выгрузить текущие статусы') 
                    if download_statuses_btn:
                        statuses_list = sqlite.get_statuses_df(conn, st.session_state.LAUNCH_NAME)
                        statuses_df = pd.DataFrame(statuses_list, columns=['PRODUCT_CLUSTER_NAME','BRANCH_NAME','STATUS'])
                        st.sidebar.markdown(get_table_download_link(statuses_df, f'Статусы', drop_index=True), unsafe_allow_html=True)
            
        st.session_state.cluster_statuses = sqlite.get_cluster_statuses(
            conn, st.session_state.user_clusters, st.session_state.LAUNCH_NAME
        )


        if 'PRODUCT_CLUSTER_NAME' not in st.session_state:
            st.session_state.PRODUCT_CLUSTER_NAME = st.session_state.user_rights.get('CLUSTER')
        if not st.session_state.user_rights.get('IS_OWNER') and not st.session_state.user_rights.get('IS_APPROVER') \
            and not st.session_state.user_rights.get('IS_TESTER'):
            custom_param('Кластер', st.session_state.PRODUCT_CLUSTER_NAME)
        else: 
            def update_cluster():
                st.session_state.PRODUCT_CLUSTER_NAME = st.session_state.SEL_PRODUCT_CLUSTER_NAME

            st.session_state.user_clusters = ['(All)'] + CLUSTERS
            clusters = sorted(st.session_state.user_clusters)
            st.selectbox('Кластер', 
                options=clusters,
                format_func=lambda x: get_marked(x, st.session_state.cluster_statuses, st.session_state.user_rights),
                on_change=update_cluster,
                key='SEL_PRODUCT_CLUSTER_NAME'
            )
        


        
        if st.session_state.user_rights.get('IS_OWNER') and st.session_state.main_page_id != 'Рынок':
            cols = st.columns(5)
            get_settings_btn = cols[0].button('📤', help='Выгрузить настройки кластера')
            if get_settings_btn:
                columns_dict = get_columns_dict()
                df = get_pce_df(st.session_state.LAUNCH_NAME)
                df = get_pce_df(st.session_state.LAUNCH_NAME, st.session_state.PRODUCT_CLUSTER_NAME)
                if not df.empty:
                    df.rename(columns_dict, axis=1, inplace=True)
                    df = df.loc[:,~df.columns.duplicated()]
                    st.markdown(get_table_download_link(
                        df, f'Настройки {st.session_state.PRODUCT_CLUSTER_NAME}', drop_index=True), 
                        unsafe_allow_html=True)
                else:
                    st.info('Нет актуальных настроек для текущего проекта')
            if not st.session_state.user_rights.get('IS_INITIATOR') and st.session_state.user_rights.get('IS_OWNER'):
                reject_cluster_btn = cols[1].button(' 👩🏼‍🏫', help='Вернуть кластер на доработку')
                reject_cluster_slot = st.empty()
                if reject_cluster_btn:
                    with reject_cluster_slot.expander('Вернуть кластер на доработку 👩🏼‍🏫', expanded=True):
                        reject_what = st.session_state.PRODUCT_CLUSTER_NAME.replace('(All)','все кластеры')
                        st.write(f'Вы уверены, что хотите вернуть {reject_what} на доработку?')
                        cols = st.columns(2)
                        def reject_cluster():
                            for branch in st.session_state.branches:
                                if st.session_state.branch_statuses.get(branch) == 'sent':
                                    st.session_state.BRANCH_NAME = branch
                                    sqlite.add_branch_status(conn, st.session_state, status='rejected')
                            # st.experimental_rerun()
                        cols[0].button('Вернуть', on_click=reject_cluster)
                        cols[1].button('Отмена')


        st.session_state.branch_statuses = sqlite.get_branch_statuses(conn, st.session_state.LAUNCH_NAME)
        # print(st.session_state.branch_statuses)
        if st.session_state.PRODUCT_CLUSTER_NAME == '(All)':
            st.session_state.branches = sqlite.get_branches(conn, CLUSTERS)
            st.session_state.cluster_status = None
        else:
            st.session_state.branches = sqlite.get_branches(conn, st.session_state.PRODUCT_CLUSTER_NAME)
            st.session_state.cluster_status = st.session_state.cluster_statuses[st.session_state.PRODUCT_CLUSTER_NAME]
        

        def update_branch():
            st.session_state.BRANCH_NAME = st.session_state.SEL_BRANCH_NAME
            st.session_state.REGION_NAME = branch_to_region(st.session_state.BRANCH_NAME)

        if 'BRANCH_NAME' in st.session_state:
            if st.session_state.BRANCH_NAME in st.session_state.branches:
                branch_index = st.session_state.branches.index(st.session_state.BRANCH_NAME)
            else:
                branch_index = 0
        else:
            branch_index = 0
        st.selectbox('Бранч',
                options=st.session_state.branches, 
                index=branch_index,
                format_func=lambda x: get_marked(x, st.session_state.branch_statuses, st.session_state.user_rights),
                on_change=update_branch,
                key='SEL_BRANCH_NAME')
        if st.session_state.BRANCH_NAME != st.session_state.SEL_BRANCH_NAME:
            update_branch()
            

        show_status_notes(st.session_state.user_rights)
        st.session_state.branch_status = st.session_state.branch_statuses.get(st.session_state.BRANCH_NAME)
        if st.session_state.branch_status not in ('sent', 'setup') or st.session_state.user_rights.get('IS_OWNER'):
            st.session_state.is_editing_allowed = True
        else:
            st.session_state.is_editing_allowed = False
        st.session_state.actual_tariffs = sqlite.get_tariffs_by_branch(conn, st.session_state.BRANCH_NAME, st.session_state.LAUNCH_NAME)

        def show_scenarios():
            df = st.session_state.region_market
            st.session_state.tele2_tariffs = sorted(list(df[df['OPERATOR'] == 'Tele2']['TARIFF'].unique()))
            st.session_state.sidebar_id = 'Список сценариев'
            if 'region_scenario' in st.session_state:
                del st.session_state.region_scenario

        if st.session_state.main_page_id == 'Рынок':
            st.button('👨‍🔧 Конструктор', on_click=show_scenarios)

        elif st.session_state.main_page_id == 'Запуск':
            
            def init_copy_branch():
                st.session_state.sidebar_id = 'Копирование бранча'

            def init_clear_branch():
                st.session_state.sidebar_id = 'Очистка бранча'

            if st.session_state.user_rights.get('IS_INITIATOR') and st.session_state.is_editing_allowed:
                st.button('Копировать из...', help="Копировать матрицу из...", on_click=init_copy_branch)
                st.button('Очистить матрицу', help="Очистить матрицу для бранча", on_click=init_clear_branch)


def set_up(conn):

    if 'is_matrice_reloading_allowed' not in st.session_state:
        st.session_state.is_matrice_reloading_allowed = True
    if 'is_tariff_copying' not in st.session_state:
        st.session_state.is_tariff_copying = False 
    if 'extras' not in st.session_state:
        st.session_state.extras = ['Нет', '5 GB', '10 GB', '15 GB', 'Удвоение', '<Свой вариант>']  

    st.session_state.launches = sqlite.get_launches(conn, st.session_state.launch_type)
    if 'LAUNCH_NAME' not in st.session_state: st.session_state.LAUNCH_NAME = st.session_state.launches[0]

    menu_dict = {
        'Рынок':'grid', 
        'Запуск':'gear', 
        'Чек-лист':'clipboard-check', 
        'Комментарии':'chat'
    }
    if st.session_state.user_rights.get('IS_OWNER'): menu_dict['Справочники'] = 'book'
    # if st.session_state.USERNAME == 'igor.i.plotnikov':
        # menu_dict.update({'Рынок NEW': 'erfc'})
    st.session_state.main_page_id = option_menu(None, 
            options=[k for k in menu_dict.keys()],
            icons=[v for v in menu_dict.values()],
            menu_icon="app-indicator", default_index=0, orientation='horizontal',
            styles={
                "container": {"background-color": "transparent"},
            #     "icon": {"color": "orange", "font-size": "25px"}, 
            #     "nav-link": {"font-size": "16px", "text-align": "left", "margin":"0px", "--hover-color": "#eee"},
            #     "nav-link-selected": {"background-color": "#02ab21"},
            }
        )
    if st.session_state.main_page_id != 'Рынок' and st.session_state.sidebar_id in ['Список сценариев', 'Сценарий', 'Конвертация в запуск']:
        st.session_state.sidebar_id = None
        if 'region_scenario' in st.session_state:
            del st.session_state.region_scenario
    
    with st.sidebar:
        set_up_sidebar(conn)
    set_up_main_page(conn)

    # ПОСМОТРЕТЬ
    # st.session_state.actual_tariffs
    # {k:v for k, v in st.session_state.items() if k.upper() == k}
    # st.session_state.this_launch_records
    # st.session_state.VOICE_MIN_M
    # st.session_state.branch_statuses
    # st.session_state.LAUNCH_NAME
    # st.write({k: v for k, v in st.session_state.items() if k != 'dic' and k != 'password' and 'FormSubmitter' not in k})
    # st.write({k: v for k, v in st.session_state.items() if 'FormSubmitter'  in k})
    # st.session_state.branches
    # st.session_state.branch_statuses
  

def log_in(username, password):
    token = win32security.LogonUser(
        username,
        SERVERNAME,
        password,
        win32security.LOGON32_LOGON_NETWORK,
        win32security.LOGON32_PROVIDER_DEFAULT
    )     
    return bool(token)


def main():

    if 'counter' not in st.session_state:
        st.session_state.counter = 0
    else:
        st.session_state.counter +=1

    _, image_col, _ = st.sidebar.columns([0.5, 1, 0.5])
    image_col.image('Tele2-PLM-logo.png', width=115)
    st.sidebar.markdown('&nbsp;')
    log_in_slot = st.sidebar.empty()

    if 'logged_in' in st.session_state:
        if 'conn' not in st.session_state:
            st.session_state.conn = sqlite.create_connection('DB.sqlite3')
            sqlite.add_auth(st.session_state.conn, st.session_state.USERNAME)
        if 'repr_dic' not in st.session_state:
            st.session_state.repr_dic = sqlite.get_repr_dic(st.session_state.conn)
        if 'user_rights' not in st.session_state:
            st.session_state.user_rights = sqlite.get_rights_by_username(st.session_state.conn, st.session_state.USERNAME)
        st.session_state.launch_type = ('test' if st.session_state.user_rights.get('IS_TESTER') else 'prod')
        if not st.session_state.user_rights:
            st.error("Ошибка: у вас нет прав для работы с чек-листами. Согласуйте доступ с ответственным менеджером")
            st.stop()
        else:
            if 'user_clusters' not in st.session_state:
                st.session_state.user_clusters = []
                cluster = st.session_state.user_rights.get('CLUSTER')
                st.session_state.user_clusters.append(cluster)
            set_up(st.session_state.conn)
            
    else:
        set_png_as_page_bg(os.path.join(curdir, r'wp10.jpg')) 
        with log_in_slot.form(key='log_in'):
            username = st.text_input(f'Username', autocomplete="username")
            password = st.text_input(f'Password', type='password', autocomplete="current-password")
            log_in_btn = st.form_submit_button('Log In')
        if log_in_btn or (username != '' and password != ''):
            try:
                st.session_state.logged_in = log_in(username, password)
            except:
                st.sidebar.error("Ошибка: неверное имя пользователя или пароль. Попробуйте еще")
            else:
                st.session_state.USERNAME = username.lower().replace('@tele2.ru','')
                st.session_state.password = password
                st.experimental_rerun()


if __name__ == '__main__':
    main()
    