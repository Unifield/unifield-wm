#!/usr/bin/env python

import re
import sys
import functools
import xmlrpclib


def catch_xmlrpc_errors(func):
    @functools.wraps(func)
    def wrapper(self, *a, **kw):
        try:
            return func(self, *a, **kw)
        except xmlrpclib.Fault, exc:
            # TODO retrieve the original stack
            if 'Traceback' in exc.faultString:
                _, _, traceback = sys.exc_info()
                raise Exception("XML-RPC call failed!\n" +
                        exc.faultString + "\nXML-RPC call failed!"), \
                    None, traceback
            raise
    return wrapper


def synchronize_rules(url, master, instances,
        clean_updates=False, clean_messages=False):
    proxy = xmlrpclib.ServerProxy(url + '/object')


    @catch_xmlrpc_errors
    def execute(instance, *args):
        return proxy.execute(instance, 1, 'admin', *args)


    def update_update_rules(instance, uuid, clean=False):
        # extract packet from master
        update_rules = execute(master, 'sync.server.sync_manager',
                               'get_model_to_sync', uuid)[1]

        # import packet on instance
        execute(instance, 'sync.client.rule', 'save', update_rules)

        if clean:
            for basename in ('sync.client', 'sync_remote_warehouse'):
                # mark all updates received as ran
                execute(instance, basename + '.update_received',
                    'write',
                    execute(instance, basename + '.update_received',
                            'search', [('run', '=', False)]),
                    {'run': True})

                # mark all updates to send as sent
                execute(instance, basename + '.update_to_send',
                    'write',
                    execute(instance, basename + '.update_to_send',
                            'search', [('sent', '=', False)]),
                    {'sent': True})


    def update_message_rules(instance, uuid, clean=False):
        # extract packet from master
        message_rules = execute(master, 'sync.server.sync_manager',
                                'get_message_rule', uuid)[1]

        # import packet on instance
        execute(instance, 'sync.client.message_rule', 'save', message_rules)

        if clean:
            for basename in ('sync.client', 'sync_remote_warehouse'):
                # mark all messages received as ran
                execute(instance, basename + '.message_received',
                    'write',
                    execute(instance, basename + '.message_received',
                            'search', [('run', '=', False)]),
                    {'run': True})

                # mark all messages to send as sent
                execute(instance,  basename + '.message_to_send',
                    'write',
                    execute(instance, basename + '.message_to_send',
                            'search', [('sent', '=', False)]),
                    {'sent': True})


    for instance in instances:
        # guess probable name
        matches = re.match(r"^([^-_]+[-_])?(.+?)(_RW)?$", instance)
        name = matches.group(2) if matches else instance

        # find UUID
        instance_ids = execute(master, 'sync.server.entity',
                               'search', [('name', '=', name)])
        assert instance_ids, "can not find instance %s" % name
        uuid = execute(master, 'sync.server.entity',
                       'read', instance_ids[0], ['identifier'])\
               ['identifier']

        update_update_rules(instance, uuid, clean=clean_updates)
        update_message_rules(instance, uuid, clean=clean_messages)


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--clean-updates', action='store_true', default=False)
    parser.add_argument('--clean-messages', action='store_true', default=False)
    parser.add_argument('url')
    parser.add_argument('master')
    parser.add_argument('instances', nargs='+')
    opt = parser.parse_args()

    synchronize_rules(opt.url, opt.master, opt.instances,
                      clean_updates=opt.clean_updates,
                      clean_messages=opt.clean_messages)
