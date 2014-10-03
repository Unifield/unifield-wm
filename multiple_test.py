
import single_test
import unittest2
import threading 
import time

single_test.version = 19.1


def suite():
    """
        Gather all the tests from this module in a test suite.
    """
    test_suite = unittest2.TestSuite()
    test_suite.addTest(unittest2.makeSuite(single_test.TestPullUpdate))
    return test_suite

mySuit=suite()
runner=unittest2.TextTestRunner()
start = time.time()
thread_list = []
for i in xrange(0,20):
    thread = threading.Thread(None, runner.run, None, (mySuit,))
    thread.result_file = "load_test_result_thread_%s.csv" % i
    thread.start()
    thread_list.append(thread)
    time.sleep(20)
    
for t in thread_list:
    t.join()

print "total %s" % str(time.time() - start)
