from provider.destination.base import DestinationProvider
from provider.source.base import Course
import cache
import logging

import datetime
import google.auth.exceptions
import googleapiclient.discovery as gcp
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow


class GoogleDestinationProvider(DestinationProvider):
    def __init__(self, calendar_id: str = 'primary', credentials_file: str = './cache/google_credentials.json', token_file: str = 'google_token.json', callback_addr: str = 'localhost', callback_port: int = 24849, api_key: str = None):
        self.__calendar_id = calendar_id
        self.__credentials_file = credentials_file
        self.__callback_addr = callback_addr
        self.__callback_port = callback_port
        self.__token_file = token_file
        self.__api_key = api_key
        self.__credentials = None
        self.__service = None
        super().__init__()

    def __login(self):
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

            if not self.__service or updated:
                self.__service = gcp.build(
                    'calendar', 'v3', credentials=self.__credentials)
        else:
            self.__service = gcp.build(
                'calendar', 'v3', developerKey=self.__api_key)

    def set_courses(self, courses: list[Course]) -> list:
        if not self.__service:
            try:
                self.__login()
            except google.auth.exceptions.TransportError as e:
                logging.warning(
                    f'Google calendar failed due to network error: {e}')
                return []
            except google.auth.exceptions.RefreshError as e:
                logging.warning(f'Failed to refresh Google calendar: {e}')
                return []
            except google.auth.exceptions.GoogleAuthError as e:
                logging.warning(f'Failed to authorized Google calendar: {e}')
                return []

        try:
            events = []
            for course in courses:
                event = {
                    'summary': course.name,
                    'location': course.location,
                    'start': {
                        'dateTime': course.start_date.isoformat(),
                        'timeZone': 'Asia/Shanghai',
                    },
                    'end': {
                        'dateTime': course.end_date.isoformat(),
                        'timeZone': 'Asia/Shanghai',
                    },
                    'recurrence': [course.recurrence],
                }
                event = self.__service.events().insert(
                    calendarId=self.__calendar_id, body=event).execute()
                logging.info(
                    f'Event created! Name: {course.name}, ID: {event.get("id")}')
                events.append(event)
            return events
        except Exception as e:
            logging.error(f'Failed to set courses to Google calendar: {e}')
            return []
