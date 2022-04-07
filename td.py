from teradatasql import connect, OperationalError, DatabaseError
import streamlit as st
import pandas as pd
import altair as alt
# import numpy as np
# from market import COLORS
from datetime import date

pd.set_option('mode.chained_assignment', None)


alt.renderers.set_embed_options(
    padding={"left": 20, "right": 20, "bottom": 20, "top": 20}
)


CONN_INFO = {
    "host": "td2800.corp.tele2.ru",
    "logmech": "TD2",
    'user': 'USER_FROM_PLM',
    'password': 'USER_FROM_PLM',
}

CURRENT_DATE = date.today()
CURRENT_WEEK_NUMBER = CURRENT_DATE.isocalendar()[1]



@st.experimental_singleton(show_spinner=False)
def get_db_connection(current_week_number):
    session = connect(**CONN_INFO)
    return session



@st.experimental_memo(show_spinner=False)
def get_all_sales(_session, CURRENT_DATE):
    query = '''
        SELECT
            report_month,
            region_name,
            name_report,
            sum(gross_count)
        FROM UAT_PRODUCT.GD_SALES_PRODUCT_NEW
        WHERE report_month >= add_months(CURRENT_DATE, -13)
        GROUP BY 1, 2, 3
        '''
    result = pd.read_sql(query, _session)
    return result


# @st.experimental_memo(show_spinner=True)
# def get_migrations(_session, region_name):
#     query = '''
#         SELECT
#             report_month,
#             region_name,
#             name_report,
#             sum(subs_count)
#         FROM UAT_PRODUCT.GD_MONTHLY_MIGRATIONS
#         WHERE CBM = 0
#             AND region_name = ?
#             AND report_month >= add_months(current_week_number, -13)
#         GROUP BY 1, 2, 3
#         '''
#     result = pd.read_sql(query, _session, params=(region_name, ))
#     # df = pd.read_sql_query(query, _session, params={'region_name':region_name})
#     return result


@st.experimental_memo(show_spinner=False)
def get_all_migrations(_session, CURRENT_DATE):
    query = '''
        SELECT
            report_month,
            region_name,
            name_report,
            sum(subs_count)
        FROM UAT_PRODUCT.GD_MONTHLY_MIGRATIONS
        WHERE CBM = 0
            AND report_month >= add_months(CURRENT_DATE, -13)
        GROUP BY 1, 2, 3
        '''
    result = pd.read_sql(query, _session)
    return result


@st.experimental_memo(show_spinner=False)
def get_all_shares(_session, current_week_number):
    query = '''
        SELECT
        case oper when 'Билайн' then 'билайн' else oper end as oper,
        reg_t2,
        ROUND(CAST("cnt" AS FLOAT) / CAST(sum("cnt") over (partition by reg_t2) AS FLOAT),3) AS "share"
    FROM uat_product.dv_ms_bdo
    WHERE report_date = (
            select max(report_date)
            from uat_product.dv_ms_bdo
        ) AND TYPE_ORIG = 'MS in Voice users'
    '''
    result = pd.read_sql(query, _session)
    return result



def draw_stacked_charts(dict, height):
    charts = []
    tariffs = ['Новогодний', 'Везде онлайн+', 'Везде онлайн', 'Безлимит', 'Мой онлайн+', 'Мой онлайн',
                        'Мой разговор', 'Мой Tele2', 'Классический', 'Other']
    for title, df in dict.items():
        # df._is_copy = None
        df['Абонентов за месяц'] = df.groupby('Месяц')['Абонентов'].transform('sum')
        df['Доля'] = df['Абонентов'] / df['Абонентов за месяц']
        df['label'] = df['Доля'].apply(lambda x: f'{x:.0%}' if x >=0.1 else '')
        df['order'] = df['Тариф'].replace({val: i for i, val in enumerate(reversed(tariffs))})
        max_domain = df['Абонентов за месяц'].max() * 1.2
        bars = alt.Chart(df, title=title, height=height).mark_bar(
            # cornerRadiusTopLeft=2, cornerRadiusTopRight=2
        ).encode(
            x=alt.X('yearmonth(Месяц):O', axis=alt.Axis(tickSize=0, title='', format=("%b %y"))), 
            y=alt.Y('Абонентов', title='', axis=None, stack='zero', scale=alt.Scale(domain=[0, max_domain]), sort='x'),
            tooltip=['Месяц', 'Регион', 'Тариф', 'Абонентов', alt.Tooltip('Доля:Q', format='.1%')],
            # color='NAME_REPORT'
            color=alt.Color('Тариф',
                scale=alt.Scale(
                domain=tariffs,
                range=['#9c755f', '#512375', '#7030a0', '#fa0000', '#17375e',
                        '#558ed5', '#8eb4e3', '#c6d9f1', '#ffc000', '#bfbfbf'],
                ), sort=alt.EncodingSortField(field="order")   
            ),
            order='order'
        ).properties(width=370, height=height)

        text = alt.Chart(df, title='', height=height).mark_text(
            color='white',
            baseline='top',
            dy=3
        ).encode(
            x=alt.X('yearmonth(Месяц):O', title=''), 
            y=alt.Y('Абонентов', title='', axis=None, stack='zero'),
            detail='Тариф:N',
            text='label',
            # text=alt.Text('label', format='.0%'),
            order='order'
        )

        top_text = alt.Chart(df, title='', height=height).mark_text(
            color='white',
            baseline='bottom',
            dy=-3
        ).encode(
            x=alt.X('yearmonth(Месяц):O', title=''), 
            y=alt.Y('sum(Абонентов):Q', title='', axis=None),
            text=alt.Text('sum(Абонентов):Q', format='.3s')
            # text=alt.Text('label', format='.0%'),
        )
# alt.hconcat(
#     left, right
# ).configure_view(strokeOpacity=0).configure_axis(
#     # remove axis line
#     grid=False, domain=False,ticks=False
# )
        
        charts.append(bars + text + top_text)
        
    canvas = alt.hconcat(*charts).configure_view(strokeOpacity=0)
    st.altair_chart(canvas, use_container_width=True)


# def draw_horizontal_stacked(df, title, height):
#     df['Абонентов за месяц'] = df.groupby('Месяц')['Абонентов'].transform('sum')
#     df['Доля'] = df['Абонентов'] / df['Абонентов за месяц']
#     bars = alt.Chart(df, title=title, height=height).mark_bar(
#         cornerRadiusTopLeft=2, cornerRadiusTopRight=2, size=22
#     ).encode(
#         x=alt.X('Абонентов', title='', axis=alt.Axis(grid=False)),
#         y=alt.Y('month(Месяц):O', title=''), 
#         tooltip=['Месяц', 'Регион', 'Оператор', 'Абонентов', alt.Tooltip('Доля:Q', format='.1%')],
#         # color='NAME_REPORT'
#         color=alt.Color('Оператор',
#             scale=alt.Scale(
#                 domain=list(COLORS.keys()),
#                 range=[COLORS[operator]['background-color'] for operator in COLORS.keys()]
#             ),
#         )
#     )
#     st.altair_chart(bars, use_container_width=True)



def show_charts(session, region_name, height): 
    # sales = get_sales(session, region_name)
    all_sales = get_all_sales(session, CURRENT_WEEK_NUMBER)
    all_sales.columns = ['Месяц', 'Регион', 'Тариф', 'Абонентов']
    sales = all_sales[all_sales['Регион'] == region_name]
    # migrations = get_migrations(session, region_name)
    all_migrations = get_all_migrations(session, CURRENT_WEEK_NUMBER)
    all_migrations.columns = ['Месяц', 'Регион', 'Тариф', 'Абонентов']
    migrations = all_migrations[all_migrations['Регион'] == region_name]
    most_recent_date = migrations['Месяц'].max()
    migrations['Абонентов'].mask(migrations['Месяц'] == most_recent_date, 0, inplace=True)
    draw_stacked_charts({'SALES MIX':sales, 'MIGRATIONS MIX (без CBM)':migrations}, height)



def get_shares(session, region_name):
    all_shares = get_all_shares(session, CURRENT_WEEK_NUMBER)
    all_shares.columns = ['Оператор', 'Регион', 'Абонентов']    
    shares = all_shares[all_shares['Регион'] == region_name]
    shares_dict = dict(zip(shares['Оператор'], shares['Абонентов']))
    return shares_dict
