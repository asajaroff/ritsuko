import os
import logging

# Set up logging

LOGLEVEL = os.environ.get('LOG_LEVEL', 'INFO').upper()
ANTHROPIC_API_KEY = os.environ.get('ANTHROPIC_API_KEY', None)
logging.basicConfig(level=LOGLEVEL)

# client = zulip.Client(config_file=".zuliprc") TODO: Use client

authorized_users = [
    'asajaroff@een.com',
    'cjewell@een.com'
    ] # TODO: move authorized_users to environment variables

class MyBotHandler(object):
    '''
    Ritsuko is an assistent bot for the Infrarstructure team.
    '''

    def usage(self):
        return '''Your description of the bot'''

    def handle_message(self, message, bot_handler):
        logging.debug(message)
        if message['sender_email'] in authorized_users:

            logging.debug("Handling event type: {type}".format(type=message['type']))

            original_content = message['content']
            original_sender = message['sender_email']
            new_content = original_content.replace('@followup',
                                                    'from %s:' % (original_sender,))


            if message['type'] == 'private':
                bot_handler.send_message(dict(
                    type='private',
                    #to=message['sender_email'],
                    to=[r['email'] for r in message['display_recipient']],
                    content='Got your message: \n> ' + message['content']))

            elif message['type'] =='stream':
                bot_handler.send_message(dict(
                    type='stream',
                    to=message['display_recipient'],
                    subject=message['subject'],
                    content='Got your message: \n> ' + message['content']))


            bot_handler.send_message(dict(
                type='private',
                to=message['sender_email'],
                content=new_content,
            ))

        else:
            if message['type'] == 'private':
                bot_handler.send_message(dict(
                    type='private',
                    #to=message['sender_email'],
                    to=[r['email'] for r in message['display_recipient']],
                    content='I am not authorized to talk to you'))

            elif message['type'] =='stream':
                bot_handler.send_message(dict(
                    type='stream',
                    to=message['display_recipient'],
                    subject=message['subject'],
                    content='I am not authorized to talk to you'))


handler_class = MyBotHandler


