#!/usr/bin/env python
# -*- coding: utf8 -*-
"""
.. module:: unifield_test
   :platform: Unix
   :synopsis: Class used for all other tests in Unifield.

.. moduleauthor:: Quentin THEURET <qt@tempo-consulting.fr>

"""
from __future__ import print_function
import unittest
from connection import XMLRPCConnection as XMLConn
from connection import UnifieldTestConfigParser
from colors import TerminalColors
from random import randrange, choice, randint
from datetime import datetime, timedelta
from time import strftime

class UnifieldTest(unittest.TestCase):
    '''
    Main test class for Unifield tests using TestCase and Openerplib as main inheritance
    @var sync: contains Synchro Server oerplib connection
    @var hq1: same as sync for HQ1 DB
    @var c1: same as sync for HQ1C1 DB
    @var p1: same as sync for HQ1C1P1 DB
    @var db: contains the list of DB connections
    @var test_module_name: name of the module used to create extended table for tests
    @var test_module_obj_name: name of the OpenERP object to use to access to extended table
    '''
    # global variable
    db = {}
    test_module_name = 'unifield_tests'
    test_module_obj_name = 'unifield.test'
    already_loaded = False

    # FIXME/TODO: Make unittest.TestCase inherit from oerplib.error class because of RPCError that could be raised by unittest.TestCase

    def _addConnection(self, db_suffix, name):
        '''
        Add new connection
        '''
        con = XMLConn(db_suffix)
        setattr(self, name, con)
        self.db[name] = con
        # Set colors
        colors = self.colors
        database_display = colors.BRed + '[' + colors.Color_Off + name.center(6) + colors.BRed + ']' + colors.Color_Off
        self.db[name].colored_name = database_display

    def _hook_db_process(self, name, database):
        '''
        Some process to do for each database (except SYNC DB)
        '''
        return True

    def __init__(self, *args, **kwargs):
        # Default behaviour
        super(UnifieldTest, self).__init__(*args, **kwargs)
        # Prepare some values
        c = UnifieldTestConfigParser()
        self.config = c.read()
        tempo_mkdb = c.getboolean('DB', 'tempo_mkdb')
        db_suffixes = ['SYNC_SERVER', 'HQ1', 'HQ1C1', 'HQ1C1P1']
        names = ['sync', 'hq1', 'c1', 'p1']
        if not tempo_mkdb:
            db_suffixes = ['SYNC_SERVER', 'HQ_01', 'COORDO_01', 'PROJECT_01']
        # Check Remote warehouse and complete old params
        remote_warehouse = c.get('DB', 'RW') or False
        self.is_remote_warehouse = False
        if remote_warehouse:
            self.is_remote_warehouse = True
        self.is_remote_warehouse = False
        # Other values
        colors = TerminalColors()
        self.colors = colors
        # Keep each database connection
        for db_tuple in zip(db_suffixes, names):
            self._addConnection(db_tuple[0], db_tuple[1])
        # Add remote warehouse
        if remote_warehouse:
            self._addConnection(remote_warehouse, 'rw')
        # For each database, check that unifield_tests module is loaded
        #+ If not, load it.
        #+ Except if the database is sync one
        if UnifieldTest.already_loaded:
            return
        for database_name in self.db:
            if database_name == 'sync':
                continue
            database = self.db.get(database_name)
            module_obj = database.get('ir.module.module')
            m_ids = module_obj.search([('name', '=', self.test_module_name)])
            database_display = database.colored_name
            for module in module_obj.read(m_ids, ['state']):
                state = module.get('state', '')
                if state == 'uninstalled':
                    print (database_display + ' [' + colors.BYellow + 'UP'.center(4) + colors.Color_Off + '] Module %s' % (self.test_module_name))
                    module_obj.button_install([module.get('id')])
                    database.get('base.module.upgrade').upgrade_module([])
                elif state in ['to upgrade', 'to install']:
                    print (database_display + ' [' + colors.BYellow + 'UP'.center(4) + colors.Color_Off + '] Module %s' % (self.test_module_name))
                    database.get('base.module.upgrade').upgrade_module([])
                elif state in ['installed']:
                    print (database_display + ' [' + colors.BGreen + 'OK'.center(4) + colors.Color_Off + '] Module %s' % (self.test_module_name))
                    pass
                else:
                    raise EnvironmentError(' Wrong module state: %s' % (state or '',))
            # Some processes after instanciation for this database
            self._hook_db_process(database_name, database)
        UnifieldTest.already_loaded = True

    def is_keyword_present(self, db, keyword):
        '''
        Check that the given keyword is present in given db connection and active.
        '''
        res = False
        if not db or not keyword:
            return res
        t_obj = db.get(self.test_module_obj_name)
        t_ids = t_obj.search([('name', '=', keyword), ('active', '=', True)])
        if not t_ids:
            return res
        return True

    def get_record(self, db, object_ref, module=None):
        '''
        Returns the object created by the test files.

        :param db: Connection to the database
        :param object_ref: XML ID of the object to find

        :return The ID of the object given in object_ref
        :rtype integer or False
        '''
        # Object
        data_obj = db.get('ir.model.data')

        if module is None:
            module = self.test_module_name

        obj = data_obj.get_object_reference(module, object_ref)

        if obj:
            return obj[1]

        return False

    def synchronize(self, db=None):
        '''
        Connect the 'db' database to the sync. server and run  synchronization.
        If no database givent in parameters, sync. all databases.
        :param db: DB connection to synchronize (can be None or a list).
        :return: True
        '''
        if not db:
            for db_conn in self.db:
                self.synchronize(db=db_conn)

        if db and isinstance(db, list):
            for db_conn in db:
                self.synchronize(db=db_conn)

        conn_obj = db.get('sync.client.sync_server_connection')
        sync_obj = db.get('sync.client.sync_manager')

        conn_ids = conn_obj.search([])
        conn_obj.action_connect(conn_ids)
        sync_ids = sync_obj.search([])
        sync_obj.sync(sync_ids)

    def get_db_partner_name(self, db):
        '''
        Return the name of partner associated to the company of the database.
        :param db: DB connection of which we get the partner.
        :return: Name of the partner associated to the company of the database.
        '''
        company_obj = db.get('res.company')

        company_ids = company_obj.search([])
        return company_obj.browse(company_ids[0]).partner_id.name

    def random_date(self, start, end):
        """Take a random date between the first date (start) and the second one (stop).
        This method was taken from http://stackoverflow.com/questions/553303/generate-a-random-date-between-two-other-dates"""
        delta = end - start
        int_delta = (delta.days * 24 * 60 * 60) + delta.seconds
        random_second = randrange(int_delta)
        return (start + timedelta(seconds=random_second))

    def random_word(self):
        """Give a random word using a dictionnary containing a lot of french words"""
        f = 'french_words.txt'
        WORDS = open(f).read().splitlines()
        return choice(WORDS)

    def generate_analytic_distribution(self, db, record=False, write=False):
        """Create an analytic distribution and return its ID.
        :param db: DB connection to fetch data
        :param record: Browse record of the object on which we want a generic analytic distribution. If False, give a default analytic distribution.
        :param write: If True, attempt to write the analytic distribution result to the given object. It only works if you give a record!
        :return: analytic distribution ID (or False if failed)
        """
        # TODO: Add a new attribute "account" that permit to only return a compatible distribution on this account (account.account)
        # Prepare some value
        res = False
        company_obj = db.get('res.company')
        company_ids = company_obj.search([])[0]
        company = company_obj.browse(company_ids)
        instance = company.instance_id
        default_cost_center = instance.top_cost_center_id and instance.top_cost_center_id.id or False
        default_funding_pool = self.get_record(db, 'analytic_account_msf_private_funds', 'analytic_distribution') or False
        distrib_obj = db.get('analytic.distribution')

        # Some functions
        def create_analytic_distribution(account_id=False):
            """If not account, search a random destination"""
            if not account_id:
                # Search a random destination
                destination_ids = db.get('account.analytic.account').search([('category', '=', 'DEST')])
                if not destination_ids:
                    raise Exception("No destination found in this database (%s)!" % (db))
                destination_id = choice(destination_ids)
            else:
                account = db.get('account.account').browse(account_id)
                destination_id = account.default_destination_id and account.default_destination_id.id or False
                if not destination_id:
                    raise Exception("No default destination found for this account: %s." % (account.code))
            distrib_id = distrib_obj.create({'name': "Autogenerated Distribution"})
            for analytic_obj, value, cc_id in [('cost.center.distribution.line', default_cost_center, False), ('funding.pool.distribution.line', default_funding_pool, default_cost_center)]:
                vals = {
                    'distribution_id': distrib_id,
                    'name': "Autogenerated Line",
                    'analytic_id': value,
                    'cost_center_id': cc_id,
                    'percentage': 100.0,
                    'currency_id': company.currency_id.id,
                    'destination_id': destination_id,
                }
                db.get(analytic_obj).create(vals)
            return distrib_id

        # Begin
        if not record:
            res = create_analytic_distribution(False)
        else:
            object_name = db.get_osv_name(record) or ''
            if not object_name:
                raise Exception("No name for this record: %s." % (record))
            pool_object = db.get(object_name)
            field = 'analytic_distribution_id'
            if object_name == 'account.bank.statement.line': # default field
                account_id = record.account_id.id or False
            elif object_name == 'purchase.order': # default field
                account_id = False
            elif object_name == 'sale.order': # default field
                account_id = False
            elif object_name == 'purchase.order.line': # default field
                account_id = record.account_4_distribution.id or False
            elif object_name == 'sale.order.line': # default field
                account_id = record.account_4_distribution.id or False
            elif object_name == 'account.move.line': # default field
                account_id = record.account_id.id or False
            elif object_name == 'account.commitment': # default field
                account_id = False
            elif object_name == 'account.commitment.line': # default field
                account_id = record.account_id.id or False
            elif object_name == 'account.invoice': # default field
                account_id = False
            elif object_name == 'account.invoice.line': # default field
                account_id = record.account_id.id or False
            elif object_name == 'account.analytic.line':
                field = 'distribution_id'
                account_id = record.general_account_id.id or False
            # TODO: Direct invoice wizard lines, open advance wizard lines
            else:
                raise Exception("Not implemented for this object: %s" % (object_name))
            # Create analytic distribution. First search a compatible destination
            res = create_analytic_distribution(account_id)
            # Write it, if asked
            if write: # only possible if record given
                pool_object.write([record.id], {field: res}, {})
        return res

    def create_journal_entry(self, database):
        '''
        Create a journal entry (account.move) with 2 lines: 
        - an expense one (with an analytic distribution)
        - a counterpart one
        Return the move ID, expense line ID, then counterpart ID
        '''
        # Prepare some values
        move_obj = database.get('account.move')
        aml_obj = database.get('account.move.line')
        period_obj = database.get('account.period')
        journal_obj = database.get('account.journal')
        partner_obj = database.get('res.partner')
        account_obj = database.get('account.account')
        distrib_obj = database.get('analytic.distribution')
        curr_date = strftime('%Y-%m-%d')
        # Search journal
        journal_ids = journal_obj.search([('type', '=', 'purchase')])
        self.assert_(journal_ids != [], "No purchase journal found!")
        # Search period
        period_ids = period_obj.get_period_from_date(curr_date)
        # Search partner
        partner_ids = partner_obj.search([('partner_type', '=', 'external')])
        # Create a random amount
        random_amount = randint(100, 10000)
        # Create a move
        move_vals = {
            'journal_id': journal_ids[0],
            'period_id': period_ids[0],
            'date': curr_date,
            'document_date': curr_date,
            'partner_id': partner_ids[0],
            'status': 'manu',
        }
        move_id = move_obj.create(move_vals)
        self.assert_(move_id != False, "Move creation failed with these values: %s" % move_vals)
        # Create some move lines
        account_ids = account_obj.search([('is_analytic_addicted', '=', True), ('code', '=', '6101-expense-test')])
        random_account = randint(0, len(account_ids) - 1)
        vals = {
            'move_id': move_id,
            'account_id': account_ids[random_account],
            'name': 'fp_changes expense',
            'amount_currency': random_amount,
        }
        # Search analytic distribution
        distribution_ids = distrib_obj.search([('name', '=', 'DISTRIB 1')])
        distribution_id = distrib_obj.copy(distribution_ids[0], {'name': 'distribution-test'})
        vals.update({'analytic_distribution_id': distribution_id})
        aml_expense_id = aml_obj.create(vals)
        counterpart_ids = account_obj.search([('is_analytic_addicted', '=', False), ('code', '=', '401-supplier-test'), ('type', '!=', 'view')])
        random_counterpart = randint(0, len(counterpart_ids) - 1)
        vals.update({
            'account_id': counterpart_ids[random_counterpart],
            'amount_currency': -1 * random_amount,
            'name': 'fp_changes counterpart',
            'analytic_distribution_id': False,
        })
        aml_counterpart_id = aml_obj.create(vals)
        # Validate the journal entry
        move_obj.button_validate([move_id]) # WARNING: we use button_validate so that it check the analytic distribution validity/presence
        return move_id, aml_expense_id, aml_counterpart_id

    def create_account(self, database, code, account_type='other', user_type_code='specific', destination_code='OPS'):
        '''
        Create an account and send the ID
        '''
        # Prepare some values
        acc_obj = database.get('account.account')
        type_obj = database.get('account.account.type')
        ana_obj = database.get('account.analytic.account')
        destination_mandatory_types = ['expense']
        # Search user_type
        type_ids = type_obj.search([('code', '=ilike', user_type_code)])
        user_type_id = type_ids and type_ids[0] or False
        if not user_type_id:
            raise Exception("User type not found: %s" % (user_type_code))
        # Search destination (only for expense accounts)
        destination_id = False
        if user_type_code in destination_mandatory_types:
            dest_ids = ana_obj.search([('category', '=', 'DEST'), ('code', '=ilike', destination_code)])
            destination_id = dest_ids and dest_ids[0] or False
            if not destination_id:
                raise Exception("Destination not found: %s" % (destination_code))
        # Create values
        vals = {
            'name': code,
            'code': code,
            'type': account_type,
            'user_type': user_type_id,
        }
        if destination_id:
            vals.update({'default_destination_id': destination_id})
        # Create account
        try:
            res_id = acc_obj.create(vals)
        except error.RPCError, e:
            raise Exception("Account creation failed!\n%s\n\n%s", (e.message, e.oerp_traceback))
        except Exception, e:
            raise Exception('error', str(e))
        return res_id

    def create_journal(self, database, name, code, journal_type, analytic_journal_id=False, account_code=False, currency_name=False, bank_journal_id=False):
        '''
        Create a journal with given info.
        If journal type is bank/cash/cheque, it needs account_code and currency_name.
        '''
        # Some checks
        if not name or not code or not journal_type:
            raise Exception("Some info missing. Name: '%s'. Code: '%s'. Type: '%s'" % (name or '', code or '', journal_type or ''))
        # Case where journal type is bank/cash/cheque
        if journal_type in ['bank', 'cheque', 'cash']:
            if not account_code or not currency_name:
                raise Exception("Bank/Cash/Cheque journals need an account code and a currency. Account: '%s'. Currency: '%s'" % (account_code or '', currency_name or ''))
        # Bank journal ID is mandatory for cheque journal
        if journal_type == 'cheque' and not bank_journal_id:
            raise Exception("Bank journal is mandatory for cheque journals!")
        # Check that we have an analytic journal
        if not analytic_journal_id:
            aj_obj = database.get('account.analytic.journal')
            analytic_journal_type = journal_type
            if journal_type in ['bank', 'cheque']:
                analytic_journal_type = 'cash'
            aj_ids =aj_obj.search([('type', '=', analytic_journal_type)])
            self.assert_(aj_ids != [], "No analytic journal found with this type: %s. Please add an analytic journal ID instead." % journal_type)
            analytic_journal_id = aj_ids[0]
        # Prepare values
        vals = {
            'name': name,
            'code': code,
            'type': journal_type,
            'analytic_journal_id': analytic_journal_id,
        }
        if account_code:
            a_obj = database.get('account.account')
            a_ids = a_obj.search([('code', '=', account_code)])
            self.assert_(a_ids != [], "No account found for the given code: %s." % account_code)
            account_id = a_ids[0]
            vals.update({
                'default_debit_account_id': account_id,
                'default_credit_account_id': account_id,
            })
        if currency_name:
            c_obj = database.get('res.currency')
            c_ids = c_obj.search([('name', '=', currency_name)])
            self.assert_(c_ids != [], "Currency not found: %s" % currency_name)
            vals.update({'currency': c_ids[0]})
        if bank_journal_id:
            vals.update({'bank_journal_id': bank_journal_id})
        # Create the journal
        return database.get('account.journal').create(vals)

    def create_register(self, database, name, code, register_type, account_code, currency_name, bank_journal_id=False):
        '''
        Create a register in the current period.
        Return register_id and journal_id.
        '''
        # Create the journal
        j_id = self.create_journal(database, name, code, register_type, account_code=account_code, currency_name=currency_name, bank_journal_id=bank_journal_id)
        # Search the register
        reg_ids = database.get('account.bank.statement').search([('journal_id', '=', j_id)])
        r_id = False
        if reg_ids:
            r_id = reg_ids[0]
        # Return register ID, journal ID
        return r_id, j_id

    def open_register(self, database, ids):
        '''
        Open the given register
        '''
        if not ids:
            return False
        if isinstance(ids, (int, long)):
            ids = [ids]
        reg_obj = database.get('account.bank.statement')
        for register in reg_obj.browse(ids):
            if not register.journal_id.type or register.state != 'draft':
                continue
            if register.journal_id.type == 'cash':
                reg_obj.button_open_cash([register.id])
            elif register.journal_id.type == 'bank':
                reg_obj.button_open_bank([register.id])
            elif register.journal_id.type == 'cheque':
                reg_obj.button_open_cheque([register.id])
        return True

    def create_register_line(self, register_id, code, amount, generate_distribution=False, date=False, document_date=False, third_partner_id=False, third_employee_id=False, third_journal_id=False):
        """Create a register line with the given account code and amount. Optionnaly third party"""
        # Check register_id presence
        if not register_id:
            raise Exception("Register ID is missing.")
        # Prepare some values
        description = ''
        register = self.reg_obj.browse(register_id)
        # Check account code
        code_ids = self.a_obj.search(['|', ('name', 'ilike', code), ('code', 'ilike', code)])
        if len(code_ids) != 1:
            raise Exception("Error searching for this account code: %s. Need %s codes." % (code, len(code_ids) > 1 and 'less' or 'more'))
        account = self.a_obj.browse(code_ids[0])
        account_id = account.id
        # Check dates
        if not date:
            date_start = register.period_id.date_start or False
            date_stop = register.period_id.date_stop or False
            if not date_start or not date_stop:
                raise Exception("No date found for the period %s." % register.period_id.name)
            random_date = self.random_date(datetime.strptime(str(date_start), '%Y-%m-%d'), datetime.strptime(str(date_stop), '%Y-%m-%d'))
            date = datetime.strftime(random_date, '%Y-%m-%d')
        if not document_date:
            document_date = date
        # Prepare some values
        if not description:
            description = self.random_word()
        vals = {
            'statement_id': register_id,
            'account_id': account_id,
            'document_date': document_date,
            'date': date,
            'amount': amount,
            'name': description,
        }
        if third_partner_id:
            vals.update({'partner_id': third_partner_id})
        if third_employee_id:
            vals.update({'employee_id': third_employee_id})
        if third_journal_id:
            vals.update({'transfer_journal_id': third_journal_id})
        res = self.absl_obj.create(vals)
        if generate_distribution and account.is_analytic_addicted:
            absl = self.absl_obj.browse(res)
            distrib_id = self.generate_analytic_distribution(self.p1, absl, True)
        else:
            distrib_id = False
        return res, distrib_id

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
