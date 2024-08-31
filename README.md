# Schedular

Its a python script to import schedules from school website to any calendar (in theory).

## Installation

Simply run the following command to install all the dependencies.

```bash
pipenv sync
```

## Usage

Just check out the example.

## Providers documentation

### Source

#### NUIST academic system

To create a instance, do this:

```python
from provider.source.nuist import NUISTSourceProvider
from datetime import datetime

source_provider = NUISTSourceProvider(
    username="", # Your student ID
    password="", # Your password
    first_school_day=datetime(2024, 9, 2), # The first day of the semester
    semester="2024-2025-1", # The semester, in the format of "year-year-semester"
    headless=True) # Set to false if u wanna see stuff happen
```

Call `source_provider.get_courses()` to get the courses.

### Destination

#### Google calendar

If you don't own an OAuth client secret file, pls check out [https://developers.google.com/calendar/api/quickstart/python#set_up_your_environment](https://developers.google.com/calendar/api/quickstart/python#set_up_your_environment) to get one.

Put it in `/cache/google_credentials.json` or any other path you like.

To create a instance, do this:

```python
from provider.destination.google import GoogleDestinationProvider

destination_provider = GoogleDestinationProvider(
        calendar_id='calendars_are_happy_to_have_an_id_i_guess@some.stuff.here') # Your calendar id, defaults to primary
```

Call `destination_provider.set_courses(courses)` to set the courses.
