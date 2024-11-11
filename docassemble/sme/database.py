import psycopg2
from docassemble.webapp import db_object
import json
__all__ = ['database_operations','update', 'fetch', 'add', 'add_multiple', 'delete', 'add_cases', 'fetch_client_by_case', 'fetch_case_cnr_details', 'raw_query']
def connect_to_postgres():
    try:
        connection = db_object.db.engine.raw_connection()
        return connection
    except Exception as e:
        print(f"Error: Unable to connect to the database.\n{e}")
        return None

def execute_query(connection, query,parameters = None,is_read=False):
    try:
        cursor = connection.cursor()
        cursor.execute("BEGIN;")
        if parameters == None:
          cursor.execute(query)
        else :
          cursor.execute(query,parameters)
        if is_read:
            result = [dict(zip([column[0] for column in cursor.description], row)) for row in cursor.fetchall()]
            return json.dumps(result, default=str),True
        else:
            connection.commit()
            return None, True
    except Exception as e:
        connection.rollback()
        print(f"Error: Unable to execute the query.\n{e}")
        return f"Error: Unable to execute the query.\n{e}", False
    finally:
        cursor.close()
        connection.close()
        print("Connection closed.")

def database_operations(query,is_read,parameters=None):
    connection = connect_to_postgres()
    if connection:
        result = execute_query(connection, query,parameters =parameters,is_read = is_read )
        return result
    else:
        return None,False
from docassemble.webapp import db_object
import psycopg2

table_columns = {
  'case_details' : ['id', 'cnr', 'updated_title', 'updated_petitioner', 'updated_respondent', 'updated_clients', 'representing', 'approved', 'adv_id'],
  'CNR_Cleaned': ['cnr', 'reg_no', 'case_type', 'petitioner', 'respondent', 'party', 'next_heading_date', 'case_stage', 'acts_and_sections', 'fir_no', 'fir_station', 'fir_year', 'court_complex', 'court_name', 'court_name_hi', 'active', 'petitioner_advocates', 'respondent_advocates', 'filing_date', 'updated_at'],
  'client_details': ['id', 'name', 'name_hi', 'father_name', 'father_name_hi', 'caste', 'caste_hi', 'age', 'mobile', 'email', 'address', 'auth_rep', 'adv_id', 'address_hi'],
  'client_case_map': ['client_id', 'case_id'],
  'case_cnr_details': ['id', 'cnr ', 'updated_title', 'updated_petitioner', 'updated_respondent', 'updated_clients', 'representing', 'approved', 'adv_id', 'cnr ', 'reg_no', 'case_type', 'petitioner', 'respondent', 'party', 'next_heading_date', 'case_stage', 'acts_and_sections', 'fir_no', 'fir_station', 'fir_year', 'court_complex', 'court_name', 'court_name_hi', 'active', 'petitioner_advocates', 'respondent_advocates', 'filing_date', 'updated_at'],
  'user_files': ['id', 'user_id', 'filename', 'file_url', 'interview_id','interview_name','created_at','interview_link','grp_id']
}

def convert_arr_to_dict(table, data, cols=None):
  arr = []
  for x in data:
    dic = {}
    for i in range(len(x)):
      if cols:
        dic[cols[i]] = x[i]
      else:
        dic[table_columns[table][i]] = x[i]
    arr.append(dic)
  return arr

def update(table_name, dic, where):
    try:
        connection = db_object.db.engine.raw_connection()
        cur = connection.cursor()
        bs = "'" #backslash not allowed in f'string
        cur.execute(f'UPDATE {table_name} SET {",".join([f"{x[0]}={bs}{x[1]}{bs}" for x in dic.items()])} WHERE {where};')
        connection.commit()
        cur.close()
        return True, 'OK'
    except Exception as err:
        return False, err

def fetch(table_name,columns = [], where = ""):
    try:
        connection = db_object.db.engine.raw_connection()
        cur = connection.cursor()
        cur.execute(f'SELECT {",".join(columns) if len(columns) else "*"} FROM {table_name} {"WHERE " + where if where else ""};')
        rows = cur.fetchall()
        cur.close()
        if len(columns):
          return True, convert_arr_to_dict(table_name, rows, columns)
        elif table_name in table_columns:
          return True, convert_arr_to_dict(table_name, rows)
        return True, rows
    except Exception as err:
        return False, err

def fetch_case_cnr_details(adv_id, cnr=None, columns=[]):
    try:
        connection = db_object.db.engine.raw_connection()
        cur = connection.cursor()
        columns_str = ','.join(columns) if columns else '*'
        cnr_condition = f"AND public.case_details.cnr = '{cnr}'" if cnr else ''
        query = f"""
            SELECT {columns_str}
            FROM public.case_details
            LEFT JOIN public."CNR_Cleaned" ON public.case_details.cnr = public."CNR_Cleaned".cnr
            WHERE public.case_details.adv_id = '{adv_id}' {cnr_condition};
        """
        cur.execute(query)
        rows = cur.fetchall()
        cur.close()
        if columns:
            return True, convert_arr_to_dict('case_cnr_details', rows, columns)
        return True, convert_arr_to_dict('case_cnr_details', rows)
    except Exception as err:
        return False, err
      
def fetch_client_by_case(case_id):
    try:
        connection = db_object.db.engine.raw_connection()
        cur = connection.cursor()
        cur.execute(f"select client_details.* from client_details inner join client_case_map on client_details.id = client_id where case_id = {case_id};")
        rows = cur.fetchall()
        cur.close()
        return True, convert_arr_to_dict('client_details', rows)
    except Exception as err:
        return False, err

def add(table_name, dic, return_val=None):
    try:
        connection = db_object.db.engine.raw_connection()
        cur = connection.cursor()
        bs = "'" #backslash not allowed in f'string
        cur.execute(f'INSERT INTO {table_name} ({",".join(dic.keys())}) VALUES ({",".join([bs+str(x)+bs for x in dic.values()])}) {"returning "+return_val if return_val else ""};')
        if return_val:
          rows = cur.fetchall()
        connection.commit()
        cur.close()
        if return_val:
          return True, rows[0]
        else:
          return True, "OK"
    except Exception as err:
        return False, err

def add_multiple(table_name, arr, return_val=None):
    try:
        connection = db_object.db.engine.raw_connection()
        cur = connection.cursor()
        bs = "'" #backslash not allowed in f'string
        cur.execute(f'INSERT INTO {table_name} ({",".join(arr[0].keys())}) VALUES ({ "),(".join( [ ",".join([bs+str(x)+bs  for x in dic.values()])  for dic in arr])}) ON CONFLICT DO NOTHING {"returning "+return_val if return_val else ""};')
        rows = cur.fetchall()
        connection.commit()
        cur.close()
        return True, rows
    except Exception as err:
        return False, err
      
def delete(table_name, where):
    try:
        connection = db_object.db.engine.raw_connection()
        cur = connection.cursor()
        cur.execute(f'DELETE FROM {table_name} WHERE {where};')
        connection.commit()
        cur.close()
        return True, 'OK'
    except Exception as err:
        return False, err
      
def raw_query(query, isRead = False,returning = False):
    try:
        resp = "OK"
        connection = db_object.db.engine.raw_connection()
        cur = connection.cursor()
        cur.execute(query)
        if isRead:
          resp = cur.fetchall()
        else:
          connection.commit()
          if returning :
              resp = cur.fetchall()
        return True, resp
    except Exception as err:
        return False, err
    finally:
        cur.close()
        connection.close()
      

def add_cases(arr, adv_id):
    try:
        connection = db_object.db.engine.raw_connection()
        cur = connection.cursor()
        bs = "'" #backslash not allowed in f'string
        cur.execute(f'INSERT INTO case_details ({",".join(arr[0].keys())}) VALUES ({ "),(".join( [ ",".join([bs+str(x)+bs  for x in dic.values()])  for dic in arr])}) ON CONFLICT DO NOTHING returning id;')
        rows = cur.fetchall()
        if len(rows):
          cur.execute(f'INSERT INTO adv_case_map (adv_id, case_id) VALUES ({ "),(".join( [f"{adv_id},{x[0]}" for x in rows])});')
        connection.commit()
        cur.close()
        return True, 'OK'
    except Exception as err:
        return False, err