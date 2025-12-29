import os
import io
import pandas as pd
from datetime import datetime
from flask import current_app, request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload

class GoogleDriveService:
    """
    Google Drive integration for importing Clue data
    """

    SCOPES = [
        'https://www.googleapis.com/auth/drive.readonly',
        'https://www.googleapis.com/auth/drive.metadata.readonly'
    ]

    def __init__(self):
        self.client_id = current_app.config.get('GOOGLE_DRIVE_CLIENT_ID')
        self.client_secret = current_app.config.get('GOOGLE_DRIVE_CLIENT_SECRET')
        self.redirect_uri = current_app.config.get('GOOGLE_DRIVE_REDIRECT_URI')

    def get_authorization_url(self, user_id):
        """Generate Google Drive OAuth authorization URL"""
        if not all([self.client_id, self.client_secret, self.redirect_uri]):
            return None

        # Dynamically determine redirect URI based on request origin
        base_url = request.host_url.rstrip('/')
        if 'railway.app' in base_url:
            redirect_uri = 'https://web-production-3e53e.up.railway.app/api/auth/google-drive/callback'
        elif 'healthtracker.ozayn.com' in base_url:
            redirect_uri = 'https://healthtracker.ozayn.com/api/auth/google-drive/callback'
        else:
            redirect_uri = self.redirect_uri or current_app.config.get('GOOGLE_REDIRECT_URI')

        flow = Flow.from_client_config(
            {
                "web": {
                    "client_id": self.client_id,
                    "client_secret": self.client_secret,
                    "redirect_uris": [redirect_uri],
                    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                    "token_uri": "https://oauth2.googleapis.com/token"
                }
            },
            scopes=self.SCOPES,
            redirect_uri=redirect_uri
        )

        authorization_url, state = flow.authorization_url(
            access_type='offline',
            include_granted_scopes='true',
            state=str(user_id)
        )

        return authorization_url

    def exchange_code_for_token(self, code):
        """Exchange authorization code for access token"""
        base_url = request.host_url.rstrip('/')
        if 'railway.app' in base_url:
            redirect_uri = 'https://web-production-3e53e.up.railway.app/api/auth/google-drive/callback'
        elif 'healthtracker.ozayn.com' in base_url:
            redirect_uri = 'https://healthtracker.ozayn.com/api/auth/google-drive/callback'
        else:
            redirect_uri = self.redirect_uri or current_app.config.get('GOOGLE_REDIRECT_URI')

        flow = Flow.from_client_config(
            {
                "web": {
                    "client_id": self.client_id,
                    "client_secret": self.client_secret,
                    "redirect_uris": [redirect_uri],
                    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                    "token_uri": "https://oauth2.googleapis.com/token"
                }
            },
            scopes=self.SCOPES,
            redirect_uri=redirect_uri
        )

        flow.fetch_token(code=code)
        credentials = flow.credentials

        return {
            'access_token': credentials.token,
            'refresh_token': credentials.refresh_token,
            'expires_at': credentials.expiry.isoformat() if credentials.expiry else None,
            'token_type': 'Bearer'
        }

    def get_drive_service(self, access_token, refresh_token=None):
        """Get authenticated Google Drive service"""
        credentials = Credentials(
            token=access_token,
            refresh_token=refresh_token,
            token_uri='https://oauth2.googleapis.com/token',
            client_id=self.client_id,
            client_secret=self.client_secret,
            scopes=self.SCOPES
        )

        # Refresh token if expired
        if credentials.expired and credentials.refresh_token:
            credentials.refresh(Request())

        return build('drive', 'v3', credentials=credentials)

    def find_clue_folder(self, service):
        """Find the HealthTrackerData/Apps/Clue folder in Google Drive"""
        try:
            # Search for the Clue folder in the expected path
            query = "name='Clue' and mimeType='application/vnd.google-apps.folder' and trashed=false"
            results = service.files().list(
                q=query,
                spaces='drive',
                fields='files(id, name, parents)',
                pageSize=100
            ).execute()

            files = results.get('files', [])

            # Look for the Clue folder that's inside HealthTrackerData/Apps/
            for file in files:
                if self._is_clue_folder_in_correct_path(service, file['id']):
                    return file['id']

            return None

        except Exception as e:
            print(f"Error finding Clue folder: {str(e)}")
            return None

    def _is_clue_folder_in_correct_path(self, service, folder_id):
        """Check if the Clue folder is in the correct path: HealthTrackerData/Apps/Clue"""
        try:
            # Get folder path by walking up the hierarchy
            path_parts = []
            current_id = folder_id

            while current_id:
                # Get folder metadata
                file_info = service.files().get(
                    fileId=current_id,
                    fields='name, parents'
                ).execute()

                path_parts.insert(0, file_info['name'])

                # Check if we've reached the expected path
                if len(path_parts) >= 3:
                    if path_parts[-3:] == ['HealthTrackerData', 'Apps', 'Clue']:
                        return True

                # Move up to parent
                parents = file_info.get('parents', [])
                if not parents:
                    break
                current_id = parents[0]

            return False

        except Exception as e:
            print(f"Error checking folder path: {str(e)}")
            return False

    def list_clue_files(self, service, folder_id):
        """List all files in the Clue folder and subfolders"""
        all_files = []

        try:
            # Get all items in the Clue folder (files and subfolders)
            results = service.files().list(
                q=f"'{folder_id}' in parents and trashed=false",
                spaces='drive',
                fields='files(id, name, mimeType, modifiedTime)',
                orderBy='modifiedTime desc'
            ).execute()

            items = results.get('files', [])

            for item in items:
                if item['mimeType'] == 'application/vnd.google-apps.folder':
                    # This is a subfolder (like ClueDataDownload-2024-01-15)
                    print(f"Found subfolder: {item['name']}")
                    # Recursively get files from this subfolder
                    subfolder_files = self._list_files_recursive(service, item['id'])
                    all_files.extend(subfolder_files)
                else:
                    # This is a file
                    all_files.append(item)

            return all_files
        except Exception as e:
            print(f"Error listing Clue files: {str(e)}")
            return []

    def _list_files_recursive(self, service, folder_id, max_depth=3, current_depth=0):
        """Recursively list files in a folder (to handle nested ClueDataDownload folders)"""
        files = []

        if current_depth >= max_depth:
            return files

        try:
            results = service.files().list(
                q=f"'{folder_id}' in parents and trashed=false",
                spaces='drive',
                fields='files(id, name, mimeType, modifiedTime)',
                orderBy='modifiedTime desc'
            ).execute()

            items = results.get('files', [])

            for item in items:
                if item['mimeType'] == 'application/vnd.google-apps.folder':
                    # Recursively search subfolders
                    subfolder_files = self._list_files_recursive(service, item['id'], max_depth, current_depth + 1)
                    files.extend(subfolder_files)
                else:
                    # This is a file - add folder path to filename for context
                    item['folder_path'] = self._get_folder_path(service, folder_id)
                    files.append(item)

            return files
        except Exception as e:
            print(f"Error in recursive file listing: {str(e)}")
            return files

    def _get_folder_path(self, service, folder_id):
        """Get the full path of a folder for context"""
        try:
            folder = service.files().get(fileId=folder_id, fields='name,parents').execute()
            path_parts = [folder['name']]

            # Walk up the hierarchy to build full path
            current_id = folder.get('parents', [None])[0]
            while current_id:
                try:
                    parent = service.files().get(fileId=current_id, fields='name,parents').execute()
                    path_parts.insert(0, parent['name'])
                    current_id = parent.get('parents', [None])[0]
                except:
                    break

            return '/'.join(path_parts)
        except Exception as e:
            print(f"Error getting folder path: {str(e)}")
            return "Unknown"

    def download_and_parse_clue_file(self, service, file_id, filename):
        """Download and parse a Clue data file"""
        try:
            # Download file
            request = service.files().get_media(fileId=file_id)
            file_data = io.BytesIO()
            downloader = MediaIoBaseDownload(file_data, request)

            done = False
            while done is False:
                status, done = downloader.next_chunk()

            file_data.seek(0)

            # Parse based on file type
            if filename.endswith('.csv'):
                df = pd.read_csv(file_data)
            elif filename.endswith('.json'):
                # Handle JSON files if needed
                pass
            else:
                return None

            return df

        except Exception as e:
            print(f"Error downloading/parsing file {filename}: {str(e)}")
            return None

    def parse_clue_cycle_data(self, df):
        """Parse Clue cycle data from DataFrame"""
        parsed_data = {
            'cycles': [],
            'symptoms': [],
            'moods': []
        }

        try:
            # Clue data typically has columns like:
            # date, cycle_day, is_period, symptoms, mood, etc.

            for _, row in df.iterrows():
                date_str = row.get('date') or row.get('Date')
                if not date_str:
                    continue

                # Parse date
                try:
                    if isinstance(date_str, str):
                        date = datetime.fromisoformat(date_str.replace('Z', '+00:00')).date()
                    else:
                        date = date_str.date()
                except:
                    continue

                cycle_data = {'date': date}

                # Cycle day
                if 'cycle_day' in row and pd.notna(row['cycle_day']):
                    cycle_data['cycle_day'] = int(row['cycle_day'])
                    parsed_data['cycles'].append(cycle_data)

                # Period
                if 'is_period' in row and row['is_period']:
                    cycle_data['is_period'] = True

                # Symptoms (could be comma-separated or individual columns)
                if 'symptoms' in row and pd.notna(row['symptoms']):
                    symptoms = str(row['symptoms']).split(',')
                    for symptom in symptoms:
                        parsed_data['symptoms'].append({
                            'date': date,
                            'symptom': symptom.strip()
                        })

                # Mood
                if 'mood' in row and pd.notna(row['mood']):
                    parsed_data['moods'].append({
                        'date': date,
                        'mood': row['mood']
                    })

        except Exception as e:
            print(f"Error parsing Clue data: {str(e)}")

        return parsed_data
