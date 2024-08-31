from provider.source.nuist import NUISTSourceProvider
from provider.destination.google import GoogleDestinationProvider
import logging
import datetime

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    first_school_day = datetime.datetime(2024, 9, 2) # MUST be the first day of semester
    source_provider = NUISTSourceProvider(
        username="1145141919810",
        password="Why do people attend class? Why do people have life?",
        first_school_day=first_school_day,
        semester="2024-2025-1", # MUST be the semester you want to fetch
        headless=True) # Set to false if u wanna see stuff happen
    courses = source_provider.get_courses()

    destination_provider = GoogleDestinationProvider(
        calendar_id='calendars_are_happy_to_have_an_id_i_guess@some.stuff.here')
    destination_provider.set_courses(courses)
