from cx_Oracle import connect, init_oracle_client
import os
import pandas as pd
import warnings


curdir = os.path.dirname(os.path.realpath(__file__)) + '\\'
libdir = os.path.join(curdir, r'instantclient_19_11\\')
try:
    init_oracle_client(lib_dir=libdir)
except:
    pass


CONN_INFO = {
    'host': '10.0.2.10',
    'port': 1521,
    'user': 'USER_FROM_PLM',
    'psw': 'Wjkgty185##',
    'service': 'DWH_CLIENT'
}

CONN_STR = '{user}/{psw}@{host}:{port}/{service}'.format(**CONN_INFO)

QUERY = f'''
    SELECT SYS_CONTEXT('USERENV','CURRENT_SCHEMA') FROM DUAL
'''


# @st.cache(allow_output_mutation=True)
# def create_oracle_connection():
#     oracle_conn = None
#     try:
#         oracle_conn = connect(CONN_STR)
#     except Exception as e:
#         print(e)
#     return oracle_conn


def drop_constraint(table_name, constraint):
    query = f'''
    ALTER TABLE {table_name}
    DROP CONSTRAINT {constraint}
    '''
    with connect(CONN_STR) as session:
        c = session.cursor()
        c.execute(query)
        result = session.commit()
        c.close()
        print(result)


def execute_crud_query(query):
    with connect(CONN_STR) as session:
        c = session.cursor()
        c.execute(query)
        result = session.commit()
        c.close()
        print(result)



def truncate_table(table_name):
    with connect(CONN_STR) as session:
        query = f'TRUNCATE TABLE {table_name}'
        c = session.cursor()
        c.execute(query)
        result = session.commit()
        c.close()
        print(result)


def update(table_name, cluster_name, launch_name):
    with connect(CONN_STR) as session:
        query = f'''
        UPDATE {table_name}
        SET IS_ACTUAL = 0
        WHERE LAUNCH_NAME = :launch_name
            AND PRODUCT_CLUSTER_NAME = :cluster_name
        '''
        c = session.cursor()
        c.execute(query, {"cluster_name":cluster_name, "launch_name":launch_name})
        result = session.commit()
        c.close()
        print(result)

    

def insert(table_name, records):
    with connect(CONN_STR) as session:
        query = f'''
        SELECT column_name
        FROM USER_TAB_COLUMNS
        WHERE table_name = :table_name
        '''
        c = session.cursor()
        c.execute(query, table_name=table_name)
        result = c.fetchall()
        columns = [row[0] for row in result]
        query = f'''
            INSERT INTO {table_name} ({', '.join(columns)})
            VALUES (:{', :'.join(columns)})
        '''
        prepared_records = []
        for rec in records:
            temp_dict = {k:v for k, v in rec.items() if k in columns}
            prepared_records.append(temp_dict)
        c.executemany(query, prepared_records)
        result = session.commit()
        c.close()
        print(result)


def drop_if_exists(table_name):
    with connect(CONN_STR) as session:
        c = session.cursor()
        c.execute(f'''
        BEGIN
        EXECUTE IMMEDIATE 'DROP TABLE ' || '{table_name}';
        EXCEPTION
        WHEN OTHERS THEN
            IF SQLCODE != -942 THEN
                RAISE;
            END IF;
        END;
        ''')
        result = session.commit()
        c.close()
        print(result)


def show_constraints(table_name):
    query = f'''
    select
        CONSTRAINT_NAME C_NAME,
        INDEX_NAME,
        CONSTRAINT_TYPE,
        Search_condition,
        R_CONSTRAINT_NAME R_NAME
    from user_constraints
    where TABLE_NAME = :table_name
    '''
    with connect(CONN_STR) as session:
        c = session.cursor()
        c.execute(query, table_name=table_name)
        result = c.fetchall()
        print(result)


def comment_table(table_name, comment_dic):
    with connect(CONN_STR) as session:
        c = session.cursor()
        for col_name, comment in comment_dic.items():
            query = f"COMMENT ON COLUMN {table_name}.{col_name} IS '{comment}'"
            c.execute(query)
        result = session.commit()
        c.close()
        print(result)


def generate_comment_query(table, column, text):
    return f'''COMMENT ON COLUMN {table}.{column} IS '{text}';
    '''


def grant(what_grant, schema_name, table_name, receiver):
    query = f'''GRANT {what_grant} ON {schema_name}.{table_name} to {receiver}'''
    with connect(CONN_STR) as session:
        c = session.cursor()
        c.execute(query)
        result = session.commit()
        c.close()
        print(result)


def create(table_name: str, dtypes: dict, pk_list: list, is_autoincr_id: bool=False):
    query = generate_create_query(table_name, dtypes, pk_list, is_autoincr_id)
    with connect(CONN_STR) as session:
        c = session.cursor()
        c.execute(query)
        result = session.commit()
        c.close()
        print(result)


def generate_create_query(table_name: str, dtypes: dict, pk_list: list, is_autoincr_id=False):
    rows = []
    for k,v in dtypes.items():
        rows.append(f"{k} {v}")
    if is_autoincr_id:
        autoincr_text = '''ID NUMBER GENERATED by default on null as IDENTITY, '''
    else:
        autoincr_text = ''
    whole_query = f'''
        CREATE TABLE {table_name} (
            {autoincr_text}
            {', '.join(rows)},
            CONSTRAINT {table_name}_PK primary key ({', '.join(pk_list)})
        )'''
    return whole_query


def get_data_from(table_name):
    with connect(CONN_STR) as session:
        c = session.cursor()
        query = f'''
            SELECT * FROM {table_name}
        '''
        c.execute(query)
        result = c.fetchall()
        col_names = [row[0] for row in c.description]
        df = pd.DataFrame.from_records(result, columns=col_names)
        c.close()
        return df


def get_micro_df(launch_name, product_cluster_name):
    with connect(CONN_STR) as session:
        c = session.cursor()
        if product_cluster_name == '(All)':
            query = f'''
                SELECT
                    *
                FROM PRODUCT_MICRO
                WHERE LAUNCH_NAME = :launch_name
                ORDER BY BRANCH_NAME, "Группа"
                '''
            c.execute(query, launch_name=launch_name)
        else:
            query = f'''
                SELECT
                    *
                FROM PRODUCT_MICRO
                WHERE LAUNCH_NAME = :launch_name
                AND "Кластер" = :product_cluster_name
                ORDER BY BRANCH_NAME, "Группа"
                '''
            c.execute(query, product_cluster_name=product_cluster_name, launch_name=launch_name)
        result = c.fetchall()
        col_names = [row[0] for row in c.description]
        df = pd.DataFrame.from_records(result, columns=col_names)
        c.close()
        return df


def get_assemblings_df(launch_name, product_cluster_name):
    with connect(CONN_STR) as session:
        c = session.cursor()
        if product_cluster_name == '(All)':
            query = f'''
                SELECT *
                FROM PRODUCT_ASSEMBLING
                WHERE LAUNCH_NAME = :launch_name
                ORDER BY BRANCH_NAME, "Тариф"
                '''
            c.execute(query, LAUNCH_NAME=launch_name)
        else:
            query = f'''
                SELECT *
                FROM PRODUCT_ASSEMBLING
                WHERE LAUNCH_NAME = :launch_name
                AND "Кластер" = :product_cluster_name
                ORDER BY BRANCH_NAME, "Тариф"
                '''
            c.execute(query, launch_name=launch_name, product_cluster_name=product_cluster_name)
        result = c.fetchall()
        col_names = [row[0] for row in c.description]
        df = pd.DataFrame.from_records(result, columns=col_names)
        c.close()
        return df


def get_pce_df(launch_name, product_cluster_name):
    with connect(CONN_STR) as session:
        c = session.cursor()
        if product_cluster_name == '(All)':
            query = f'''
                SELECT
                    *
                FROM PRODUCT_CHANGES pc
                INNER JOIN PRODUCT_CHANGES_ENRICHED pce
                    ON pc.LAUNCH_NAME = pce.PROJECT
                    AND pc.TARIFF = pce.TRPL_TYPE
                    AND pc.BRANCH_NAME = pce.BRANCH_NAME
                    AND pc.IS_ACTUAL = pce.IS_ACTUAL
                WHERE pc.IS_ACTUAL = 1
                    AND pc.LAUNCH_NAME = :launch_name
                '''
            c.execute(query, launch_name=launch_name)
        else:
            query = f'''
                SELECT
                    *
                FROM PRODUCT_CHANGES pc
                INNER JOIN PRODUCT_CHANGES_ENRICHED pce
                    ON pc.LAUNCH_NAME = pce.PROJECT
                    AND pc.TARIFF = pce.TRPL_TYPE
                    AND pc.BRANCH_NAME = pce.BRANCH_NAME
                    AND pc.IS_ACTUAL = pce.IS_ACTUAL
                WHERE pc.IS_ACTUAL = 1
                    AND pc.LAUNCH_NAME = :launch_name
                    AND pc.PRODUCT_CLUSTER_NAME = :product_cluster_name
                '''
            c.execute(query, launch_name=launch_name, product_cluster_name=product_cluster_name)
        result = c.fetchall()
        col_names = [row[0] for row in c.description]
        df = pd.DataFrame.from_records(result, columns=col_names)
        c.close()
        return df


def upd_assembling_params(param_value, rn):
    with connect(CONN_STR) as session:
        c = session.cursor()
        print(f'''
            UPDATE ASSEMBLING_PARAMS
            SET PARAM_VALUE = {param_value}
            WHERE ROWID = {rn}
        ''')
        query = f'''
            UPDATE ASSEMBLING_PARAMS
            SET PARAM_VALUE = :param_value
            WHERE ROWID = :rn
        '''
        c.execute(query, param_value=param_value, rn=rn)
        result = session.commit()
        c.close()
        print(result)


def get_columns_dict():
    with connect(CONN_STR) as session:
        c = session.cursor()
        query = f'''
            SELECT a.column_name COLUMN_NAME,
                COALESCE(MIN(Substr(a.comments,1,200)), COLUMN_NAME) REPR_NAME
            FROM   all_col_comments a
            WHERE  a.table_name IN ('PRODUCT_CHANGES','PRODUCT_CHANGES_ENRICHED')
            AND    a.owner = 'USER_FROM_PLM'
            GROUP BY COLUMN_NAME
        '''
        c.execute(query)
        columns_dict = {col[0]:col[1] for col in c.fetchall()}
        c.close()
        return columns_dict


def get_assemling_params():
    with connect(CONN_STR) as session:
        c = session.cursor()
        query = f'''SELECT ROWID, ASSEMBLING_PARAMS.*
            FROM ASSEMBLING_PARAMS
        '''
        c.execute(query)
        result = c.fetchall()
        col_names = [row[0] for row in c.description]
        df = pd.DataFrame.from_records(result, columns=col_names)
        c.close()
        return df


def show_tables():
    with connect(CONN_STR) as session:
        c = session.cursor()
        query = f'''
            select TABLE_NAME from user_tables
        '''
        c.execute(query)
        result = c.fetchall()
        c.close()
        return result


def main():
    with connect(CONN_STR) as session:
        c = session.cursor()
        print(QUERY)
        c.execute(QUERY)
        for row in c:
            print(row)



if __name__ == '__main__':
    pass


 # коллегам доступы
 # PI_SERVICE_USER, SERVICE_RPI
 # SERVICE_RPI

# GRANT SELECT ON TABLE USER_FROM_PLM.PRODUCT_CHANGES to PI_SERVICE_USER;
# GRANT SELECT ON TABLE USER_FROM_PLM.PRODUCT_CHANGES to SERVICE_RPI;