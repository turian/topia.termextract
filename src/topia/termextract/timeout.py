"""
Timeout decorator
from ActiveState: http://code.activestate.com/recipes/307871-timing-out-function/
http://www.saltycrane.com/blog/2010/04/using-python-timeout-decorator-uploading-s3/
"""

import signal

class TimeoutError(Exception):
    def __init__(self, value = "Timed Out"):
        self.value = value
    def __str__(self):
        return repr(self.value)

def timeout(seconds_before_timeout):
    def decorate(f):
        def handler(signum, frame):
            raise TimeoutError()
        def new_f(*args, **kwargs):
            old = signal.signal(signal.SIGALRM, handler)
            signal.alarm(seconds_before_timeout)
            try:
                result = f(*args, **kwargs)
            finally:
                signal.signal(signal.SIGALRM, old)
            signal.alarm(0)
            return result
        new_f.func_name = f.func_name
        return new_f
    return decorate

"""
import time

@timeout(5)
def mytest():
    print "Start"
    for i in range(1,10):
        time.sleep(1)
        print "%d seconds have passed" % i

if __name__ == '__main__':
    mytest()
"""
