import os
from googleapiclient import errors
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.http import MediaFileUpload
from google.oauth2.credentials import Credentials
from logger import get_logger

log = get_logger()

SCOPES = [
    'https://www.googleapis.com/auth/drive.appdata',
    'https://www.googleapis.com/auth/drive.file',
]

CREDENTIALS_PATH = 'base/credentials.json'
TOKEN_PATH = 'token.json'
BACKUP_MIME_TYPE = 'application/gzip'


class DriveClient:
    """Cliente reutilizable para Google Drive."""

    def __init__(self):
        self._service = None

    def _get_service(self):
        if self._service is None:
            self._service = self._build_service()
        return self._service

    def _build_service(self):
        creds = None
        if os.path.exists(TOKEN_PATH):
            creds = Credentials.from_authorized_user_file(TOKEN_PATH, SCOPES)

        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_PATH, SCOPES)
                creds = flow.run_local_server(port=0)

            with open(TOKEN_PATH, "w") as token:
                token.write(creds.to_json())

        return build('drive', 'v3', credentials=creds, cache_discovery=False, static_discovery=False)

    def _find_file(self, filename):
        """Buscar archivo por nombre. Retorna file_id o None."""
        service = self._get_service()
        log.info(f'[DRIVE] Buscando: {filename}')
        try:
            results = service.files().list(
                pageSize=10,
                fields="nextPageToken, files(id, name)",
                q=f"name='{filename}'"
            ).execute()
            items = results.get('files', [])
            if items:
                return items[0]['id']
            return None
        except errors.HttpError as error:
            log.error(f'[DRIVE] Error buscando archivo: {error}')
            return None

    def upload_or_update(self, filename, filepath, mimetype=BACKUP_MIME_TYPE):
        """Sube o actualiza un archivo en Drive. Retorna file_id o None."""
        file_id = self._find_file(filename)
        if file_id:
            return self._update_file(file_id, filepath, mimetype)
        return self._upload_file(filename, filepath, mimetype)

    def _upload_file(self, filename, filepath, mimetype):
        """Subir archivo nuevo a Drive."""
        service = self._get_service()
        log.info(f'[DRIVE] Subiendo: {filename}')
        try:
            file_metadata = {'name': filename}
            media = MediaFileUpload(filepath, mimetype=mimetype, resumable=True)
            file = service.files().create(
                body=file_metadata,
                media_body=media,
                fields='id'
            ).execute()
            file_id = file.get('id')
            log.info(f'[DRIVE] Subido: {file_id}')
            return file_id
        except errors.HttpError as error:
            log.error(f'[DRIVE] Error subiendo archivo: {error}')
            return None

    def _update_file(self, file_id, filepath, mimetype):
        """Actualizar archivo existente en Drive."""
        service = self._get_service()
        log.info(f'[DRIVE] Actualizando: {file_id}')
        try:
            media_body = MediaFileUpload(filepath, mimetype=mimetype, resumable=True)
            updated_file = service.files().update(
                fileId=file_id,
                body={},
                media_body=media_body
            ).execute()
            log.info(f'[DRIVE] Actualizado: {updated_file["id"]}')
            return updated_file['id']
        except errors.HttpError as error:
            log.error(f'[DRIVE] Error actualizando archivo: {error}')
            return None
