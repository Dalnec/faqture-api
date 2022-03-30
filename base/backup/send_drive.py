from __future__ import print_function
import pickle
import os.path
# import pkg_resources.py2_warn
from googleapiclient import errors
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.http import MediaFileUpload
from logger import log

# If modifying these scopes, delete the file token.pickle.
SCOPES = ['https://www.googleapis.com/auth/drive'] #.metadata.readonly']

def getCredentials():
    creds = None
    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credenciales/credentials_faqture.json', SCOPES)
            creds = flow.run_local_server(port=0)
        with open('token.pickle', 'wb') as token:
            pickle.dump(creds, token)

    service = build('drive', 'v3', credentials=creds, cache_discovery=False, static_discovery=False)
    return service

def list_items():
    services = getCredentials()
    results = services.files().list(pageSize=5, 
                                    fields="nextPageToken, files(id, name)").execute()
    items = results.get('files', [])

    if not items:
        log.info('No files found.')
    else:
        log.info('Files:')
        for item in items:
            log.info(u'{0} ({1})'.format(item['name'], item['id']))

def uploadFile(filename,filepath,mimetype):
    services = getCredentials()
    log.info('Backup Uploading...')
    file_metadata = {'name': filename}
    media = MediaFileUpload(filepath, 
                            mimetype = mimetype, 
                            resumable = True) #resumable=True para enviar achivos mayores a 5MB
    file = services.files().create(body = file_metadata,
                                    media_body = media,
                                    fields='id').execute()
    return log.info('Uploaded: %s' % (file.get('id')))

def searchFile(size, query, filename):
    services = getCredentials()
    log.info('Searching File...')
    f_mT = 'application/x-rar-compressed'
    results = services.files().list(pageSize = size,
                                    fields = "nextPageToken, files(id)",
                                    q=query).execute()
    items = results.get('files', [])
    if not items:
        log.info('No files found.')        
        uploadFile(filename, filename, f_mT)
    else:
        for item in items:            
            fileId = item['id']
        updateFile(fileId, filename, f_mT)
        return item
    
def updateFile(file_id, new_filename, new_mime_type):
    services = getCredentials()
    log.info('Backup Updating...')
    try:
        file = {}
        media_body = MediaFileUpload(new_filename, 
                                    mimetype=new_mime_type, 
                                    resumable=True)
        updated_file = services.files().update(fileId=file_id,                                           
                                            body=file,
                                            media_body=media_body).execute()
        return log.info('Updated: %s' % (updated_file['id']))
    except errors.HttpError as error:
        log.error('%s An error occurred: %s' % (error)) 
        return None