import os
import logging
import zulip
import sys
from commands import execute_command

# Set up logging
logging.basicConfig(
    level=os.environ.get('LOG_LEVEL', 'INFO').upper(),
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

RITSUKO_VERSION = 'local-dev'

#Set up tools
ANTHROPIC_API_KEY = os.environ.get('ANTHROPIC_API_KEY', None)

# Validate required environment variables
required_env_vars = ['ZULIP_EMAIL', 'ZULIP_API_KEY', 'ZULIP_SITE']
missing_vars = [var for var in required_env_vars if not os.environ.get(var)]
if missing_vars:
    logging.error(f'Missing required environment variables: {", ".join(missing_vars)}')
    sys.exit(1)

try:
    client = zulip.Client(
        email=os.environ['ZULIP_EMAIL'],
        api_key=os.environ['ZULIP_API_KEY'],
        site=os.environ['ZULIP_SITE']
    )
except Exception as e:
    logging.error(f'Failed to initialize Zulip client: {e}')
    sys.exit(1)

authorized_users = [
    'asajaroff@een.com',
    'cjewell@een.com'
    ] # TODO: move authorized_users to environment variables

def send_message(message_dict):
    """Send a message with error handling."""
    try:
        result = client.send_message(message_dict)
        if result.get('result') != 'success':
            logging.error(f'Failed to send message: {result.get("msg", "Unknown error")}')
            return False
        return True
    except Exception as e:
        logging.error(f'Exception while sending message: {e}')
        return False

def handle_message(message):
    """Handle incoming Zulip messages with error handling."""
    try:
        # Ignore messages from the bot itself
        if message['sender_email'] == os.environ['ZULIP_EMAIL']:
            logging.debug('Ignoring own message')
            return

        if message['sender_email'] in authorized_users:
            logging.info(f'{message['sender_email']}: {message['content']}' )

            # Execute command and get response
            response = execute_command(message)

            if message['type'] == 'private':
                send_message(dict(
                    type='private',
                    to=[r['email'] for r in message['display_recipient']],
                    content=response
                ))

            elif message['type'] == 'stream':
                send_message(dict(
                    type='stream',
                    to=message['display_recipient'],
                    subject=message['subject'],
                    content=response
                ))

        else:
            logging.warning(f'Ignoring message from {message['sender_email']} -- msg: {message['content']}' )
            if message['type'] == 'private':
                send_message(dict(
                    type='private',
                    to=[r['email'] for r in message['display_recipient']],
                    content='I am not authorized to talk to you'
                ))

            elif message['type'] == 'stream':
                send_message(dict(
                    type='stream',
                    to=message['display_recipient'],
                    subject=message['subject'],
                    content='I am not authorized to talk to you'
                ))

    except KeyError as e:
        logging.error(f'Missing expected field in message: {e}')
    except Exception as e:
        logging.error(f'Unexpected error handling message: {e}')


def main():
    """Main function to run the bot."""
    # Subscribe to messages
    logging.info('Starting Zulip bot...')
    try:
        client.call_on_each_message(handle_message)
    except KeyboardInterrupt:
        logging.info('Bot stopped by user')
        sys.exit(0)
    except Exception as e:
        logging.error(f'Fatal error in message loop: {e}')
        sys.exit(1)

if __name__ == '__main__':
    main()
