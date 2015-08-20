"""
Price Watcher notifications class -- it encapsulates the notification mechanisms available to the app

At this time we are using Amazon SQS services (http://aws.amazon.com/sqs/) for this purpose, together with a SQS-to-XMPP gateway that we already had implmented.
"""

import ConfigParser
import boto3

class Notifier(object):
    """
    Represents the notifier object
    """

    def __init__( self, config_file ):
        """
        Create the Notifier object

        :param String config_file The path to a config file that ConfigParser can read and that has a "Notifier" section.
        """
        self.version = 0

        config = ConfigParser.ConfigParser()
        config.read( config_file )

        self.session = boto3.session.Session(
            aws_access_key_id=config.get('Notifier','aws_access_key_id'),
            aws_secret_access_key=config.get('Notifier','aws_secret_access_key'),
            region_name=config.get('Notifier','region_name'),
        )
        self.sqs = self.session.resource('sqs')
        self.queue = self.sqs.get_queue_by_name(QueueName=config.get('Notifier','queue_name'))
        self.recipient = config.get('Notifier','recipient_jid')



    def notify( self, message ):
        """
        Send a message to the recipient indicated in the config file
        """
        
        return self.queue.send_message( MessageBody='Notify ' + self.recipient + ': price_watcher: ' + message )
