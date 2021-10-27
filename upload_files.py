import pickle
import os
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.http import MediaFileUpload

# If modifying these scopes, delete the file token.pickle.
SCOPES = ['https://www.googleapis.com/auth/drive.metadata.readonly',
          'https://www.googleapis.com/auth/drive.file']


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

    return build('drive', 'v3', credentials=creds)


def upload_files(local_folder, file_name, destination_folder):
    """
    Creates a folder and upload a file to it
    """
    # authenticate account
    service = get_gdrive_service()
    # folder details we want to make
    folder_metadata = {
        "name": destination_folder,
        "mimeType": "application/vnd.google-apps.folder"
    }


    # create the folder
    response = service.files().list(q="name='{name}' and mimeType='{mimeType}'".format(name=folder_metadata['name'], mimeType=folder_metadata['mimeType'])).execute()
    # print("\n\nResponse : \n",response)
    items = response.get('files', [])

    if not items:
        # print("'{}'' not found, create new".format(folder_metadata['name']))
        file = service.files().create(body=folder_metadata,
                                            fields='id').execute()
    else:
        # print("'{}'' found".format(folder_metadata['name']))
        file = items[0]

    # get the folder id
    folder_id = file.get("id")
    # print("Folder ID:", folder_id)
    # upload a file text file
    # first, define file metadata, such as the name and the parent folder ID
    file_metadata = {
        "name": file_name,
        "parents": [folder_id]
    }
    # upload
    media = MediaFileUpload(local_folder+"/"+file_name, resumable=True)
    file = service.files().create(body=file_metadata, media_body=media, fields='id').execute()
    print("\nUploaded :  ",file_name, " ", file.get("id"))


if __name__ == '__main__':
    upload_files("local_folder", "one.jpeg", "TestFolder")