import datetime
from argparse import ArgumentError
from dataclasses import dataclass


@dataclass
class Course:
    name: str
    location: str
    recurrence: 'Recurrence'
    start_date: datetime.datetime
    end_date: datetime.datetime

    def __hash__(self):
        h = hash(self.name) * 31
        h += hash(self.location) * 31
        h += hash(self.recurrence) * 31
        h += hash(self.start_date) * 31
        h += hash(self.end_date) * 31
        return h

    def __eq__(self, other):
        return isinstance(other, self.__class__) and \
            self.name == other.name and self.location == other.location and \
            self.recurrence == other.recurrence and self.start_date == other.start_date \
            and self.end_date == other.end_date


class Recurrence:
    def to_ical_presentation(self) -> str:
        pass

    @staticmethod
    def from_ical_presentation(ical_presentation: str) -> 'Recurrence':
        if not ical_presentation.startswith('RRULE:'):
            raise ArgumentError(message=f'Invalid ical presentation "{ical_presentation}"', argument=None)

        arguments = ical_presentation[len('RRULE:'):].split(';')
        freq = ''
        count = ''
        interval = ''
        for arg in arguments:
            name, para = arg.split('=')
            if name == 'FREQ':
                freq = para
            elif name == 'COUNT':
                count = para
            elif name == 'INTERVAL':
                interval = para

        if not freq or not count or not interval:
            raise ArgumentError(message=f'Ical "{ical_presentation}" is missing parameters', argument=None)

        if freq == 'WEEKLY':
            return WeeklyRecurrence(interval=int(interval), count=int(count))
        else:
            raise NotImplementedError(f'Unsupported frequency "{freq}"')



@dataclass
class WeeklyRecurrence(Recurrence):
    interval: int
    count: int

    def __hash__(self):
        return self.interval * 31 + self.count

    def to_ical_presentation(self) -> str:
        return f'RRULE:FREQ=WEEKLY;COUNT={self.count};INTERVAL={self.interval}'


class SourceProvider:
    def __init__(self):
        pass

    def get_courses(self) -> set[Course]:
        raise NotImplementedError("Method not implemented")
