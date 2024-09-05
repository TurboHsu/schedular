from provider.source.base import Course

class DestinationProvider:
    def __init__(self):
        pass

    def remove_courses(self, courses: list[Course]) -> list:
        raise NotImplementedError("Method not implemented")

    def add_courses(self, courses: list[Course]):
        raise NotImplementedError("Method not implemented")