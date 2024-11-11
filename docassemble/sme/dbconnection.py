from docassemble.interview.database import raw_query
from docassemble.webapp import db_object
from docassemble.base.util import get_config
from datetime import datetime
from docassemble.interview.database import add
import json


__all__ = ['raw_query1', 'insertOpenAIResponse', 'save_file_info_db', 'fetchCompanyList', 'fetchEmployeeList', 'fetchCompanyData', 'fetchEmployeeData', 'insertEmployeeData', 'insertRecord', 'updateEmployeeData', 'dbUpdateRelation', 'fetchPositionList','return_file_public_url']


def raw_query1(query, isRead=False):
    try:
        resp = "OK"
        connection = db_object.db.engine.raw_connection()
        cur = connection.cursor()
        cur.execute(query)  # Execute the INSERT query
        if isRead:
            resp = cur.fetchall()
        else:
            # Fetch the returned UUID if it's an INSERT query with RETURNING
            if query.strip().lower().startswith("insert") and "returning uuid" in query.lower():
                resp = cur.fetchone()[0]  # Fetch the first column of the first row
            connection.commit()
        cur.close()
        return True, resp
    except Exception as err:
        return False, err

def fetchCompanyList(userID):
    rows = []
    dataFetchStatus = raw_query(f"""SELECT uuid, jsondata->>'name' AS Name FROM user_data_map WHERE type = 'company' AND user_id = '{userID}';""",True)
    if dataFetchStatus[0] == True:
        rows = dataFetchStatus[1]
    rows.insert(0, ("Other", "Add new"))
    return rows

def fetchEmployeeList(CompanyUUID, status):
    rows = []
    dataFetchStatus = raw_query(f"""
    WITH ExtractedUUIDs AS (
    SELECT UNNEST(relation) AS extracted_uuid
    FROM user_data_map
    WHERE uuid = '{CompanyUUID}'
    )
    SELECT udm.uuid, udm.jsondata->>'name' AS Name
    FROM user_data_map udm
    JOIN ExtractedUUIDs eu ON udm.uuid = eu.extracted_uuid
	WHERE udm.jsondata->>'status' = '{status}';
    """,True)
    if dataFetchStatus[0] == True:
        rows = dataFetchStatus[1]
    rows.insert(0, ("Other", "Add new"))
    return rows

def fetchCompanyData(uuid):
    res, resdata = raw_query1(f"SELECT  jsondata FROM user_data_map WHERE uuid = '{uuid}'::uuid;", True)
    if res == False:
        data = {
            "name": "",
            "type": "",
            "address": {
                "address": "",
                "city": "",
                "state": "",
                "zip": "",
                "country": ""
            },
            "about": "",
            "url": "",
            "hr": ""
        }
    else:
        data = resdata[0][0]
    return data

def fetchEmployeeData(uuid):
    res, resdata = raw_query1(f"SELECT  jsondata FROM user_data_map WHERE uuid = '{uuid}'::uuid;", True)
    if res == False:
        data = {
            "status": "",
            "name": "",
            "prefix": "",
            "age": "",
            "father_husband": "",
            "address": {
                "address": "",
                "city": "",
                "state": ""
            },
            "mobile": ""
        }
    else:
        data = resdata[0][0]
    return data

def insertEmployeeData(role, jsondata, userID):
    res, data = raw_query1(f"INSERT INTO user_data_map(type, jsondata, user_id) VALUES ('{role}', '{jsondata}'::json, '{userID}') returning uuid::text;")
    return res, data

def updateEmployeeData(uuid, jsondata):
    res, data = raw_query1(f"UPDATE user_data_map SET jsondata = '{jsondata}'::json WHERE uuid = '{uuid}'::uuid;")
    return res, data

def insertRecord(role_map, record, userID):
    res, data = raw_query1(f"INSERT INTO contract_records(role_map, info,user_id) VALUES ('{role_map}'::json, '{record}'::json, '{userID}') returning uuid::text;")
    return res, data

def dbUpdateRelation(uuid, relation):
  return raw_query(f"UPDATE user_data_map SET relation = COALESCE(relation, ARRAY[]::uuid[]) || '{relation}'::uuid WHERE uuid = '{uuid}'::uuid;",False)

def fetchPositionList(uuid = 'a2843fca-a395-4001-af1f-a8e8339f88b2'):
    rows = [] 
    dataFetchStatus = raw_query(f"""
        SELECT
            value AS json_value,
            key AS json_key
        FROM
            clauses,
            jsonb_each_text(conditions) AS json_data WHERE uuid = '{uuid}'::uuid;
        """,True)
    if dataFetchStatus[0] == True:
        rows = dataFetchStatus[1]
    rows.insert(0, ("Other", "Others"))
    return rows



def insertOpenAIResponse(userID, position, prompt_response):
    response = {
        f"{position}" : f"{prompt_response}" 
    }
    res, data = raw_query1(f"INSERT INTO openai(user_id,prompt,response) VALUES ('{userID}','{position}'::text,'{json.dumps(response)}'::json) RETURNING id::text;")
    return res, data

def save_file_info_db(files, user_id, interview_id,interview_name,interview_link,filename1,grp_id):
  # Select first DAFile from DAFileList
  file = files
  # New unique filename
  filename = f'{user_id}_{interview_id}_{datetime.now().strftime("%H%M%S%Y%m%d")}'
  # Set file attributes
  file.set_attributes(private=False, persistent=True, filename=filename)
  # Set file access for specific user
  file.user_access(user_id)
  # Save file
  file.commit()
  # Add DB entry for file mapped to user
  return [f'{filename1}.{file.extension}',file.url_for(external=True)]
  
  isSucess, [file_id] = add('user_files', {'user_id': user_id, 'filename': f'{filename1}.{file.extension}', 'file_url': file.url_for(external=True), 'interview_id': interview_id,'interview_name':interview_name,'interview_link':interview_link,'grp_id':grp_id}, 'id')
  return isSucess, file_id
def return_file_public_url(files, user_id,filename):
  # Select first DAFile from DAFileList
  file = files
  # Set file attributes
  file.set_attributes(private=False, persistent=True, filename=filename)
  # Set file access for specific user
  file.user_access(user_id)
  # Save file
  file.commit()
  # Add DB entry for file mapped to user
  return [f'{filename}.{file.extension}',file.url_for(external=True)]

