import glob
import os
import shutil
from google.auth.transport import Response
import pandas as pd

import pickle
import re
import io
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.http import MediaIoBaseDownload
import requests
from tqdm import tqdm
import download_files
import upload_files


# If modifying these scopes, delete the file token.pickle.
SCOPES = ['https://www.googleapis.com/auth/drive.metadata',
          'https://www.googleapis.com/auth/drive',
          'https://www.googleapis.com/auth/drive.file'
          ]


def get_gdrive_service():
    creds = None
    # The file token.pickle stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open('token.pickle', 'wb') as token:
            pickle.dump(creds, token)
    # initiate Google Drive service API
    return build('drive', 'v3', credentials=creds)



def sync_files():
    cwd = os.getcwd()
    local_folder = cwd + "/local_folder"
    print("\n\nLocal Sync Folder : ",local_folder)
    # print(local_folder)
    local_files_list = os.listdir(local_folder)
    print("\n\nAll local files : ")
    
    for file in local_files_list:
        print(file)


    folder_metadata = {
        'name': "TestFolder",
        'mimeType': 'application/vnd.google-apps.folder'
    }

    print("\n\nGoogle Drive Sync Folder : ")
    service = get_gdrive_service()
    response = service.files().list(q="name='{name}' and mimeType='{mimeType}'".format(name=folder_metadata['name'], mimeType=folder_metadata['mimeType'])).execute()
    # print("\n\nResponse : \n",response)
    items = response.get('files', [])

    if not items:
        print("'{}'' not found, create new".format(folder_metadata['name']))
        file = service.files().create(body=folder_metadata,
                                            fields='id').execute()
    else:
        print("'{}'' found".format(folder_metadata['name']))
        file = items[0]

    folder_id = file.get('id')
    print("folderId={}".format(folder_id))

    response = service.files().list(q="'{folderId}' in parents".format(folderId=folder_id)).execute()
    # response = service.files().list().execute()
    # print("\n\nGdrive Files response", response)
    print("\n\n\nGdrive Files List : ")
    gdrive_files_list = {}
    for temp in response.get('files'):
        print(temp)
        gdrive_files_list[temp['name']] = temp['id']

    # print("\n\n")
    # for key, val in gdrive_files_list.items():
    #     print(key, val)



    trash_response = service.files().list(q="trashed = true").execute()
    # print(trash_response)
    print("\n\n\nTrash Files List :")
    trash_files_list = {}
    for temp in trash_response.get('files'):
        print(temp)
        trash_files_list[temp['name']] = temp['id']

    print("\n\n")
    # for key, val in trash_files_list.items():
    #     print(key, val)





    # print("\n\ngrive_files_list", gdrive_files_list.keys())
    # print("\n\ntrash_files_list", trash_files_list.keys())
    # print("\n\nlocal_file_list", local_files_list)


    # download

    print("\n\n---------------  Downloading Syncing --------------\n")
    for file_name in gdrive_files_list.keys():

        # file_id = gdrive_files_list[file_name]
        # print("filename : ",file_name,"     Response : ",service.files().trash(fileId=file_id).execute())
        
        if file_name not in trash_files_list and file_name not in local_files_list :
            file_id = gdrive_files_list[file_name]
            # make it shareable
            service.permissions().create(body={"role": "reader", "type": "anyone"}, fileId=file_id).execute()
            # download file
            # print("\n\nlocal_folder", local_folder)
            # print("\n\nFile_name", file_name)
            download_files.download_file_from_google_drive(file_id, local_folder+"/"+file_name)
            print()
    print("---------------------------------------------------")

    # upload

    print("\n\n\n------------------  Upload Syncing ----------------")
    for file_name in local_files_list:
        if file_name in trash_files_list.keys():
            path = local_folder+"/"+file_name
            if os.path.exists(path):
                print("\nRemoving Local File : ", file_name)
                os.remove(path)


        elif file_name not in gdrive_files_list.keys():
            upload_files.upload_files(local_folder, file_name, folder_metadata['name'])

            
    print("\n---------------------------------------------------\n\n")

if __name__ == '__main__':
    sync_files()