import threading


class TaskTimer:
    def __init__(self, timer_period, function):
        self.timer_period = timer_period
        self.function = function
        self.thread = threading.Timer(self.timer_period, self.handle_function)

    def handle_function(self):
        self.function()
        self.thread = threading.Timer(self.timer_period, self.handle_function)
        self.thread.start()

    def start(self):
        self.thread.start()

    def stop(self):
        self.thread.cancel()
