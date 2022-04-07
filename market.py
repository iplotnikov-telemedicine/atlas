import pandas as pd
import streamlit as st
import re
# from io import BytesIO
from jinja2 import Template
import numpy as np
# from streamlit.type_util import data_frame_to_bytes


COLORS = {
    'Tele2': {'background-color': '#1f2229', 'color': 'white'},
    'МТС': {'background-color': '#dc0610','color': 'white'},
    'Мегафон': {'background-color': '#01bf56','color': 'black'},
    'билайн': {'background-color': '#fdb82c','color': 'black'},
    'Мотив': {'background-color': '#fa4b08','color': 'white'},
    'Летай': {'background-color': '#e66f1c','color': 'white'},
    'Yota': {'background-color': '#01d1ff', 'color': 'black'}
}



def local_css(css_file):
    with open(css_file) as f:
        st.markdown('<style>{}</style>'.format(f.read()), unsafe_allow_html=True)

# local_css(css_file)


def render_sim(row, tooltip_dict, filled=True):
    for k, v in row.items():
        if k.startswith('IS_'):
            row[k] = ('да' if v else 'нет')
    comment_dic = {tooltip_dict[key]:val for key, val in row.items() if key in tooltip_dict.keys()}
    if comment_dic['Есть скидка на АП'] == 'нет': del comment_dic['АП после скидки']
    tooltip = '&#13;&#10;'.join(f'{key}: {value}' for key, value in comment_dic.items())
    min_value = int(row.get('VOICE_MIN'))
    gb_value = int(row.get('DATA_GB'))
    action = row.get('ACTION')
    if min_value < 400:
        if gb_value < 25:
            tooltip_position = 'right-top' 
        else:
            tooltip_position = 'right-bottom' 
    else:
        if gb_value < 20:
            tooltip_position = 'left-top' 
        else:
            tooltip_position = 'left-bottom' 

    operator = row.get('OPERATOR')
    sim_color = COLORS[operator]['background-color'] if filled else 'transparent'
    text_color = COLORS[operator]['color']

    if action == 'Закрыть':
        action_class = 'closed'
    elif action == 'Новый тариф':
        action_class = 'new'
    else:
        action_class = ''

    border_color = 'black'
    element = 'p' #'button' if operator == 'Tele2' else 
    fee_label = str(row.get('FEE'))
    fee_after_discount = row.get('FEE_AFTER_DISCOUNT')
    if fee_after_discount > 0: fee_label = fee_label + '/' + str(int(fee_after_discount))
    sim = f'''<div class="tooltip" style="border-radius: 0.25rem;">
                <span class="tooltiptext {tooltip_position}">{tooltip}</span>
                <div class="css-181e6i2 edgvbvh1 {action_class}"  id="{row.get('ID')}"
                style="background-color: {sim_color}; border-radius: 0.25rem; 
                border: 0.5px solid {border_color}; height: 100%; width: fit-content;">
                    <{element} align="center" style="font-family: Tele2 DisplayStencil;
                    background-color: transparent; font-size: 14px; padding: 2px 6px; margin: 0;
                    margin-bottom: 1px; vertical-align: top; color: {text_color};">{fee_label}</{element}> 
                </div>
            </div>
    '''
    return sim

@st.experimental_memo(show_spinner=False)  
def render_market(df, tooltip_dict):
    st.session_state.tele2_dics = []
    gb_values, min_values = df['DATA_GB'].astype(int).unique(), df['VOICE_MIN'].astype(int).unique()
    header_cells = list()
    lines = list()
    header_cells.append('')
    for min_value in sorted(min_values):
        header_cells.append(min_value)
    list_of_rows = list()
    for gb_value in sorted(gb_values, reverse=True): #для каждой строки
        row_of_cells = list()
        row_of_cells.append(gb_value)
        for min_value in sorted(min_values): #для каждого столбца
            fee_df = df[(df['VOICE_MIN'] == min_value) & (df['DATA_GB'] == gb_value)]
            one_cell_content = str()
            for _, row in fee_df.sort_values(by='FEE', ascending=False).iterrows(): #для каждой ячейки
                one_cell_content += render_sim(row, tooltip_dict)
                if not pd.isna(row.get('ID_NEW')): lines.append((int(row.get('ID')), int(row.get('ID_NEW'))))
            row_of_cells.append(one_cell_content)
        list_of_rows.append(row_of_cells) 
    with open('market.html') as html:
        template = Template(html.read())
    return template.render(header_cells=header_cells, list_of_rows=list_of_rows, lines=lines)
    
 
def stylize_value(text):
    return st.markdown(f'''<p align="center" style="color: #373839; font-family: Tele2 DisplayStencil;
        font-weight: bold; font-size: 14px; width: 4em; height: 100%; margin-bottom: 0px;">{text}</p>''', unsafe_allow_html=True)


def str_to_int(x):
    if type(x) == int:
        return x
    else:
        y_str = x.split('.')[0]
        y_str = ''.join(filter(str.isdigit, y_str))
        try:
            y = int(y_str)
        except ValueError:
            return 999
        else:
            return y


def where_column_clean(string):
    return ' + '.join(x.strip().title().replace('Дополнительно', 'Доп') for x in string.split('+'))


def internet_extras_clean(string):
    string = string.replace('.', ' ')
    repl_dict = {
        # 'безлимитные': 'unlim',
        # 'безлимит': 'unlim',
        # 'безлимит на': 'unlim',
        # 'безлим': 'unlim',
        # 'unlim': 'unlim',
        # 'unlim': 'unlim',
        # 'мессенджеры': 'месс',
        # 'месс. ': 'месс',
        '`': '',
        '+': '',
    }   
    return ''.join(repl_dict.get(word, word) for word in string.split())


def get_index_tariff(tariff):
    pass


def split_fee(x, group_num):
    sequence = re.search('[z_]*([0-9]*)([\+∞]*)[_А]*\/*([0-9]*)⌂*([\+∞]*)', x)
    fee_str = sequence.group(group_num)
    return int(fee_str) if fee_str else 0


# @st.experimental_memo(show_spinner=False)          
# def process_df(df):
#     df.fillna('', inplace=True)
#     df = df.astype(str)
#     df['FEE'] = df['FEE_STR'].apply(lambda fee: split_fee(fee, 1))
#     df['IS_FEE_DISCOUNT'] = df['FEE_STR'].apply(lambda fee: (1 if '/' in fee else 0))
#     df['FEE_AFTER_DISCOUNT'] = df.apply(lambda row:
#         split_fee(row['FEE_STR'], 3) if row['IS_FEE_DISCOUNT'] else row['FEE'],
#     axis=1)
#     df['VOICE_MIN'] = df['VOICE_MIN_STR'].apply(lambda x: str_to_int(x))
#     df['DATA_GB'] = df['DATA_GB_STR'].apply(lambda x: str_to_int(x))
#     df['IS_SHELF'] = df['IS_SHELF'].apply(lambda x: str_to_int(x))
#     df['USAGE'] = df['USAGE'].apply(lambda string: where_column_clean(string))
#     df['IS_INDEX_NEEDED'] = df.duplicated(subset=['REGION_NAME','OPERATOR','TARIFF_NAME'], keep=False)
#     df['CONSTRUCTOR_INDEX'] = (df
#         .sort_values(['VOICE_MIN', 'DATA_GB'])
#         .groupby(['REGION_NAME','OPERATOR','TARIFF_NAME'])
#         .cumcount()+1
#     )
#     df['TARIFF'] = np.where(
#         df['IS_INDEX_NEEDED'] == True,
#         df['TARIFF_NAME'] + ' ' + df['CONSTRUCTOR_INDEX'].astype(str),
#         df['TARIFF_NAME']
#     )
#     df['ACTION'] = None
    # (df[(df['Регион'] == 'Москва') & (df['Оператор'] == 'Tele2')]
    #     [['Название тарифа', 'Пакет data', 'Пакет минут', 'Индекс для конструктора', 'Тариф']]
    #     .sort_values(by=['Название тарифа', 'Индекс для конструктора'])
    # )
    # df['Интернет, дополнительно'] = df['Интернет, дополнительно'].apply(lambda string: internet_extras_clean(string))
    # return df
    

# def fill_constructor(comment_dic, id):
#     st.session_state.constructor = {key: value for key, value in comment_dic.items() if key in st.session_state.constructor_columns}
#     st.session_state.constructor['id'] = id


# def cancel_construct():
#     st.session_state.constructor.clear()


# def show_market(df, columns, region):
#     df = df[(df['Регион'] == region)]
#     if df.empty:
#         st.markdown('''<p style="text-align: center; font-family: Source Sans Pro; color: #373839">
#             Бранч не найден 😟</p>''', unsafe_allow_html=True)
#     gb_values, min_values = df['Пакет data'].unique(), df['Пакет минут'].unique()
#     cols_count = len(min_values)
#     cols = st.columns(cols_count + 1)
#     for col_num, min_value in enumerate(sorted(min_values), start=1):
#         with cols[col_num]:
#             stylize_value(str(min_value))
#     for gb_value in sorted(gb_values, reverse=True):
#         st.markdown('---')
#         cols = st.columns(cols_count + 1)
#         with cols[0]:
#             stylize_value(str(gb_value))
#         # cols[0].write(str(gb_value))
#         for col_num, min_value in enumerate(sorted(min_values), start=1):
#             fee_df = df[(df['Пакет минут'] == min_value) & (df['Пакет data'] == gb_value)]
#             for id, row in fee_df[columns].iterrows():
#                 fee = str(row['Абонплата']).replace(' ','')
#                 operator = row['Оператор']
#                 tariff = row['Название тарифа']
#                 comment_dic = {column : str(value).replace('+ ', '+') for column, value in row.items() if column != 'id'}
#                 with cols[col_num]:
#                     draw_micro_sim(id, fee, operator, comment_dic) 
#                     if operator == 'Tele2':
#                         with st.form(key=f'{id}'):
#                             if tariff == st.session_state.constructor.get(tariff):
#                                 st.form_submit_button('', on_click=cancel_construct)
#                             else:
#                                 st.form_submit_button('', on_click=fill_constructor, args=(comment_dic, id))


    # st.download_button('Download file', convert_to_excel(df), mime='text/csv')

# for row in grouped_df['Пакет data'].unique().sort_values(ascending=True):
    # for col in grouped_df['Пакет data'].unique().sort_values(ascending=False):



# for i, column in enumerate(['Регион','Дата добавления данных']):
#     cols[i].selectbox(column, sorted(df[column].unique()), index=0, key=column)
# st.write('')



