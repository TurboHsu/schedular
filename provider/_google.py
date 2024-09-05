import google.auth.exceptions as ge
import googleapiclient.discovery as gcp
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow

import cache


class AuthorizationException(Exception):
    def __init__(self, message: str, base_exception: Exception):
        super().__init__(message, base_exception)
        self.message = message
        self.base_exception = base_exception


class GoogleProvider:
    def __init__(self, calendar_id: str = 'primary', credentials_file: str = './cache/google_credentials.json',
                 token_file: str = 'google_token.json', callback_addr: str = 'localhost', callback_port: int = 24849,
                 api_key: str = None):
        self._calendar_id = calendar_id
        self.__credentials_file = credentials_file
        self.__callback_addr = callback_addr
        self.__callback_port = callback_port
        self.__token_file = token_file
        self.__api_key = api_key
        self.__credentials = None
        self._service = None

    def _login_or_fail(self):
        if not self._service:
            try:
                self._login()
            except ge.TransportError as e:
                raise AuthorizationException(
                    'Google calendar failed due to network error', e)
            except ge.RefreshError as e:
                raise AuthorizationException('Failed to refresh Google calendar', e)
            except ge.GoogleAuthError as e:
                raise AuthorizationException('Failed to authorized Google calendar', e)

    def _login(self):
        if self.__api_key is None:
            if cache.exists(self.__token_file):
                self.__credentials = Credentials.from_authorized_user_file(
                    cache.get_file(self.__token_file))

            updated = False
            if not self.__credentials or not self.__credentials.valid:
                updated = True
                if self.__credentials and self.__credentials.expired and self.__credentials.refresh_token:
                    self.__credentials.refresh(Request())
                else:
                    scope = ['https://www.googleapis.com/auth/calendar']
                    flow = InstalledAppFlow.from_client_secrets_file(
                        self.__credentials_file, scope)
                    self.__credentials = flow.run_local_server(
                        bind_addr=self.__callback_addr, port=self.__callback_port)
                    with cache.open_cache(self.__token_file, 'w') as token:
                        token.write(self.__credentials.to_json())

            if not self._service or updated:
                self._service = gcp.build(
                    'calendar', 'v3', credentials=self.__credentials)
        else:
            self._service = gcp.build(
                'calendar', 'v3', developerKey=self.__api_key)
