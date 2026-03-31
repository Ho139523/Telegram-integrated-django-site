import time


class CircuitBreaker:

    def __init__(self):
        self.failures = 0
        self.last_failure_time = None

    def allow_request(self):

        if self.failures >= 5:

            if time.time() - self.last_failure_time < 60:
                return False

            self.failures = 0

        return True

    def record_failure(self):
        self.failures += 1
        self.last_failure_time = time.time()

