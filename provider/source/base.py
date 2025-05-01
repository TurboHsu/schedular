import datetime
import time
from argparse import ArgumentError
from dataclasses import dataclass
from zoneinfo import ZoneInfo


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


class ICalendarRepresentable:

    @staticmethod
    def from_ical_presentation(ical_presentation: str) -> 'ICalendarRepresentable':
        if ical_presentation.startswith('EXDATE;'):
            return Exdate.from_ical_presentation(ical_presentation)
        elif ical_presentation.startswith('RRULE:'):
            return WeeklyRecurrence.from_ical_presentation(ical_presentation)
        else:
            raise ArgumentError(message=f'Invalid ical presentation "{ical_presentation}"', argument=None)

    def to_ical_presentation(self) -> str:
        pass


class Recurrence(ICalendarRepresentable):
    def __init__(self, extra_args: ICalendarRepresentable = None):
        self.extra_args = extra_args

    def to_ical_presentation(self) -> list[str]:
        pass

    @staticmethod
    def from_ical_presentation(ical_presentation: list[str]) -> 'Recurrence':
        presentations = list(ICalendarRepresentable.from_ical_presentation(p) for p in ical_presentation)
        try:
            rule = next(p for p in presentations if isinstance(p, Recurrence))
            rule.extra_args = list(p for p in presentations if not isinstance(p, Recurrence))
            if not rule.extra_args:
                rule.extra_args = None
            return rule
        except StopIteration:
            raise IndexError('This presentation is missing recurrence definition')


@dataclass
class WeeklyRecurrence(Recurrence):
    interval: int
    count: int
    extra_args: list[ICalendarRepresentable] = None

    def __hash__(self):
        return self.interval * 31 + self.count

    @staticmethod
    def from_ical_presentation(ical_presentation: str) -> 'Recurrence':
        RRULE = 'RRULE:'
        if not ical_presentation.startswith(RRULE):
            raise ArgumentError(f"This presentation doesn't conform to Recurrence")
        arguments = ical_presentation[len(RRULE):].split(';')
        freq = ''
        count = ''
        interval = '1'
        for arg in arguments:
            name, para = arg.split('=')
            if name == 'FREQ':
                freq = para
            elif name == 'COUNT':
                count = para
            elif name == 'INTERVAL':
                interval = para

        if not freq or not count:
            raise ArgumentError(message=f'Ical "{ical_presentation}" is missing parameters', argument=None)

        if freq == 'WEEKLY':
            return WeeklyRecurrence(interval=int(interval), count=int(count))
        else:
            raise NotImplementedError(f'Unsupported frequency "{freq}"')

    def to_ical_presentation(self) -> list[str]:
        l = [f'RRULE:FREQ=WEEKLY;COUNT={self.count};INTERVAL={self.interval}']
        if self.arguments:
            for arg in self.arguments:
                l.append(arg.to_ical_presentation())
        return l


@dataclass
class Exdate(ICalendarRepresentable):
    dates: list[datetime.datetime]
    timezone_id: str = None

    @staticmethod
    def from_ical_presentation(ical_presentation: str) -> 'Exdate':
        (ext_params, time_buf) = ical_presentation[len('EXDATE'):].split(':')
        ext_params = list(pair.split('=') for pair in ext_params.split(';')[1:])
        try:
            date_only = next(value for (key, value) in ext_params if key == 'VALUE') == 'DATE'
        except StopIteration:
            date_only = False
        try:
            tzid = next(value for (key, value) in ext_params if key == 'TZID')
            tz = ZoneInfo(tzid)
        except StopIteration:
            tzid = None
            tz = None

        dates = list[datetime.datetime]()
        for t in time_buf.split(','):
            if date_only:
                ts = time.strptime(t.strip(), '%Y%m%d')
            else:
                ts = time.strptime(t.strip(), '%Y%m%dT%H%M%S')
            dates.append(datetime.datetime.fromtimestamp(time.mktime(ts), tz=tz))

        return Exdate(dates, tzid)

    def to_ical_presentation(self) -> str:
        buf = 'EXDATE'
        if self.timezone_id:
            buf += f';TZID={self.timezone_id}'
        buf += ':'
        buf += ','.join(
            f'{date.year:04d}{date.month:02d}{date.day:02d}T{date.hour:02d}{date.minute:02d}{date.second:02d}' for date
            in self.dates)
        return buf


class SourceProvider:
    def __init__(self):
        pass

    def get_courses(self) -> set[Course]:
        raise NotImplementedError("Method not implemented")
