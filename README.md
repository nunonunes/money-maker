Price Watcher
=============

This is a very simple (and as of yet experimental) system that I use to balance a portfolio of currencies. Right now I simply try to keep the same value in every currency I own.


Disclaimers
-----------

This system was created as an experiment and is not fit to deal with your money at all!

Furthermore: **As of this moment the system is very much in BETA status. Do _not_ use it with real money.**

Even if you ignore this advice, at this point the system doesn't actually run any live transactions on your portfolio. :-)


Usage
-----

After installing everything you need to run the project, copy `price-watcher.cfg-dist` to `price-watcher.cfg` and edit it to your heart's content. The `RecordKeeper` and `Notifier` sections are optional and I require a bit of mucking about to get right. YMMV.  
After that simply run `./price-watcher.py -h` and you will be given a description of how to use the script.

Please note you can also turn DEBUG mode on via the environment (simply define a `DEBUG` environment variable).


Connection to other systems
---------------------------

I make use of several systems in this project, namely:

- [Bitreserve][]: The broker I use to keep the actual currency (it has a nice
                    [API][Bitreserve API] and a nice 
                    [Python SDK][Bitreserve Python SDK]
- [Google Sheets][]: I like to keep a record of portfolios and transactions in
                     a nice spreadsheet. I access it through the very nice
                     [gspread][] module
- [Amazon SQS][]: This I use in order to tie in with a custom notifications
                  system I have developed a while ago. I use the [boto][]
                  module for this purpose

The Google Sheets and Amazon SQS integration are fully opcional and if you decide to try and run them you do have to make quite a bit of leg work in order to get the setup right. As always YMMV.


TO-DO
-----

This is still an experimental system and an ongoing project. These are the main things I'm thinking about doing.

- Create unitary tests for the various modules
    - portfolio
    - broker
    - money_maker
- Create tests for the script (`price-watcher.py`)
- Enable the `run_transactions` method in the `Portfolio`
- Create a weight system to enable keeping different relative values in each 
  currency
- Create a dependencies file for auto installation


Kudos
-----

[Joao][] started me thinking about playing with currency arbitrage a while ago and inspired me to tackle the problem. His own dalliances with the same problem are also [public][moneybot].


[Bitreserve]: https://bitreserve.org
[Bitreserve API]: https://developer.bitreserve.org/api/v0/
[Bitreserve Python SDK]: https://github.com/byrnereese/bitreserve-python-sdk
[Google Sheets]: https://www.google.com/sheets/about/
[gspread]: https://github.com/burnash/gspread
[Amazon SQS]: http://aws.amazon.com/sqs/
[boto]: https://github.com/boto/boto3
[Joao]: https://github.com/jneves
[moneybot]: https://github.com/jneves/moneybot
