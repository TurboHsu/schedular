from provider.source.base import Course

class DestinationProvider:
    def __init__(self):
        pass
    
    def set_courses(self, courses: list[Course]):
        raise NotImplementedError("Method not implemented")