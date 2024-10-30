import logging

from provider._google import GoogleProvider, AuthorizationException, google_event_to_course, RetryException
from provider.destination.base import DestinationProvider
from provider.source.base import Course


class GoogleDestinationProvider(DestinationProvider, GoogleProvider):

    def __init__(self, calendar_id: str = 'primary', credentials_file: str = './cache/google_credentials.json',
                 token_file: str = 'google_token.json', callback_addr: str = 'localhost', callback_port: int = 24849,
                 api_key: str = None):
        DestinationProvider.__init__(self)
        GoogleProvider.__init__(self, calendar_id, credentials_file, token_file, callback_addr, callback_port,
                                api_key)

    def remove_courses(self, courses: list[Course]) -> list:
        try:
            self._login_or_fail()
        except RetryException:
            return self.remove_courses(courses)
        except AuthorizationException as e:
            logging.error(e.message, exc_info=e.base_exception)
            return []
        if len(courses) <= 0:
            return []

        earliest_day = courses[0].start_date
        for course in courses[1:]:
            if course.start_date < earliest_day:
                earliest_day = course.start_date

        time_min = earliest_day.replace(tzinfo=self._calendar_tz()) if earliest_day.tzinfo is None else earliest_day
        events = self._service.events().list(calendarId=self._calendar_id, timeMin=time_min.isoformat()).execute()

        course_remaining = list(courses)
        events_removal = []
        for event in events['items']:
            if 'summary' not in event:
                continue
            for course in courses:
                if course.name != event['summary'] or google_event_to_course(event) != course:
                    continue

                course_remaining.remove(course)
                events_removal.append(event)

        if course_remaining:
            raise LookupError(f'{', '.join(c.name for c in course_remaining)} are not available in calendar')

        events_service = self._service.events()
        for event in events_removal:
            events_service.delete(calendarId=self._calendar_id, eventId=event['id']).execute()
            logging.info(f'Event removed. Name: {event['summary']}, ID: {event['id']}')

        return events_removal

    def add_courses(self, courses: list[Course]) -> list:
        try:
            self._login_or_fail()
        except RetryException:
            return self.add_courses(courses)
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
                }
                if course.recurrence:
                    event['recurrence'] = [course.recurrence.to_ical_presentation()]

                event = self._service.events().insert(
                    calendarId=self._calendar_id, body=event).execute()
                logging.info(
                    f'Event created! Name: {course.name}, ID: {event.get("id")}')
                events.append(event)
            return events
        except Exception as e:
            logging.error(f'Failed to set courses to Google calendar: {e}')
            return []
