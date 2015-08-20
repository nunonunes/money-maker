#!/bin/env python
# coding=utf-8

import ConfigParser
import sys
import pprint
import os
import argparse
from datetime import datetime

sys.path.append('.')
from broker import Broker
from moneymaker import MoneyMaker


##############################################
# Here we go


# Read in arguments and environment and configure this run
DEBUG = os.getenv('DEBUG', False)
parser = argparse.ArgumentParser()
parser.add_argument(
    "--debug", 
    help="turn debug on", 
    action="store_true"
)
parser.add_argument(
    "--dryrun", 
    help="analise but don't effect any change (implies debug)", 
    action="store_true"
)
args = parser.parse_args()
if args.debug:
    DEBUG = True
if args.dryrun:
    DEBUG = True
    dry_run = True
else:
    dry_run = False

if DEBUG:
    print 'Starting up at ' \
    + datetime.utcnow().strftime( '%Y-%m-%d %H:%M:%S +0000' )
    if dry_run:
        print 'This is a dry-run. No change will be effected'


# Setup pretty printing of data structures
if DEBUG:
    pp = pprint.PrettyPrinter()


# Read in the configs
Config = ConfigParser.ConfigParser()
Config.read('./price-watcher.cfg')


# Set up our currencies
# TODO: kill this eval with extreme prejudice!
base_currency = Config.get('Setup','base_currency')
wanted_currencies = eval(Config.get('Setup','currencies'))

if DEBUG:
    print "Currencies I'm looking for:"
    pp.pprint( wanted_currencies )


# Set up the record keeper to store our history
recorder = False
if Config.has_section('RecordKeeper'):
    from recordkeeper import RecordKeeper
    recorder = RecordKeeper( './price-watcher.cfg' )


# Set up the broker object for dealing with the money
broker = Broker( 
    './price-watcher.cfg', 
    wanted_currencies, 
    base_currency, 
    DEBUG 
)

current_portfolio = broker.get_portfolio()
if DEBUG:
    print "Current portfolio:"
    pp.pprint( current_portfolio )


# Find the new currency equilibrium
money_maker = MoneyMaker(
    './price-watcher.cfg', 
    base_currency, 
    wanted_currencies, 
    DEBUG 
)
transactions = money_maker.shake( current_portfolio )


# Get the notifier ready
notifier = False
if Config.has_section('Notifier'):
    from notifications import Notifier
    notifier = Notifier('./price-watcher.cfg')


# No transactions were deemed necessary
if not transactions:
    if DEBUG:
        if notifier:
            notifier.notify(
              'No change needed in portfolio -- ' \
              + str(
                money_maker.__calculate_portfolio_value__(current_portfolio)
              )
            )
        print "Done!"
    sys.exit(0)


# Let's run those transactions
if DEBUG:
    print "Transactions to run:"
    pp.pprint( transactions )

if not dry_run:
    broker.run_transactions( transactions )
    if recorder:
        # Record the original portfolio
        recorder.write_portfolio( 
            current_portfolio, 
            money_maker.__calculate_portfolio_value__( current_portfolio )
        )
        # Record the new portfolio
        new_portfolio = broker.get_portfolio()
        recorder.write_portfolio( 
            new_portfolio, 
            money_maker.__calculate_portfolio_value__( new_portfolio )
        )
        # Record the transactions that were carried out
        recorder.write_transactions( transactions )

    if notifier:
        notifier.notify( 
            'Done rebalancing portfolio. New value: ' \
            + str(money_maker.__calculate_portfolio_value__( new_portfolio )) \
            + ' ' \
            + base_currency 
        )


if DEBUG:
    print "Done!"
