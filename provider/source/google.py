import logging
from datetime import datetime

from provider._google import GoogleProvider, AuthorizationException, google_event_to_course, RetryException
from provider.source.base import SourceProvider, Course


class GoogleSourceProvider(SourceProvider, GoogleProvider):

    def __init__(self, first_school_day: datetime, calendar_id: str = 'primary',
                 credentials_file: str = './cache/google_credentials.json',
                 token_file: str = 'google_token.json', callback_addr: str = 'localhost', callback_port: int = 24849,
                 api_key: str = None):
        SourceProvider.__init__(self)
        GoogleProvider.__init__(self, calendar_id, credentials_file, token_file, callback_addr, callback_port,
                                api_key)
        self.__first_school_day = first_school_day

    def get_courses(self) -> set[Course]:
        try:
            self._login_or_fail()
        except RetryException:
            return self.get_courses()
        except AuthorizationException as e:
            logging.error(e.message, exc_info=e.base_exception)
            return set()

        time_min = self.__first_school_day.replace(
            tzinfo=self._calendar_tz()) if self.__first_school_day.tzinfo is None else self.__first_school_day

        result = set()
        page_token = None
        while True:
            events = self._service.events().list(calendarId=self._calendar_id,
                                             timeMin=time_min.isoformat(),
                                             pageToken=page_token).execute()
            for e in events['items']:
                if 'summary' in e:
                    result.add(google_event_to_course(e))

            if 'nextPageToken' in events:
                page_token = events['nextPageToken']
            else:
                break

        return result