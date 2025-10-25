import os
import logging
import zulip

# Set up logging
logging.basicConfig(
    level=os.environ.get('LOG_LEVEL', 'INFO').upper(),
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

#Set up tools
ANTHROPIC_API_KEY = os.environ.get('ANTHROPIC_API_KEY', None)


client = zulip.Client(
    email=os.environ['ZULIP_EMAIL'],
    api_key=os.environ['ZULIP_API_KEY'],
    site=os.environ['ZULIP_SITE']
)

authorized_users = [
    'asajaroff@een.com',
    'cjewell@een.com'
    ] # TODO: move authorized_users to environment variables

def handle_message(message):

    # Ignore messages from the bot itself
    if message['sender_email'] == os.environ['ZULIP_EMAIL']:
        logging.debug('Ignoring own message')
        return

    
    if message['sender_email'] in authorized_users:
        logging.info(f'Authorized user {message['sender_email']} wants to know {message['content']}' )

        original_content = message['content']
        original_sender = message['sender_email']
        # new_content = original_content.replace('@followup',
        #                                         'from %s:' % (original_sender,))

        # client.send_message(dict(
        #     type='private',
        #     to=message['sender_email'],
        #     content=new_content,
        # ))

        if message['type'] == 'private':
            client.send_message(dict(
                type='private',
                to=[r['email'] for r in message['display_recipient']],
                content='Got your message: \n> ' + message['content']
            ))

        elif message['type'] == 'stream':
            client.send_message(dict(
                type='stream',
                to=message['display_recipient'],
                subject=message['subject'],
                content='Got your message: \n> ' + message['content']
            ))

    else:
        logging.warning(f'Ignoring message from {message['sender_email']} -- msg: {message['content']}' )
        if message['type'] == 'private':
            client.send_message(dict(
                type='private',
                to=[r['email'] for r in message['display_recipient']],
                content='I am not authorized to talk to you'
            ))

        elif message['type'] == 'stream':
            client.send_message(dict(
                type='stream',
                to=message['display_recipient'],
                subject=message['subject'],
                content='I am not authorized to talk to you'
            ))


# Subscribe to messages
client.call_on_each_message(handle_message)


# class MyBotHandler(object):
#     '''
#     Ritsuko is an assistent bot for the Infrarstructure team.
#     '''

#     def usage(self):
#         return '''Your description of the bot'''

#     def handle_message(self, message, bot_handler):
#         logging.debug(message)
#         if message['sender_email'] in authorized_users:

#             logging.debug("Handling event type: {type}".format(type=message['type']))

#             original_content = message['content']
#             original_sender = message['sender_email']
#             new_content = original_content.replace('@followup',
#                                                     'from %s:' % (original_sender,))


#             if message['type'] == 'private':
#                 bot_handler.send_message(dict(
#                     type='private',
#                     #to=message['sender_email'],
#                     to=[r['email'] for r in message['display_recipient']],
#                     content='Got your message: \n> ' + message['content']))

#             elif message['type'] =='stream':
#                 bot_handler.send_message(dict(
#                     type='stream',
#                     to=message['display_recipient'],
#                     subject=message['subject'],
#                     content='Got your message: \n> ' + message['content']))


#             bot_handler.send_message(dict(
#                 type='private',
#                 to=message['sender_email'],
#                 content=new_content,
#             ))

#         else:
#             if message['type'] == 'private':
#                 bot_handler.send_message(dict(
#                     type='private',
#                     #to=message['sender_email'],
#                     to=[r['email'] for r in message['display_recipient']],
#                     content='I am not authorized to talk to you'))

#             elif message['type'] =='stream':
#                 bot_handler.send_message(dict(
#                     type='stream',
#                     to=message['display_recipient'],
#                     subject=message['subject'],
#                     content='I am not authorized to talk to you'))
#
#handler_class = MyBotHandler


