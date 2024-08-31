import datetime
from dataclasses import dataclass

@dataclass
class Course:
    name: str
    location: str
    recurrence: str
    last_time: datetime.timedelta
    start_date: datetime.datetime
    end_date: datetime.datetime

class SourceProvider:
    def __init__(self):
        pass
    
    def get_courses(self) -> list[Course]:
        raise NotImplementedError("Method not implemented")
