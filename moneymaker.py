"""
Price Watcher money maker class -- a collection of ways to handle a portfolio in order to (hopefuly) make money
"""

import ConfigParser
import pprint

class MoneyMaker(object):
    """
    Represents the money-making "magic" logic

    The most used piece of information by this object is a portfolio, which is
    passed in to most methods.

    A portfolio is a structure similar to the one below:

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

    def __init__( self, config_file, base_currency, currencies, DEBUG=False ):
        """
        Create the MoneyMaker

        :param String base_currency The base currency identifier
        :param String config_file The path to a config file that ConfigParser can read and that has a "MoneyMaker" section.
        :param String currencies a dictionary with the following structure: { currency:min_transaction_value }
        :param String DEBUG Debug level
        """
        self.version = 0

        config = ConfigParser.ConfigParser()
        config.read( config_file )

# TODO: How do I get rid of this nasty `eval`?
        self.rebalance_threshold = float( config.get( 'MoneyMaker', 'rebalance_threshold' ))
        self.DEBUG         = DEBUG
        self.base_currency = base_currency
        self.currencies    = currencies


    def __calculate_portfolio_value__( self, portfolio ):
        """
        Take a portfolio as an argument and calculate its total value,
        taking into account a possible 'TOTAL' item that must not be added.

        : param Dictionary portfolio The portfolio we wish to evaluate.

        :rtype: A float corresponding the the sum of all 'value's, excluding the 'TOTAL' 'value' (if it exists)
        """

        total_value = sum( [ item['value'] for item in portfolio.values() ] )
        if 'TOTAL' in portfolio:
            total_value -= portfolio['TOTAL']['value']
        return total_value


    def __calculate_portfolio_percentages__( self, portfolio ):
        """
        Take a portfolio and calculate the different percentages of each 
        currency in it.

        : param Dictionary portfolio The portfolio we wish to analise.
        """

        # Calculate relative weight of each currency in the current portfolio
        portfolio_value = self.__calculate_portfolio_value__( portfolio )
        for currency in portfolio:
            if currency == 'TOTAL':
                continue
            portfolio[currency]['pctg'] = portfolio[currency]['value'] / portfolio_value
        return portfolio


    def shake( self, portfolio ):
        """
        Execute whatever algorithm was chosen in order to re-balance the 
        portfolio.

        At this time is only does a straight `rebalance_portfolio()`

        : param Dictionary portfolio The portfolio we wish to evaluate and 
                                     work on.

        :rtype: A list of all the transactions that need to happen in order to 
                take us from the current portfolio to a new, balanced one. 
                The list consists dictionaries with the following elements:

                {
                    'origin': String (currency),
                    'destination': String (currency),
                    'value': Number (ammount to buy or sell in base_currency),
                    'base_currency': String (base currency for the operation),
                }
        """

        return self.rebalance_portfolio( portfolio )


    def rebalance_portfolio( self, portfolio ):
        """
        Evaluate if there is a need to rebalance the portfolio and, if so, 
        calculate the transactions that need to happen in order to achieve it.

        See `shake` for a list of parameters and return values.
        """

        # Compute the value of the current portfolio
        if 'TOTAL' in portfolio:
            current_portfolio_value = portfolio['TOTAL']['value']
            if self.DEBUG:
                print 'MoneyMaker: Portfolio value: Declared: ' \
                + str(current_portfolio_value) \
                + '; Calculated: ' \
                + str(self.__calculate_portfolio_value__( portfolio ))
        else:
            current_portfolio_value = self.__calculate_portfolio_value__( portfolio )


        # Calculate the current percentages of each currency
        current_status = self.__calculate_portfolio_percentages__( portfolio )
        pctgs = [currency['pctg'] for currency in current_status.values() if 'pctg' in currency]
        max_pctg = max(pctgs)
        min_pctg = min(pctgs)

        if self.DEBUG:
            pp = pprint.PrettyPrinter()
            print "MoneyMaker: Current status:"
            pp.pprint( current_status )
            print "MoneyMaker: Current value: " + str(current_portfolio_value)
            print 'MoneyMaker: Lowest pctg found: ' + str(min_pctg)
            print 'MoneyMaker: Highest pctg found: ' + str(max_pctg)


        # Should we rebalance the portfolio?
        if (max_pctg - min_pctg) < self.rebalance_threshold:
            if self.DEBUG:
                print 'MoneyMaker: No need to rebalance the portfolio'
            return []


        # Find the ideal relative weight of each currency
        target_pctg = 1.0 / ( len( portfolio ) - 1 )
        target_value = current_portfolio_value * target_pctg
        if self.DEBUG:
            print 'MoneyMaker: Target percentage: ' + str(target_pctg)
            print 'MoneyMaker: Target value: ' + str(target_value)


        # Balance each currency
        senders   = []
        receivers = []
        for currency in current_status:
            if currency == 'TOTAL':
                continue
            transaction_value = 0
            min_transaction = self.currencies[current_status[currency]['base_currency']]['min_transaction']
            if target_value < current_status[currency]['value']:
                transaction_value = current_status[currency]['value'] \
                                    - target_value
                transaction_value = round(transaction_value/min_transaction)*min_transaction
                if transaction_value < min_transaction:
                    if self.DEBUG:
                        print 'MoneyMaker: Avoiding transaction bellow ' \
                            + str(min_transaction)\
                            + ' (send ' \
                            + str(transaction_value) \
                            + ' ' \
                            + currency \
                            + ')'
                    continue
                senders.append({
                    'currency': currency,
                    'value': transaction_value
                })
            elif target_value > current_status[currency]['value']:
                transaction_value = target_value \
                                    - current_status[currency]['value']
                transaction_value = round(transaction_value/min_transaction)*min_transaction
                if transaction_value < min_transaction:
                    if self.DEBUG:
                        print 'MoneyMaker: Avoiding transaction bellow ' \
                            + str(min_transaction)\
                            + ' (receive ' \
                            + str(transaction_value) \
                            + ' ' \
                            + currency \
                            + ')'
                    continue
                receivers.append({ 
                        'currency': currency, 
                        'value': transaction_value
                })

        # Calculate the necessary transactions
        transactions = []

        while senders and receivers:
            senders.sort(key=lambda currency: currency['value'], reverse=True)
            receivers.sort(key=lambda currency: currency['value'], reverse=True)
            sender = senders[0]
            receiver = receivers[0]

            amount_to_transfer = sender['value']
            if amount_to_transfer >= receiver['value']:
                amount_to_transfer = receiver['value']
                transactions.append({
                    'origin': sender['currency'],
                    'destination': receiver['currency'],
                    'value': amount_to_transfer,
                    'base_currency': self.base_currency
                })
                receivers.pop(0)
                senders[0]['value'] -= amount_to_transfer
                if senders[0]['value'] < self.currencies[sender['currency']]['min_transaction']:
                    senders.pop(0)
            else:
                transactions.append({
                    'origin': sender['currency'],
                    'destination': receiver['currency'],
                    'value': amount_to_transfer,
                    'base_currency': self.base_currency
                })
                senders.pop(0)
                receivers[0]['value'] -= amount_to_transfer
                if receivers[0]['value'] < self.currencies[receiver['currency']]['min_transaction']:
                    receivers.pop(0)


        if self.DEBUG:
            print "MoneyMaker: Transactions:"
            pp.pprint( transactions )


        return transactions
