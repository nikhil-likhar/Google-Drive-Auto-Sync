from __future__ import print_function

import os
import glob

from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from httplib2 import Http
from oauth2client import file as oauth2file, client, tools

SCOPES = 'https://www.googleapis.com/auth/drive'
CREDENTIAL_FILE = 'client_credentials.json'
TOKEN_FILE = 'gdrive_sync_token.json'

def sync_folder(local_folder, gdrive_folder_name):
    store = oauth2file.Storage(TOKEN_FILE)
    creds = store.get()
    if not creds or creds.invalid:
        flow = client.flow_from_clientsecrets(CREDENTIAL_FILE, SCOPES)
        creds = tools.run_flow(flow, store)
    service = build('drive', 'v3', http=creds.authorize(Http()))
    drive_service = service

    file_metadata = {
        'name': gdrive_folder_name,
        'mimeType': 'application/vnd.google-apps.folder'
    }

    response = drive_service.files().list(q="name='{name}' and mimeType='{mimeType}'".format(name=file_metadata['name'], mimeType=file_metadata['mimeType'])).execute()
    items = response.get('files', [])
    if not items:
        print("'{0}'' not found, create new".format(file_metadata['name']))
        file = drive_service.files().create(body=file_metadata,
                                            fields='id').execute()
    else:
        print("'{0}'' found".format(file_metadata['name']))
        file = items[0]

    folder_id = file.get('id')
    print("folderId={0}".format(folder_id))

    # check files on gdrive
    response = drive_service.files().list(q="'{folderId}' in parents".format(folderId=folder_id)).execute()
    drive_filenames = {}
    for _file in response.get('files', []):
        drive_filenames[_file.get('name')] = _file.get('id')

    print("drive_filenames={0}".format(len(drive_filenames)))

    # only upload new files
    for _file in glob.glob(local_folder + '/*.gz'):
        filename = os.path.basename(_file)
        if filename not in drive_filenames:
            print("Upload {0}".format(filename))

            file_metadata = {
                'name': filename,
                'parents': [folder_id],
            }
            media = MediaFileUpload(_file, mimetype='application/gzip')
            file = drive_service.files().create(body=file_metadata,
                                                media_body=media,
                                                fields='id').execute()

            print("Uploaded: {0}".format(file.get('id')))
        else:
            print("{0} Exist".format(filename))


    # delete files no longer exist in local
    for _file, _id in drive_filenames.iteritems():
        print("Delete '{0}', {1}".format(_file, _id))
        drive_service.files().delete(fileId=_id).execute()

