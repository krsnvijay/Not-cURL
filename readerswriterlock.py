from contextlib import contextmanager
from threading import Lock


# Readers-Writer lock with two mutexes,
# Source https://en.wikipedia.org/wiki/Readers%E2%80%93writer_lock
class ReadersWriterLock(object):

    def __init__(self):
        self.g = Lock()
        self.r = Lock()
        self.b = 0

    def begin_read(self):
        self.r.acquire()
        self.b += 1
        if self.b == 1:
            self.g.acquire()
        self.r.release()

    def end_read(self):
        assert self.b > 0
        self.r.acquire()
        self.b -= 1
        if self.b == 0:
            self.g.release()
        self.r.release()

    @contextmanager
    def readers_locked(self):
        try:
            self.begin_read()
            yield
        finally:
            self.end_read()

    def begin_write(self):
        self.g.acquire()

    def end_write(self):
        self.g.release()

    @contextmanager
    def writer_locked(self):
        try:
            self.begin_write()
            yield
        finally:
            self.end_write()
