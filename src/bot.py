import os
import logging
import zulip
import sys
import threading
import time
from http.server import HTTPServer, BaseHTTPRequestHandler
from commands import execute_command

# Set up logging
logging.basicConfig(
    level=os.environ.get('LOG_LEVEL', 'INFO').upper(),
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

RITSUKO_VERSION = 'local-dev'

# Cache bot profile to avoid repeated API calls
BOT_PROFILE = None

#Set up tools
ANTHROPIC_API_KEY = os.environ.get('ANTHROPIC_API_KEY', None)

# Validate required environment variables
required_env_vars = ['ZULIP_EMAIL', 'ZULIP_API_KEY', 'ZULIP_SITE']
missing_vars = [var for var in required_env_vars if not os.environ.get(var)]
if missing_vars:
    logging.error(f'Missing required environment variables: {", ".join(missing_vars)}')
    sys.exit(1)

# Initialize client as None - will be set in main() with retry logic
client = None

authorized_users = [
    'asajaroff@een.com',
    'miniguez@een.com',
    'user1088@chat.eencloud.com', # Manu
    'jchio@een.com',
    'pwhiteside@een.com',
    'mdiemel@een.com',
    'cjewell@een.com',
    'yolorunsola@een.com',
    'abrown@een.com',
    'gkameni@een.com',
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
    """
    Handle incoming Zulip messages with the following behavior:
    - Always reply when tagged with @
    - In public/private streams: never reply if not tagged
    - In private conversations with 3+ users (including bot): don't reply unless tagged
    - In 1-on-1 conversations: always reply, even without tag
    """
    try:
        # Ignore messages from the bot itself
        if message['sender_email'] == os.environ['ZULIP_EMAIL']:
            return

        # Get message metadata
        bot_user_id = BOT_PROFILE['user_id']
        mentioned_user_ids = message.get('mentioned_user_ids', [])
        msg_type = message.get('type', 'unknown')
        content = message.get('content', '')

        logging.debug(f'Message type: {msg_type}, Bot ID: {bot_user_id}, Mentioned IDs: {mentioned_user_ids}')
        logging.debug(f'Message content: {content}')

        # Check if bot is mentioned
        bot_mentioned = (bot_user_id in mentioned_user_ids or
                        '@**Ritsuko**' in content or
                        '@_**Ritsuko**' in content)

        # Determine if we should respond based on message type and context
        should_respond = False

        if msg_type == 'stream':
            # Public streams: only respond if bot is mentioned
            if bot_mentioned:
                should_respond = True
                logging.debug('Responding to stream message with mention')
            else:
                logging.debug('Ignoring stream message without mention')
                return

        elif msg_type == 'private':
            display_recipient = message.get('display_recipient', [])

            # Count non-bot users in the conversation
            non_bot_users = [r for r in display_recipient if r['email'] != os.environ['ZULIP_EMAIL']]
            num_non_bot_users = len(non_bot_users)

            logging.debug(f'Private message with {num_non_bot_users} non-bot user(s)')

            if num_non_bot_users == 1:
                # 1-on-1 conversation: always respond
                should_respond = True
                logging.debug('Responding to 1-on-1 private message')
            else:
                # Group private conversation: only respond if mentioned
                if bot_mentioned:
                    should_respond = True
                    logging.debug('Responding to group private message with mention')
                else:
                    logging.debug('Ignoring group private message without mention')
                    return
        else:
            logging.debug(f'Unknown message type: {msg_type}')
            return

        # If we shouldn't respond, exit early
        if not should_respond:
            return

        # Log the message
        logging.info(f'{message["sender_email"]}: {message["content"]}')

        # Check authorization
        if message['sender_email'] not in authorized_users:
            logging.warning(f'Unauthorized user: {message["sender_email"]}')
            response = 'I am not authorized to talk to you'
        else:
            # Import handle_ai to check if we need to pass callback
            from commands import parse_command, handle_ai
            command, args = parse_command(message)

            # For AI command, pass the send_message callback for progress updates
            if command == 'ai':
                response = handle_ai(message, args, send_message_callback=send_message)
            else:
                response = execute_command(message)

        # Send response
        if message['type'] == 'private':
            send_message({
                'type': 'private',
                'to': [r['email'] for r in message['display_recipient'] if r['email'] != os.environ['ZULIP_EMAIL']],
                'content': response
            })
        elif message['type'] == 'stream':
            send_message({
                'type': 'stream',
                'to': message['display_recipient'],
                'subject': message['subject'],
                'content': response
            })

    except Exception as e:
        logging.error(f'Error handling message: {e}')


def main():
    """Main function to run the bot."""
    global BOT_PROFILE, client

    # Start health check server first so K8s doesn't kill us during initialization
    start_health_server(port=8080)

    # Initialize Zulip client with retry logic
    max_retries = 5
    retry_delay = 10  # seconds

    for attempt in range(1, max_retries + 1):
        try:
            logging.info(f'Attempting to connect to Zulip (attempt {attempt}/{max_retries})...')
            client = zulip.Client(
                email=os.environ['ZULIP_EMAIL'],
                api_key=os.environ['ZULIP_API_KEY'],
                site=os.environ['ZULIP_SITE']
            )
            # Test connection by getting profile
            BOT_PROFILE = client.get_profile()
            logging.info(f'Successfully connected! Bot profile: {BOT_PROFILE.get("full_name")} (ID: {BOT_PROFILE.get("user_id")})')
            break
        except Exception as e:
            logging.error(f'Failed to initialize Zulip client (attempt {attempt}/{max_retries}): {e}')
            if attempt < max_retries:
                logging.info(f'Retrying in {retry_delay} seconds...')
                time.sleep(retry_delay)
            else:
                logging.error('Max retries reached. Exiting.')
                sys.exit(1)

    # Subscribe to messages
    logging.info('Starting Zulip bot message loop...')
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
