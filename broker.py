"""
Price Watcher broker class -- it encapsulates the connection with the broker we are using for handling our currency and operations.

At this time we are using Bitreserve (http://bitreserve.org/) through the Bitreserve Python SDK (http://github.com/byrnereese/bitreserve-python-sdk).
"""

import ConfigParser
from bitreserve import Bitreserve

class Broker(object):
    """
    Represents the broker that handles our portfolio
    """

    def __init__( self, config_file, currencies, base_currency, DEBUG=False ):
        """
        Create the Broker object

        :param String config_file The path to a config file that ConfigParser can read and that has a "Broker" section.
        """
        self.version = 0

        config = ConfigParser.ConfigParser()
        config.read( config_file )

        self.api = Bitreserve()
        self.api.auth_pat( config.get( 'Broker', 'pat' ) )
        self.currencies    = currencies
        self.base_currency = base_currency
        self.DEBUG         = DEBUG


    def get_tickers( self ):
        """
        Get the tickers for the currencies in the configuration (paired with the base_currency)

        :rtype: A dictionary of currency tickers with 3 fields: ask, bid, pair
        """

        tickers = self.api.get_ticker()
        relevant_pairs = {}
        
        for currency in self.currencies:
            relevant_pairs[ currency + self.base_currency ] = { 'currency': currency, 'direction': 'direct' }
            relevant_pairs[ self.base_currency + currency ] = { 'currency': currency, 'direction': 'reverse', 'direct': currency + self.base_currency }
        my_tickers = {}
        for ticker in tickers:
            if ticker[ 'pair' ] in relevant_pairs:
                if relevant_pairs[ ticker[ 'pair' ] ][ 'direction'] == 'direct':
                    new_ticker = {
                        'pair': ticker[ 'pair' ],
                        'ask':  float(ticker['ask']),
                        'bid':  float(ticker['bid']),
                    }
                    my_tickers[ relevant_pairs[ ticker[ 'pair' ] ][ 'currency'] ] = new_ticker
                elif relevant_pairs[ ticker[ 'pair' ] ][ 'direction'] == 'reverse':
                    new_ticker = {
                        'pair': relevant_pairs[ ticker[ 'pair' ] ][ 'direct' ],
                        'ask':  1.0 / float(ticker['bid']),
                        'bid':  1.0 / float(ticker['ask']),
                    }
                    my_tickers[ relevant_pairs[ ticker[ 'pair' ] ][ 'currency'] ] = new_ticker
        return my_tickers

    def get_portfolio( self ):
        """
        Get all of my assets, from my cards

        :rtype: A dictionary with the following structure:
            { 'BTC': { 
                        'amount': 0.0543,       # ammont in BTC
                        'value': 13.88,         # value in base_currency
                        'rate': 255.70500,      # conversion rate
                        'base_currency': 'USD'
                     },
              'TOTAL': {
                        'value': 13.88,         # total value in base_currency
                        'base_currency': 'USD'
                       }
            }
        """

        my_portfolio = {}
        all_of_me = self.api.get_me()
        if self.DEBUG:
            import pprint
            pp = pprint.PrettyPrinter()
            print "Broker: Balances I got:"
            pp.pprint( all_of_me['balances'] )

        total_balance = {
            'value':         float(all_of_me['balances']['total']),
            'base_currency': all_of_me['settings']['currency'],
        }
        my_portfolio['TOTAL'] = total_balance
        for currency in all_of_me['balances']['currencies']:
            if currency not in self.currencies:
                continue

            balance = {
                'amount': float(all_of_me['balances']['currencies'][currency]['balance']),
                'value':   float(all_of_me['balances']['currencies'][currency]['amount']),
                'rate':    float(all_of_me['balances']['currencies'][currency]['rate']),
                'base_currency': all_of_me['balances']['currencies'][currency]['currency'],
            }
            if balance['base_currency'] != my_portfolio['TOTAL']['base_currency']:
                print "Broker: Warning: suspicious base_currency in balance for " + currency
            my_portfolio[currency] = balance

        return my_portfolio


    def run_transactions( self, transactions ):
        """
        Get a list of transactions and run them on bitreserve.

        :param List transactions A list of transactions of the form:
            [{'base_currency': 'USD',
              'destination': u'BTC',
              'origin': u'USD',
              'amount': 0.21},
             {'base_currency': 'USD',
              'destination': u'BTC',
              'origin': u'GBP',
              'amount': 0.17},
             {'base_currency': 'USD',
              'destination': u'BTC',
              'origin': u'CNY',
              'amount': 0.13}]
        """

        # Get cards addresses
        my_cards = self.api.get_cards()
        addresses = {}
        for card in my_cards:
            addresses[card['currency']] = card['address']['bitcoin']

        # Run through the transacctions and prepare them
        ready_txns = []
        for trans in transactions:
            txn_id = self.api.prepare_txn(
                        addresses[trans['origin']],
                        addresses[trans['destination']],
                        trans['amount'],
                        trans['base_currency']
                    )
            if txn_id:
                ready_txns.append({
                            'id': txn_id,
                            'origin': addresses[trans['origin']]
                })
            else:
                print "Broker: Something went wrong with the following transaction:"
                import pprint
                pp = pprint.PrettyPrinter()
                pp.pprint( trans )
                return

        # TODO: Test this out VERY THOROUGHLY before enabling it
        import pprint
        pp=pprint.PrettyPrinter()
        print 'Broker: Created all the transactions and all appears to be well'
        pp.pprint( ready_txns )
        print 'Broker: Cowardly bailing out before committing them'
        return

        # If all went well...
        for txn in ready_txns:
            self.api.execute_txn(
                txn['origin'],
                txn['id'],
                'Money Maker automatic transaction'
            )
