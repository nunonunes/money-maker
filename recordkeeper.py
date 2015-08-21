"""
Price Watcher recordkeeper class -- it encapsulates the system used to maintain the records regarding our current assets and history of assets and transactions.

At this time we are using Google Spresdsheets for this, with the help of the gspread module (https://github.com/burnash/gspread).
"""

import ConfigParser
import gspread
import json
import time
from oauth2client.client import SignedJwtAssertionCredentials
from datetime import datetime

class RecordKeeper(object):
    """
    Represents our record
    """

    def __init__( self, config_file ):
        """
        Create the RecordKeeper object

        :param String config_file The path to a config file that ConfigParser can read and has both a "RecordKeeper" and a "Google" section.
        """
        self.version = 0

        config = ConfigParser.ConfigParser()
        config.read( config_file )

        # Get the credentials for OAuth 2 authentication
        json_key = json.load(open(config.get('RecordKeeper','google_api_credentials_file')))
        scope = ['https://spreadsheets.google.com/feeds']
        credentials = SignedJwtAssertionCredentials(json_key['client_email'], json_key['private_key'], scope)

        # Authenticate and get the worksheets
        gc = gspread.authorize(credentials)
        ss = gc.open(config.get('RecordKeeper','spreadsheet_name'))
        self.worksheet_transactions = ss.worksheet(config.get('RecordKeeper','worksheet_transactions'))
        self.worksheet_portfolios = ss.worksheet(config.get('RecordKeeper','worksheet_portfolios'))

        self.max_retries = int( config.get( 'RecordKeeper','max_retries' ))


    def get_transactions_working_row( self ):
        """
        Calculate the working row for the transactions worksheet
        """
        all_rows = self.worksheet_transactions.col_values(1)
        return len( all_rows ) + 1


    def write_transactions ( self, transactions, date=datetime.utcnow().strftime( '%Y-%m-%d %H:%M:%S +0000' ) ):
        """
        Record the given transactions in the transactions worksheet, with full details.

        The list of transactions is presented in the transactions parameter and has the following structure:

        [{'base_currency': 'USD',
        'destination': u'BTC',
        'origin': u'USD',
        'value': 0.35714285714285765},
        {'base_currency': 'USD',
        'destination': u'BTC',
        'origin': u'GBP',
        'value': 0.3071428571428587},
        {'base_currency': 'USD',
        'destination': u'BTC',
        'origin': u'JPY',
        'value': 0.29714285714285893},
        {'base_currency': 'USD',
        'destination': u'BTC',
        'origin': u'EUR',
        'value': 0.15714285714284948}]
        """

        num_rows = len( transactions )

        retries = self.max_retries
        while retries > 0:
            try:
                row = self.get_transactions_working_row()
                ws = self.worksheet_transactions
                start = ws.get_addr_int(row, 1)
                end = ws.get_addr_int(row+num_rows-1, 5)
                cells = ws.range( start+':'+end )

                i = 0
                for t in transactions:
                    cells[i].value = date
                    i += 1
                    for key in [ 'origin', 'destination', 'amount', 'base_currency' ]:
                        cells[i].value = t[key]
                        i += 1

                self.worksheet_transactions.update_cells( cells )
                break
            except:
                print 'RecordKeeper: Error trying to record full log, trying again in one second'
                time.sleep(1)
                retries -= 1
        if retries == 0:
            print 'RecordKeeper: Could not record the full log, giving up'
            raise
            sys.exit()


    def get_portfolios_working_row( self ):
        """
        Calculate the working row for the full log worksheet
        """
        all_rows = self.worksheet_portfolios.col_values(1)
        return len( all_rows ) + 1


    def write_portfolio( self, portfolio, total_value, date=datetime.utcnow().strftime( '%Y-%m-%d %H:%M:%S +0000' ) ):
        """
        Record the full portfolio in the portfolios worksheet, complete with
        the full value.

        A portfolio is a structure similar to the following:

            { 'BTC': {                          # this item's currency -- BTC
                        'amount': 0.0543,       # amount in BTC
                        'value': 13.88,         # value in base_currency
                        'rate': 255.70500,      # conversion rate
                        'base_currency': 'USD'
                     },
              'TOTAL': {                        # special item (optional)
                        'value': 13.88,         # total value in base_currency
                        'base_currency': 'USD'
                       }
            }
        """

        num_rows = len(portfolio)

        retries = self.max_retries
        while retries > 0:
            try:
                row = self.get_portfolios_working_row()
                ws = self.worksheet_portfolios
                start = ws.get_addr_int(row, 1)
                end = ws.get_addr_int(row+num_rows, 4)
                cells = ws.range( start+':'+end )

                i=0
                for currency,data in portfolio.items():
                    if currency == 'TOTAL':
                        continue
                    cells[i].value = date
                    i += 1
                    cells[i].value = currency
                    i += 1
                    cells[i].value = data['amount']
                    i += 1
                    cells[i].value = data['value']
                    i += 1

                cells[i].value = date
                i += 1
                cells[i].value = 'TOTAL'
                i += 1
                cells[i].value = ''
                i += 1
                cells[i].value = total_value

                ws.update_cells( cells )
                break
            except:
                print 'RecordKeeper: Error trying to record portfolio, trying again in one second'
                time.sleep(1)
                retries -= 1
        if retries == 0:
            print 'RecordKeeper: Could not record portfolio, giving up'
            raise
            sys.exit()

