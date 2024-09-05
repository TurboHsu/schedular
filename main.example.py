import datetime
import logging

from provider.destination.google import GoogleDestinationProvider
from provider.source.google import GoogleSourceProvider
from provider.source.nuist import NUISTSourceProvider

logging.basicConfig(level=logging.INFO)

calendar_id = 'calendars_are_happy_to_have_an_id_i_guess@some.stuff.her'
first_school_day = datetime.datetime(2024, 9, 2)  # MUST be the first day of semester
source_provider = NUISTSourceProvider(
    username="1145141919810",
    password="Why do people attend class? Why do people have life?",
    first_school_day=first_school_day,
    semester="2024-2025-1",  # MUST be the semester you want to fetch
    headless=True)  # Set to false if u wanna see stuff happen

if __name__ == '__main__':
    destination_provider = GoogleDestinationProvider(calendar_id)
    gs_provider = GoogleSourceProvider(first_school_day=first_school_day, calendar_id=calendar_id)

    nuist_course = source_provider.get_courses()
    gc_course = gs_provider.get_courses()

    addition = nuist_course - gc_course
    removal = gc_course - nuist_course

    if addition:
        print('+', *(e.name for e in addition))
    if removal:
        print('-', *(e.name for e in removal))

    if not addition and not removal:
        print("Today there's nothing to do.")
    else:
        accept = input('Do you accept these changes? (y/N)')
        if accept == 'y':
            destination_provider.remove_courses(list(removal))
            destination_provider.add_courses(list(addition))
