__all__ = ['get_file_id_from_folder']
import json
from docassemble.interview.google_drive import list_files_in_path,get_folder_id2



def get_files_from_folder(path,root='AdvocateCopilotDND'):
  return list_files_in_path(path, root=get_folder_id2('AdvocateCopilotDND'))

def get_file_id_from_folder(file_name,path,root='AdvocateCopilotDND'):
    files = get_files_from_folder(path,root)
    needed_file = ''
    for file in files:
        if file['name'] == file_name:
          needed_file = file
          break
    return needed_file