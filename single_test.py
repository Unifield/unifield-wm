import openerplib
from conf_lib import *
import unittest2
from time import time
import csv
import sys
import threading
from datetime import datetime, date

version = 18.0


def version(vmin=None, vmax=None):
    """
        use as decorator to specify on which version the test can be executed.
        vmin: the version should be at least at vmin version to execute the test
        vmax: the version should be at most at vmax verion to execute the test
    """
    def real_decorator(function):
        def wrapper(self, *args, **kwargs):
            global version
            if vmin and vmin > version:
                raise self.skipTest(self._testMethodName)
            if vmax and vmax < version:
                raise self.skipTest(self._testMethodName)
            return function(self, *args, **kwargs)
        return wrapper
    return real_decorator

class TestPerfFramework(unittest2.TestCase): 
    
    @classmethod
    def setUpClass(self):
        self.connection = get_server_connection(self.CONFIG_FILE)
        thread = threading.currentThread()
        thread.rows = []
        
    @classmethod
    def tearDownClass(self):
        thread = threading.currentThread()
        if hasattr(thread, "result_file"):
            result_file = thread.result_file
        else:
            result_file = "load_test_result.csv"
        with open(result_file, 'a') as f:
            writer = csv.writer(f)
            for row in thread.rows:
                writer.writerow(row)
    def search_read(self, model, domain, fields=[], offset=0, limit=80, order="", context=None):
        model_obj = self.connection.get_model(model)
        ids = model_obj.search(domain, offset=offset, limit=limit, order=order, context=context)
        if limit and len(ids) == limit:
            length = model_obj.search_count(domain, context=context)
        else:
            length = len(ids) + (offset or 0)
        records = model_obj.read(ids, fields, context=context)
        records.sort(key=lambda obj: ids.index(obj['id']))
        return records, length
    
    def start_time(self):
        self._st = time()
        
    def print_time(self):
        print "%s - %s\t%s" % (self.__class__.__name__, self._testMethodName, time() - self._st)
        thread = threading.currentThread()
        thread.rows.append([self.__class__.__name__, self._testMethodName, time() - self._st])
    
    
    def setUp(self):
        self.start_time()

    def tearDown(self):
        self.print_time()
        
class TestPullUpdate(TestPerfFramework):
    
    @classmethod
    def setUpClass(self):
        self.CONFIG_FILE = "connection.conf"
        self.uuid = "7b939730-da91-11e3-ba4d-9c8e99deb5bd"
        self.hw_id = '56546545665794'
        self.packet_size = 500
        super(TestPullUpdate, self).setUpClass()
        
    def test_get_update(self):
        sync_server = self.connection.get_model("sync.server.sync_manager")
        _, max_seq, _ =  sync_server.get_max_sequence(self.uuid, self.hw_id)
        print "%s MB" % sync_server.get_memory_usage()
        stop_flag = False
        offset = 0
        while not stop_flag:
            res = sync_server.get_update(self.uuid, self.hw_id, 1, offset, self.packet_size, max_seq)
            #print "%s MB" % sync_server.get_memory_usage()
            stop_flag = res[2]
            if stop_flag:
                break
            offset += res[1]['offset']
            #sync_server.save_puller()
            print "%s MB" % sync_server.get_memory_usage()
            
            

   
if __name__ == '__main__':
    arg1 = sys.argv[1]
    sys.argv.remove(arg1)
    version = float(arg1)
    
    unittest2.main()

