from datetime import datetime


class Timer:

    def __init__(self):
        self.start_time = None
        self.end_time = None

    def start_timer(self):
        self.start_time = datetime.now()

    def stop_timer(self):
        self.end_time = datetime.now()
        return (self.end_time - self.start_time)

    def duration_in_seconds(self):
        return (self.end_time - self.start_time).seconds
