import openerplib
import ConfigParser
        

def get_server_connection(config_file):
    config = ConfigParser.RawConfigParser({'protocol' : 'xmlrpc', 'port' : 8069})
    config.read(config_file)

    hostname = config.get('Connection', 'hostname')
    database = config.get('Connection', 'database')
    login = config.get('Connection', 'login')
    password = config.get('Connection', 'password')
    protocol = config.get('Connection', 'protocol')
    port = int(config.get('Connection', 'port'))
    return openerplib.get_connection(hostname=hostname, database=database, login=login, password=password, protocol=protocol, port=port)
    
    
def get_version(config_file):
    config = ConfigParser.RawConfigParser()
    config.read(config_file)
    version = config.get('tag', 'version')
    return version
    
def get_int_list(config_file, section, parameter):
    config = ConfigParser.RawConfigParser()
    config.read(config_file)
    issues = config.get(section, parameter)
    return [int(x) for x in filter(lambda x: x, issues.split(','))]
    
#v6 compatibility
def __getattr__(self, method):
    """
    Provides proxy methods that will forward calls to the model on the remote OpenERP server.

    :param method: The method for the linked model (search, read, write, unlink, create, ...)
    """
    def proxy(*args, **kw):
        """
        :param args: A list of values for the method
        """
        self.connection.check_login(False)
        result = self.connection.get_service('object').execute(
                                                self.connection.database,
                                                self.connection.user_id,
                                                self.connection.password,
                                                self.model_name,
                                                method,
                                                *args)
        if method == "read":
            if isinstance(result, list) and len(result) > 0 and "id" in result[0]:
                index = {}
                for r in result:
                    index[r['id']] = r
                result = [index[x] for x in args[0] if x in index]
        return result
    return proxy

openerplib.Model.__getattr__ = __getattr__