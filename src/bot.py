import os
import logging
import zulip
import sys
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
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
    'miniguez@een.com',
    'jchio@een.com',
    'mgolden@een.com',
    'pwhiteside@een.com',
    'mdiemel@een.com',
    'manuvs@een.com',
    'manu.vs@een.com',
    'cjewell@een.com'
    ] # TODO: move authorized_users to environment variables

# Health check server
class HealthCheckHandler(BaseHTTPRequestHandler):
    """Simple HTTP handler for health checks."""

    def do_GET(self):
        """Handle GET requests for health checks."""
        if self.path in ['/healthz', '/readyz']:
            self.send_response(200)
            self.send_header('Content-type', 'text/plain')
            self.end_headers()
            self.wfile.write(b'OK')
        else:
            self.send_response(404)
            self.end_headers()

    def log_message(self, format, *args):
        """Suppress default logging to avoid cluttering logs."""
        pass

def start_health_server(port=8080):
    """Start HTTP server for health checks in a separate thread."""
    server = HTTPServer(('0.0.0.0', port), HealthCheckHandler)
    logging.info(f'Starting health check server on port {port}')

    def serve():
        try:
            server.serve_forever()
        except Exception as e:
            logging.error(f'Health check server error: {e}')

    thread = threading.Thread(target=serve, daemon=True)
    thread.start()
    return server

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
    # Start health check server
    start_health_server(port=8080)

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
