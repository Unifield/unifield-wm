from os import path
import sys, traceback, re
from sys import stdout, stderr
from xmlrpclib import Fault, ProtocolError


## Continue raising exception
def raise_error():
    raise sys.exc_info()[0], sys.exc_info()[1]


## Make a test
class test(object):
    def __init__(self):
        self.reset()

    def __init__(self, name=None):
        if name != None: self.name = name
        self.reset()

    def next(self):
        if self.step == 'finally': return False
        next_possibilities = ['finally']
        if not self.failure():
            if self.next_step != None:
                next_possibilities.insert(0, self.next_step)
                self.next_step = None
            elif self.step == None:
                next_possibilities[:0] = [0, 1]
            elif isinstance(self.step, int):
                next_possibilities[:0] = [self.step + 1, 'finally']
        for step in next_possibilities:
            foo = "step_"+str(step)
            if hasattr(self, foo):
                self.step = step
                return True
        return False

    def reset(self):
        self.status = 'not-executed'
        self.step = None
        self.next_step = None
        self.reason = None
        self.traceback = None

    def failed(self, reason):
        self.status, self.reason = 'failed', reason
        self.fail_step = self.step

    def success(self):
        self.step = 0
        self.status = 'success'

    def failure(self):
        return self.status == 'failed'

    def execute(self):
        try:
            foo = getattr(self, "step_"+str(self.step))
        except:
            if self.step not in (0, 'finally', ): raise Exception, "Cannot find step `"+str(self.step)+"'!"
        else:
            if self.step == 'finally':
                try:
                    self.step_finally()
                except:
                    stderr.write("Warning: finally process failed.\n")
            else:
                self.status = 'execution'
                try:
                    self.next_step = foo()
                except Fault, e:
                    self.traceback = "\n".join(traceback.format_exc().splitlines()[0:-1]) + "\n" + e.faultString
                    self.failed('Fault: '+str(e.faultCode))
                ## TODO not tested
                except ProtocolError, e:
                    self.traceback = "\n".join(traceback.format_exc().splitlines()[0:-1]) + "\n" + e.faultString
                    self.failed('ProtocolError: %s: %s' % (e.errcode, e.errmsg,))
                except:
                    e, msg = sys.exc_info()[0].__name__, str(sys.exc_info()[1])
                    self.traceback = traceback.format_exc()
                    self.failed(e+(": "+msg if msg else ''))

    def run(self):
        stdout.write(self.name)
        stdout.flush()
        while self.next():
            self.execute()
            if not self.failure():
                stdout.write('.')
                stdout.flush()
        if not self.failure():
            stdout.write('pass\n')
            stdout.flush()
            self.success()
        else:
            stdout.write('fail ('+str(self.fail_step)+'/)\n')


## Make a serie of tests
class serie(test):
    def __init__(self):
        self.reset()

    def reset(self):
        self.step = None
        self.status = 'not-executed'
        self.reason = None
        self.traceback = None
        _temp = __import__(self.__module__, globals(), locals(), self.tests, -1)
        if not hasattr(self, 'classes'):
            self.classes = self.tests
        self.tests = [getattr(_temp, t)() for t in self.classes]
        self.it = iter(self.tests)

    def run(self):
        self.status = 'execution'
        stdout.write(self.name+'...\n')
        try:
            while True:
                self.execute()
        except StopIteration:
            if not self.failure():
                self.success()
        stdout.write(self.name+' ended.\n')

    def execute(self):
        foo = self.it.next()
        foo.run()
        if foo.failure():
            self.traceback = foo.traceback
            self.failed("Serie Test failure on test: "+foo.name+': '+(foo.reason or 'Unknown'))
            raise StopIteration


################################################################################
##
##  tests
##
##################
if __name__ == '__main__':
    class example(test):
        name = "My new test"

        def step_1(self):
            globals()['a'] = False

        def step_2(self):
            pass

        def step_3(self):
            pass
            raise StandardError

        def step_finally(self):
            #raise Exception
            globals()['a'] = True

    class myserie(serie):
        name = "My Test Serie"
        tests = ['example']

    s = myserie()

    s.run()
    if s.failure(): print s.reason

    print a

