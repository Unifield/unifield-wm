from unittest import *

import unittest
import types
import sys
import os

from .case import (TestCase, FunctionTestCase, SkipTest, skip, skipIf,
                   skipUnless, expectedFailure)
from .signals import installHandler
import loader
import runner

import pdb

def __init27__(self, module='__main__', defaultTest=None, argv=None,
                testRunner=None, testLoader=loader.defaultTestLoader,
                exit=True, verbosity=1, failfast=None, catchbreak=None,
                buffer=None):
    if isinstance(module, basestring):
        self.module = __import__(module)
        for part in module.split('.')[1:]:
            self.module = getattr(self.module, part)
    else:
        self.module = module
    if argv is None:
        argv = sys.argv

    self.exit = exit
    self.failfast = failfast
    self.catchbreak = catchbreak
    self.verbosity = verbosity
    self.buffer = buffer
    self.defaultTest = defaultTest
    self.testRunner = testRunner
    self.testLoader = testLoader
    self.progName = os.path.basename(argv[0])
    self.parseArgs(argv)
    self.runTests()

unittest.TestProgram.__init__ = __init27__

def runTests27(self):
    if self.catchbreak:
        installHandler()
    if self.testRunner is None:
        self.testRunner = runner.TextTestRunner
    if isinstance(self.testRunner, (type, types.ClassType)):
        try:
            testRunner = self.testRunner(verbosity=self.verbosity,
                                         failfast=self.failfast,
                                         buffer=self.buffer)
        except TypeError:
            # didn't accept the verbosity, buffer or failfast arguments
            testRunner = self.testRunner()
    else:
        # it is assumed to be a TestRunner instance
        testRunner = self.testRunner
    self.result = testRunner.run(self.test)
    if self.exit:
        sys.exit(not self.result.wasSuccessful())

unittest.TestProgram.runTests = runTests27

