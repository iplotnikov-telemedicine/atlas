import sqlite3
from datetime import datetime
import streamlit as st
import pandas as pd


@st.experimental_singleton
def create_connection(db_file):
    _conn = None
    try:
        _conn = sqlite3.Connection(db_file, check_same_thread=False)
    except sqlite3.Error as e:
        print(e)
    return _conn


@st.experimental_singleton
def create_test_connection(db_file):
    _conn = None
    try:
        _conn = sqlite3.Connection(db_file, check_same_thread=False)
    except sqlite3.Error as e:
        print(e)
    return _conn


def get_last_launch(_conn, launch_type):
    cursor = _conn.cursor()
    sql = '''
        SELECT LAUNCH_NAME 
        FROM LAUNCHES 
        WHERE LAUNCH_TYPE = ?
        ORDER BY DATE_TIME DESC 
        LIMIT 1
    '''
    cursor.execute(sql, (launch_type, ))
    result = cursor.fetchone()
    cursor.close()
    return (result[0] if result else None)


def get_launches(_conn, launch_type):
    cursor = _conn.cursor()
    sql = '''
        SELECT LAUNCH_NAME 
        FROM LAUNCHES 
        WHERE LAUNCH_TYPE=?
        ORDER BY DATE_TIME DESC
    '''
    cursor.execute(sql, (launch_type, ))
    launches = [col[0] for col in cursor.fetchall()]
    cursor.close()
    return launches


def get_available_launches(_conn, branch, launch_type):
    cursor = _conn.cursor()
    sql = '''
        WITH A AS (
            SELECT MAX(LAST_BRANCH_STATUSES.DATE_TIME) AS LAST_SETUP_DATE_TIME
            FROM LAST_BRANCH_STATUSES
            JOIN LAUNCHES USING (LAUNCH_NAME)
            WHERE STATUS in ('setup', 'sent')
                AND BRANCH_NAME = ? AND LAUNCH_TYPE = ?
        )

        SELECT
            LAUNCH_NAME
        FROM LAUNCHES
        WHERE DATE_TIME > (SELECT LAST_SETUP_DATE_TIME FROM A)
        ORDER BY DATE_TIME DESC
    '''
    cursor.execute(sql, (branch, launch_type))
    launches = [col[0] for col in cursor.fetchall()]
    cursor.close()
    return launches


def get_rights_by_username(_conn, username):
    cursor = _conn.cursor()
    sql = "SELECT * FROM USERS WHERE LOWER(USERNAME)=?"
    cursor.execute(sql, (username, ))
    columns = [column[0] for column in cursor.description]
    result = cursor.fetchone()
    cursor.close()
    if result:
        return dict(zip(columns, result))
    return dict.fromkeys(columns)


def get_repr_name(_conn, col_name):
    cursor = _conn.cursor()
    sql = "SELECT REPR_NAME FROM COLUMNS WHERE COLUMN_NAME=?"
    cursor.execute(sql, [(col_name)])
    result = cursor.fetchone()
    if type(result) == tuple:
        result, *_ = result
    cursor.close()
    return (result if result else col_name)


def get_repr_dic(_conn):
    cursor = _conn.cursor()
    sql = "SELECT COLUMN_NAME, COALESCE(REPR_NAME, COLUMN_NAME) FROM COLUMNS"
    cursor.execute(sql)
    result = {col[0]:col[1] for col in cursor.fetchall()}
    cursor.close()
    return result



def get_product_changes(_conn, table_name, cluster, launch_name):
    cursor = _conn.cursor()
    sql = f'''
        SELECT * FROM {table_name}
        WHERE PRODUCT_CLUSTER_NAME = ?
            AND LAUNCH_NAME = ?;
        '''
    cursor.execute(sql, (cluster, launch_name))
    result = []
    columns = [column[0] for column in cursor.description]
    for row in cursor.fetchall():
        result.append(dict(zip(columns, row)))
    cursor.close()
    return result


def get_records_by_branch(_conn, launch_name, launch_type, branch):
    cursor = _conn.cursor()
    sql = f'''       
        
WITH LAUNCH_HISTORY AS (
            SELECT LAUNCH_NAME, LAUNCH_TYPE,
                LEAD(DATE_TIME, 1, '2099-12-31 23:59:59') OVER (ORDER BY DATE_TIME) as END_DATE_TIME
            FROM LAUNCHES
            WHERE launch_type = ?),

RANKED_CHANGES AS (
            SELECT
            	LAUNCH_HISTORY.*,
                CHANGES.*,
                row_number() over (partition by CHANGES.TARIFF
                    order by LAUNCH_HISTORY.END_DATE_TIME DESC) as IS_ACTUAL
            FROM CHANGES
            INNER JOIN LAUNCH_HISTORY USING (LAUNCH_NAME)
            WHERE BRANCH_NAME = ?
            	AND LAUNCH_HISTORY.END_DATE_TIME <= (
            		SELECT END_DATE_TIME
            		FROM LAUNCH_HISTORY
            		WHERE LAUNCH_NAME = ? 
            	)
          )
          
          SELECT
            COALESCE(TARIFF_ALIASES.TARIFF_ALIAS, RANKED_CHANGES.TARIFF) as TARIFF_NAME,
          	RANKED_CHANGES.*
          FROM RANKED_CHANGES
          LEFT JOIN TARIFF_ALIASES USING (TARIFF, LAUNCH_NAME)
          WHERE IS_ACTUAL = 1
--      
        '''
    cursor.execute(sql, (launch_type, branch, launch_name))
    result = []
    columns = [column[0] for column in cursor.description]
    for row in cursor.fetchall():
        result.append(dict(zip(columns, row)))
    cursor.close()
    return result


def get_ready_clusters(_conn, launch_name):
    cursor = _conn.cursor()
    sql = '''
    SELECT
        PRODUCT_CLUSTER_NAME
    FROM LAST_CLUSTER_STATUSES 
    WHERE STATUS = 'sent'
        AND LAUNCH_NAME = ?
    '''
    cursor.execute(sql, (launch_name, ))
    clusters = [col[0] for col in cursor.fetchall()]
    cursor.close()
    return clusters


def get_this_launch_records(_conn, table, product_cluster_name, launch_name):
    cursor = _conn.cursor()
    if product_cluster_name == '(All)':
        sql = f'''
            SELECT * FROM {table}
            WHERE LAUNCH_NAME=?
            '''
        cursor.execute(sql, (launch_name, ))
    else:
        sql = f'''
        SELECT * FROM {table}
        WHERE LAUNCH_NAME=?
            AND PRODUCT_CLUSTER_NAME=?
        '''
        cursor.execute(sql, (launch_name, product_cluster_name))
    result = []
    columns = [column[0] for column in cursor.description]
    for row in cursor.fetchall():
        result.append(dict(zip(columns, row)))
    cursor.close()
    return result


def get_tariffs_by_branch(_conn, branch_name, launch_name):
    cursor = _conn.cursor()
    sql = f'''
        SELECT TARIFF FROM CHANGES
        WHERE BRANCH_NAME=?
            AND LAUNCH_NAME=?
        '''
    cursor.execute(sql, (branch_name, launch_name))
    tariffs = [col[0] for col in cursor.fetchall()]
    cursor.close()
    return tariffs


def get_record(_conn, branch, tariff, launch_name):
    cursor = _conn.cursor()
    sql = f'''
            SELECT
                COALESCE(TARIFFS_BY_LAUNCH.TARIFF_ALIAS, CH.TARIFF) as TARIFF_NAME,
        	    CH.*
            FROM CHANGES CH
            LEFT JOIN TARIFFS_BY_LAUNCH USING (TARIFF, LAUNCH_NAME)
            WHERE BRANCH_NAME=?
                AND TARIFF=? 
                AND LAUNCH_NAME=?;
            '''
    cursor.execute(sql, (branch, tariff, launch_name))
    columns = [column[0] for column in cursor.description]
    result = cursor.fetchone()
    cursor.close()
    if result:
        return dict(zip(columns, result))
    return dict.fromkeys(columns)


def get_last_record(_conn, branch, tariff, launch_type):
    cursor = _conn.cursor()
    sql = f'''
            SELECT * 
            FROM PRODUCT_CHANGES
            WHERE BRANCH_NAME = ?
                AND TARIFF = ?
                AND LAUNCH_TYPE = ?
            ORDER BY DATE_TIME DESC LIMIT 1;
            '''
    cursor.execute(sql, (branch, tariff, launch_type))
    columns = [column[0] for column in cursor.description]
    result = cursor.fetchone()
    cursor.close()
    if result:
        return dict(zip(columns, result))
    return dict.fromkeys(columns)


def get_params_by_default(_conn, tariff):
    cursor = _conn.cursor()
    sql = f'''
            SELECT * FROM PARAMS_BY_DEFAULT
            WHERE TARIFF=?;
            '''
    cursor.execute(sql, (tariff,))
    columns = [column[0] for column in cursor.description]
    result = cursor.fetchone()
    cursor.close()
    if result:
        return dict(zip(columns, result))
    return dict.fromkeys(columns)



def get_param_by_default(_conn, tariff, param):
    cursor = _conn.cursor()
    sql = f'''
            SELECT {param} FROM PARAMS_BY_DEFAULT
            WHERE TARIFF=?;
            '''
    cursor.execute(sql, (tariff, ))
    result = cursor.fetchone()
    cursor.close()
    return (result[0] if result else None)



def get_columns(_conn, table):
    cursor = _conn.cursor()
    sql = f'PRAGMA table_info({table});'
    cursor.execute(sql)
    columns = [col[1] for col in cursor.fetchall()]
    cursor.close()
    return columns


def add_record(_conn, session_dict):
    columns = get_columns(_conn, 'CHANGES')
    values = []  
    for col in columns:
        if col == 'DATE_TIME':
            values.append(datetime.now().replace(microsecond=0))
        else:
            values.append(session_dict.get(col, None))
    sql = f'''
    INSERT OR REPLACE INTO CHANGES ({ ','.join(columns)}) 
    VALUES ({ ','.join('?'*len(values))});
    '''
    _conn.execute(sql, values)
    _conn.commit()
    return


def delete_record(_conn, launch_name, branch_name, tariff):
    sql = f'''
    DELETE FROM CHANGES
    WHERE LAUNCH_NAME=?
        AND BRANCH_NAME=?
        AND TARIFF=?
    '''
    _conn.execute(sql, (launch_name, branch_name, tariff))
    _conn.commit()
    return


def clear_branch(_conn, launch_name, branch_name):
    sql = f'''
    DELETE FROM CHANGES
    WHERE LAUNCH_NAME=?
        AND BRANCH_NAME=?
    '''
    _conn.execute(sql, (launch_name, branch_name))
    _conn.commit()
    return


def get_dtypes(_conn, table, receiver):
    cursor = _conn.cursor()
    sql = f'PRAGMA table_info({table});'
    cursor.execute(sql)
    dtypes = {col[1]:col[2] for col in cursor.fetchall()}
    cursor.close()
    if receiver == 'pandas':
        convert_types = {'REAL':'float64','INTEGER':'int64','TEXT':'object','':'int64'}
    elif receiver == 'oracle':
        convert_types = {'REAL':'NUMBER(16,6)','INTEGER':'NUMBER(11,0)','TEXT':'VARCHAR2(50)','':'NUMBER(11,0)'}
    if convert_types:
        for k,v in dtypes.items():
            dtypes[k] = convert_types.get(v)
    return dtypes


def add_branch_status(_conn, session_dict, status):
    table_name = 'BRANCH_STATUSES'
    columns = get_columns(_conn, table_name)
    values = []
    for col in columns:
        if col == 'STATUS':
            values.append(status)
        elif col == 'DATE_TIME':
            values.append(datetime.now().replace(microsecond=0))
        else:
            values.append(session_dict.get(col, None))
    sql = f'''
    INSERT INTO {table_name} ({ ','.join(columns)}) 
    VALUES ({ ','.join('?'*len(values))});
    '''
    _conn.execute(sql, values)
    _conn.commit()
    return


def add_branch_comment(_conn, session_dict):
    table_name = 'BRANCH_COMMENTS'
    columns = get_columns(_conn, table_name)
    values = []
    for col in columns:
        if col == 'COMMENT':
            values.append(session_dict.get('comment'))
        elif col == 'DATE_TIME':
            values.append(datetime.now().replace(microsecond=0))
        else:
            values.append(session_dict.get(col, None))
    sql = f'''
    INSERT INTO {table_name} ({ ','.join(columns)}) 
    VALUES ({ ','.join('?'*len(values))});
    '''
    _conn.execute(sql, values)
    _conn.commit()
    return


def get_branches(_conn, clusters):
    if type(clusters) == list:
        clusters = "','".join(clusters)
    cursor = _conn.cursor()
    sql = f'''
            SELECT BRANCH_NAME FROM BRANCH
            WHERE PRODUCT_CLUSTER_NAME IN ('{clusters}')
            ORDER BY BRANCH_NAME;
            '''
    cursor.execute(sql)
    result = [row[0] for row in cursor.fetchall()]
    cursor.close()
    return result


def get_not_empty_branches(_conn, cluster, launch_name):
    cursor = _conn.cursor()
    sql = f'''
        SELECT BRANCH_NAME
        FROM PRODUCT_CHANGES
        WHERE PRODUCT_CLUSTER_NAME=?
            AND LAUNCH_NAME=?
        GROUP BY BRANCH_NAME
        '''
    cursor.execute(sql, (cluster, launch_name))
    result = [row[0] for row in cursor.fetchall()]
    cursor.close()
    return result


def get_not_empty_branches_all(_conn, launch_name):
    cursor = _conn.cursor()
    sql = f'''
        SELECT BRANCH_NAME
        FROM CHANGES
        WHERE LAUNCH_NAME=?
        GROUP BY BRANCH_NAME
        '''
    cursor.execute(sql, (launch_name, ))
    result = [row[0] for row in cursor.fetchall()]
    cursor.close()
    return result


def empty_branch(_conn, branch_name, launch_name):
    sql = f'''
    DELETE FROM CHANGES
    WHERE BRANCH_NAME=? AND LAUNCH_NAME=? AND ACTION IS NULL
    '''
    _conn.execute(sql, (branch_name, launch_name))
    _conn.commit()
    return
        

def get_last_by_branch(_conn, table_name, branch_name, launch_name):
    cursor = _conn.cursor()
    sql = f'''
        SELECT * FROM {table_name}
        WHERE BRANCH_NAME=? AND LAUNCH_NAME=?;
        '''
    cursor.execute(sql, (branch_name, launch_name))
    result = []
    columns = [column[0] for column in cursor.description]
    for row in cursor.fetchall():
        result.append(dict(zip(columns, row)))
    cursor.close()
    return result


def duplicate_branch(_conn, username, branch_from, branch_to, launch_from, launch_to):
    table_name = 'CHANGES'
    records = get_last_by_branch(_conn, table_name, branch_from, launch_from)
    columns = get_columns(_conn, table_name)
    for rec in records:
        values = []
        if not rec.get('ACTION'):
            for col in columns:
                if col == 'BRANCH_NAME':
                    values.append(branch_to)
                elif col == 'LAUNCH_NAME':
                    values.append(launch_to)
                elif col == 'TRPL_NAME':
                    values.append(rec.get(col).replace(branch_from, branch_to))
                elif col == 'USERNAME':
                    values.append(username)
                elif col == 'DATE_TIME':
                    values.append(datetime.now().replace(microsecond=0))
                else:
                    values.append(rec.get(col, None))     
            sql = f'''
            INSERT INTO {table_name} ({','.join(columns)}) 
            VALUES ({ ','.join('?'*len(values))});
            '''
            _conn.execute(sql, values)
    _conn.commit()
    return
    

def get_messages_by_branch(_conn, branch):
    cursor = _conn.cursor()
    sql = f'''
        SELECT *
        FROM LAST_CHATS
        WHERE BRANCH_NAME=?
        ORDER BY DATE_TIME ASC;
        '''
    cursor.execute(sql, (branch, ))
    result = []
    columns = [column[0] for column in cursor.description]
    for row in cursor.fetchall():
        result.append(dict(zip(columns, row)))
    cursor.close()
    return result


def get_last_branch_status(_conn, branch, launch_name):
    cursor = _conn.cursor()
    sql = f'''
        SELECT STATUS 
        FROM LAST_BRANCH_STATUSES
        WHERE BRANCH_NAME=? AND LAUNCH_NAME=?;
        '''
    cursor.execute(sql, (branch, launch_name))
    result = cursor.fetchone()
    cursor.close()
    return (result[0] if result else None)


def get_branch_statuses(_conn, launch_name):
    cursor = _conn.cursor()
    sql = f'''
        SELECT BRANCH_NAME,
            STATUS
        FROM LAST_BRANCH_STATUSES A
        WHERE LAUNCH_NAME=? 
        ORDER BY BRANCH_NAME
    '''
    cursor.execute(sql, (launch_name, ))
    statuses_dict = {col[0]:col[1] for col in cursor.fetchall()}
    cursor.close()
    return statuses_dict


def get_statuses_df(_conn, launch_name):
    cursor = _conn.cursor()
    sql = f'''
        SELECT 
            B.PRODUCT_CLUSTER_NAME,
            B.BRANCH_NAME,
            CASE A.STATUS
                WHEN 'rejected' then 'на доработке'
                WHEN 'editing' then 'в работе'
                WHEN 'sent' then 'на согласовании'
                ELSE STATUS
            END AS STATUS
        FROM BRANCH B
        LEFT JOIN (
            SELECT *
            FROM LAST_BRANCH_STATUSES
            WHERE LAUNCH_NAME=?) A
            USING (BRANCH_NAME) 
        ORDER BY B.PRODUCT_CLUSTER_NAME, B.BRANCH_NAME
    '''
    cursor.execute(sql, (launch_name, ))
    result = []
    columns = [column[0] for column in cursor.description]
    for row in cursor.fetchall():
        result.append(dict(zip(columns, row)))
    cursor.close()
    return result


def get_branch_status_meta(_conn, branch, launch_name):
    cursor = _conn.cursor()
    sql = f'''
        SELECT DATE_TIME, USERNAME
        FROM LAST_BRANCH_STATUSES
        WHERE BRANCH_NAME=? AND LAUNCH_NAME=?;
        '''
    cursor.execute(sql, (branch, launch_name))
    result = cursor.fetchone()
    cursor.close()
    return (result[0], result[1]) if result else (None, None)


def get_cluster_status_meta(_conn, cluster, launch_name):
    cursor = _conn.cursor()
    sql = f'''
        SELECT DATE_TIME, USERNAME
        FROM LAST_CLUSTER_STATUSES
        WHERE PRODUCT_CLUSTER_NAME=? AND LAUNCH_NAME=?;
        '''
    cursor.execute(sql, (cluster, launch_name))
    result = cursor.fetchone()
    cursor.close()
    return (result[0], result[1]) if result else (None, None)


def get_cluster_statuses(_conn, clusters, launch_name):
    cursor = _conn.cursor()
    sql = f'''
        SELECT PRODUCT_CLUSTER_NAME, STATUS
        FROM LAST_CLUSTER_STATUSES A
        WHERE PRODUCT_CLUSTER_NAME IN ({ ','.join('?'*len(clusters))})
            AND LAUNCH_NAME=?
        ORDER BY PRODUCT_CLUSTER_NAME;
        '''
    cursor.execute(sql, (*clusters, launch_name))
    statuses_dict = {col[0]:col[1] for col in cursor.fetchall()}
    cursor.close()
    for cluster in clusters:
        if cluster not in statuses_dict:
            statuses_dict.update({cluster:None})
    return statuses_dict


def add_launch(_conn, launch_name, launch_type):
    table_name = 'LAUNCHES'
    columns = get_columns(_conn, table_name)
    values = []  
    for col in columns:
        if col == 'DATE_TIME':
            values.append(datetime.now().replace(microsecond=0))
        elif col == 'LAUNCH_NAME':
            values.append(launch_name)
        elif col == 'LAUNCH_TYPE':
            values.append(launch_type)
        else:
            values.append(None)
    sql = f'''
    INSERT INTO {table_name} ({ ','.join(columns)}) 
    VALUES ({ ','.join('?'*len(values))});
    '''
    _conn.execute(sql, values)
    _conn.commit()
    return


def rename_launch(_conn, launch_name, new_launch_name):
    sql = f'''
    UPDATE LAUNCHES SET LAUNCH_NAME=?
    WHERE LAUNCH_NAME=?
    '''
    _conn.execute(sql, (new_launch_name, launch_name))
    _conn.commit()
    return


def delete_launch(_conn, launch_name):
    sql = f'''
    DELETE FROM LAUNCHES
    WHERE LAUNCH_NAME=?
    '''
    _conn.execute(sql, (launch_name, ))
    _conn.commit()
    return


def add_auth(_conn, username):
    table_name = 'AUTHS'
    columns = get_columns(_conn, table_name)
    values = []
    for col in columns:
        if col == 'USERNAME':
            values.append(username)
        elif col == 'DATE_TIME':
            values.append(datetime.now().replace(microsecond=0))
    sql = f'''
    INSERT INTO {table_name} ({ ','.join(columns)}) 
    VALUES ({ ','.join('?'*len(values))});
    '''
    _conn.execute(sql, values)
    _conn.commit()
    return
    

def get_market_max_date(_conn):
    cursor = _conn.cursor()
    sql = f'''
        SELECT max(REPORT_DATE)
        FROM MARKET
        '''
    cursor.execute(sql)
    result = cursor.fetchone()
    cursor.close()
    return (result[0] if result[0] else '1970-01-01')


def get_market_max_date_time(_conn):
    cursor = _conn.cursor()
    sql = f'''
        SELECT max(DATE_TIME)
        FROM MARKET
        '''
    cursor.execute(sql)
    result = cursor.fetchone()
    cursor.close()
    return (result[0] if result[0] else '2000-01-01 00:00:00')


def update_market(_conn, df):
    columns = get_columns(_conn, 'MARKET')
    for tup in df.itertuples(index=False):
        sql = f'''
        INSERT INTO MARKET ({ ','.join('"' + col + '"' for col in columns)}) 
        VALUES ({ ','.join('?'*len(columns))});
        '''
        _conn.execute(sql, tup)
    _conn.commit()
    return


# @st.experimental_memo
# def get_market_df(_conn, market_date: str):
#     sql = f'''
#         SELECT *
#         FROM MARKET
#         WHERE REPORT_DATE = :market_date
#         '''
#     df = pd.read_sql_query(sql, _conn, params={'market_date':market_date})
#     return df


# def get_market_record(_conn, market_date, region, tariff):
#     cursor = _conn.cursor()
#     sql = f'''
#             SELECT * 
#             FROM MARKET
#             WHERE "Регион"=?
#                 AND "Название тарифа"=? 
#                 AND "Дата добавления данных"=?;
#             '''
#     cursor.execute(sql, (region, tariff, market_date))
#     columns = [column[0] for column in cursor.description]
#     result = cursor.fetchone()
#     cursor.close()
#     if result:
#         return dict(zip(columns, result))
#     return dict.fromkeys(columns)


def add_scenario(_conn, username, launch_name, region_name, scenario_name):
    table_name = 'SCENARIOS'
    columns = get_columns(_conn, table_name)
    values = []  
    for col in columns:
        if col == 'DATE_TIME':
            values.append(datetime.now().replace(microsecond=0))
        elif col == 'USERNAME':
            values.append(username)
        elif col == 'SCENARIO_NAME':
            values.append(scenario_name)
        elif col == 'LAUNCH_NAME':
            values.append(launch_name)
        elif col == 'REGION_NAME':
            values.append(region_name)
        else:
            values.append(None)
    sql = f'''INSERT INTO {table_name} ({ ','.join(columns)}) 
    VALUES ({ ','.join('?'*len(values))});
    '''
    _conn.execute(sql, values)
    _conn.commit()
    return


def delete_scenario(_conn, scenario_id):
    sql = f'''
    DELETE FROM SCENARIOS
    WHERE SCENARIO_ID=?
    '''
    _conn.execute(sql, (scenario_id, ))
    _conn.commit()
    return


def rename_scenario(_conn, old_name, new_name):
    sql = f'''
    UPDATE SCENARIOS SET SCENARIO_NAME=?
    WHERE SCENARIO_NAME=?
    '''
    _conn.execute(sql, (new_name, old_name))
    _conn.commit()
    return


def delete_action(_conn, scenario_id, tariff):
    sql = f'''
    DELETE FROM ACTIONS
    WHERE SCENARIO_ID=?
        AND TARIFF=?
    '''
    _conn.execute(sql, (scenario_id, tariff))
    _conn.commit()
    return


def get_scenarios(_conn, region_name):
    cursor = _conn.cursor()
    sql = '''
        WITH a as (
            SELECT SCENARIO_ID, max(DATE_TIME) as ACT_MAX_DATE_TIME
            FROM ACTIONS
            GROUP BY SCENARIO_ID
        ),
		
	b as (

        SELECT
            s.SCENARIO_ID, 
            s.SCENARIO_NAME, 
            s.USERNAME, 
            s.DATE_TIME,
            ss.STATUS,
            ss.LAUNCH_NAME,
            ss.USERNAME as STATUS_USERNAME,
            ss.DATE_TIME as STATUS_DATE_TIME,
            a.ACT_MAX_DATE_TIME,
			ROW_NUMBER() OVER (
				PARTITION BY s.SCENARIO_ID ORDER BY ss.DATE_TIME DESC
			) AS rn
        FROM SCENARIOS s
        LEFT JOIN a
        USING (SCENARIO_ID)
        LEFT JOIN SCENARIO_STATUSES ss
        USING (SCENARIO_ID)
        WHERE REGION_NAME = ?
        
	)
	
	SELECT
		SCENARIO_ID, 
		SCENARIO_NAME, 
		USERNAME, 
		DATE_TIME,
		STATUS,
		LAUNCH_NAME,
		STATUS_USERNAME,
		STATUS_DATE_TIME,
		ACT_MAX_DATE_TIME
	FROM b
	WHERE rn = 1
	ORDER BY DATE_TIME ASC
    '''
    cursor.execute(sql, (region_name, ))
    result = []
    columns = [column[0] for column in cursor.description]
    for row in cursor.fetchall():
        result.append(dict(zip(columns, row)))
    cursor.close()
    return result


# def get_scenario_id(_conn, scenario_name, launch_name, region_name):
#     cursor = _conn.cursor()
#     sql = '''SELECT SCENARIO_ID
#         FROM SCENARIOS
#         WHERE SCENARIO_NAME=?
#             AND LAUNCH_NAME=?
#             AND REGION_NAME=?
#         '''
#     cursor.execute(sql, (scenario_name, launch_name, region_name))
#     scenario_id = cursor.fetchall()[0][0]
#     cursor.close()
#     return scenario_id


def add_action(_conn, constructor):
    table_name = 'ACTIONS'
    columns = get_columns(_conn, table_name)
    values = []  
    for col in columns:
        if col == 'DATE_TIME':
            values.append(datetime.now().replace(microsecond=0))
        else:
            values.append(constructor.get(col, None))
    sql = f'''INSERT OR REPLACE INTO {table_name} ({ ','.join(columns)}) 
    VALUES ({ ','.join('?'*len(values))});
    '''
    _conn.execute(sql, values)
    _conn.commit()
    return


def get_action_by_tariff(_conn, scenario_id, tariff):
    cursor = _conn.cursor()
    sql = f'''
            SELECT * 
            FROM ACTIONS 
            WHERE SCENARIO_ID=?
                AND TARIFF=?
            '''
    cursor.execute(sql, (scenario_id, tariff))
    columns = [column[0] for column in cursor.description]
    result = cursor.fetchone()
    cursor.close()
    if result:
        return dict(zip(columns, result))
    return dict.fromkeys(columns)


def get_actions(_conn, scenario_id):
    cursor = _conn.cursor()
    sql = f'''
            SELECT * 
            FROM ACTIONS 
            WHERE SCENARIO_ID=?
            '''
    cursor.execute(sql, (scenario_id, ))
    result = []
    columns = [column[0] for column in cursor.description]
    for row in cursor.fetchall():
        result.append(dict(zip(columns, row)))
    cursor.close()
    return result


def get_region_market_df(_conn, region_name):
    sql = f'''
        SELECT *
        FROM MARKET_CLEAN
        WHERE REGION_NAME = :region_name
        '''
    df = pd.read_sql_query(sql, _conn, 
        params={'region_name':region_name}
    )
    return df

    # cursor = _conn.cursor()
    # sql = f'''
    #     SELECT *
    #     FROM MARKET_CLEAN
    #     WHERE REGION_NAME=?
    #     '''
    # cursor.execute(sql, (region_name, ))
    # columns = [column[0] for column in cursor.description]
    # result = cursor.fetchone()
    # cursor.close()
    # if result:
    #     return dict(zip(columns, result))
    # return dict.fromkeys(columns)


def get_region_scenario_df(_conn, scenario_id):
    sql = f'''
    WITH SCE AS (
        SELECT SCENARIO_ID, REGION_NAME
            FROM SCENARIOS
            WHERE SCENARIO_ID = :scenario_id
    ),

    ACT AS (
        SELECT
            'Tele2' AS OPERATOR, TARIFF, IS_SHELF, IS_CONVERGENT, FEE_TYPE, FEE, IS_FEE_DISCOUNT, 
            FEE_AFTER_DISCOUNT, VOICE_MIN, DATA_GB, EXTRA, USAGE, INTERNET_EXTRA, ACTION
        FROM ACTIONS
        WHERE SCENARIO_ID = (SELECT SCENARIO_ID FROM SCE)	
    ),

    MAR AS (
        SELECT
            MARKET_CLEAN.OPERATOR, 
			MARKET_CLEAN.TARIFF, 
			MARKET_CLEAN.IS_SHELF, 
			MARKET_CLEAN.IS_CONVERGENT, 
			MARKET_CLEAN.FEE_TYPE,
			MARKET_CLEAN.FEE, 
			MARKET_CLEAN.IS_FEE_DISCOUNT,
            MARKET_CLEAN.FEE_AFTER_DISCOUNT, 
			MARKET_CLEAN.VOICE_MIN, 
			MARKET_CLEAN.DATA_GB, 
            MARKET_CLEAN.PROMO as EXTRA,
			MARKET_CLEAN.USAGE, 
			MARKET_CLEAN.INTERNET_EXTRA, 
			CASE ACT.ACTION WHEN 'Новый тариф' THEN 'Закрыть' ELSE NULL END AS ACTION
        FROM MARKET_CLEAN
		LEFT JOIN ACT
			ON MARKET_CLEAN.TARIFF = ACT.TARIFF
			AND MARKET_CLEAN.OPERATOR = ACT.OPERATOR
			AND ACT.ACTION <> 'Закрыть'
        WHERE REGION_NAME = (SELECT REGION_NAME FROM SCE)
    ),

    MAR_ACT AS (
        SELECT U.*, ROW_NUMBER() OVER() AS ID
        FROM (SELECT * FROM ACT
                UNION ALL
                SELECT * FROM MAR) U
    )

    SELECT MAR_ACT.*, MAR_ACT1.ID AS ID_NEW
    FROM MAR_ACT
    LEFT JOIN MAR_ACT as MAR_ACT1
        ON MAR_ACT.OPERATOR = MAR_ACT1.OPERATOR
        AND MAR_ACT.TARIFF = MAR_ACT1.TARIFF
        AND MAR_ACT.ID <> MAR_ACT1.ID
        AND MAR_ACT1.ACTION = 'Изменить'
    '''
    df = pd.read_sql_query(sql, _conn,
        params={'scenario_id':scenario_id}
    )
    return df


def upd_scenario_status(_conn, scenario_id, status, username, launch_name=None):
    columns = get_columns(_conn, 'SCENARIO_STATUSES')
    values = []  
    for col in columns:
        if col == 'DATE_TIME':
            values.append(datetime.now().replace(microsecond=0))
        elif col == 'STATUS':
            values.append(status)
        elif col == 'SCENARIO_ID':
            values.append(scenario_id)
        elif col == 'USERNAME':
            values.append(username)
        elif col == 'LAUNCH_NAME':
            values.append(launch_name)
        else:
            values.append(None)
    sql = f'''
    INSERT OR REPLACE INTO SCENARIO_STATUSES ({ ','.join(columns)}) 
    VALUES ({ ','.join('?'*len(values))});
    '''
    _conn.execute(sql, values)
    _conn.commit()
    return



def del_scenario_status(_conn, scenario_id, status):
    sql = f'''
    DELETE FROM SCENARIO_STATUSES WHERE SCENARIO_ID=? AND STATUS=?
    '''
    _conn.execute(sql, (scenario_id, status))
    _conn.commit()
    return


def clear_for_convert(_conn, branch_name, convert_launch_name):
    sql = f'''
    DELETE FROM CHANGES
    WHERE BRANCH_NAME=? AND LAUNCH_NAME=? AND ACTION IS NOT NULL;
    '''
    _conn.execute(sql, (branch_name, convert_launch_name))
    _conn.commit()
    return