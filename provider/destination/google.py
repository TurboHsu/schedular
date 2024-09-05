import logging

from provider._google import GoogleProvider, AuthorizationException
from provider.destination.base import DestinationProvider
from provider.source.base import Course


class GoogleDestinationProvider(DestinationProvider, GoogleProvider):

    def __init__(self, calendar_id: str = 'primary', credentials_file: str = './cache/google_credentials.json',
                 token_file: str = 'google_token.json', callback_addr: str = 'localhost', callback_port: int = 24849,
                 api_key: str = None):
        DestinationProvider.__init__(self)
        GoogleProvider.__init__(self, calendar_id, credentials_file, token_file, callback_addr, callback_port,
                                api_key)

    def set_courses(self, courses: list[Course]) -> list:
        try:
            self._login_or_fail()
        except AuthorizationException as e:
            logging.error(e.message, exc_info=e.base_exception)
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
                    'recurrence': [course.recurrence.to_ical_presentation()],
                }
                event = self._service.events().insert(
                    calendarId=self._calendar_id, body=event).execute()
                logging.info(
                    f'Event created! Name: {course.name}, ID: {event.get("id")}')
                events.append(event)
            return events
        except Exception as e:
            logging.error(f'Failed to set courses to Google calendar: {e}')
            return []
