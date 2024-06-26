import atexit
from flask import Flask, request, jsonify
import hmac
import hashlib
import os
import requests
import json
import logging.config
import logging.handlers
from logging.handlers import QueueHandler
import pathlib

logger = logging.getLogger("bot_notification")
#discord = logging.getLogger("discord")

def setup_logging():
    config_file = pathlib.Path("logging_config/config.json")
    with open(config_file) as f_in:
        config= json.load(f_in)
    
    logging.config.dictConfig(config)
   # queue_handler = logging.getHandlerByName("queue")
    #if queue_handler is not None:
     #   queue_handler.listener.start()
      #  atexit.register(queue_handler.listener.stop)

app = Flask(__name__)

# Load secrets from secrets.json
with open('secrets/secrets.json', 'r') as s:
    secrets = json.load(s)

client_id = secrets['client_id']
client_secret = secrets['client_secret']
webhook_secret = secrets['webhook_secret']
discord_webhook_url = secrets['discord_webhook_url']
broadcaster_user_id = secrets['broadcaster_user_id']
callback_url = secrets['callback_url']

@app.route('/webhook', methods=['GET', 'POST'])
def webhook():
    if request.method == 'GET':
        logger.info("Webhook endpoint for Twitch notifications. Use POST method for Twitch webhook notifications.")
        return jsonify({'message': 'Webhook endpoint for Twitch notifications. Use POST method for Twitch webhook notifications.'})
        
    elif request.method == 'POST':
        # Verify signature
        signature = request.headers.get('X-Hub-Signature')
        logger.info(f"signiture: {signature}")
        if not signature:
            logger.error("signiture failed or missing")
            return jsonify({'status': 'error', 'message': 'Signature missing'}), 400
            
        expected_signature = 'sha256=' + hmac.new(webhook_secret.encode(), request.data, hashlib.sha256).hexdigest()
        logging.info(f"expected signature{expected_signature}")
        if not hmac.compare_digest(signature, expected_signature):
            logger.error(f"error: invalid signature")
            return jsonify({'status': 'error', 'message': 'Invalid signature'}), 403
        
        # Parse the incoming notification
        data = request.json
        
        # Extract relevant information from the payload
        event_type = request.headers.get('Twitch-Event-Type')
        event_timestamp = request.headers.get('Twitch-Eventsub-Message-Timestamp')
        event_id = request.headers.get('Twitch-Eventsub-Message-Id')
        event_subscription_id = request.headers.get('Twitch-Eventsub-Subscription-Id')
        
        # Extract broadcaster information
        broadcaster_id = data['event']['broadcaster_user_id']
        broadcaster_name = data['event']['broadcaster_user_name']
        stream_id = data['event']['id']
        stream_title = data['event']['title']
        stream_type = data['event']['type']
        stream_started_at = data['event']['started_at']
        stream_ended_at = data['event']['ended_at'] if 'ended_at' in data['event'] else None
        stream_language = data['event']['language']
        stream_game_id = data['event']['game_id']
        stream_viewer_count = data['event']['viewer_count']
        stream_tags = data['event']['tag_ids']
        
        # Perform actions based on the notification
        if event_type == 'stream.online':
            send_discord_notification(f"{broadcaster_name} started streaming with title '{stream_title}, The activity today will be {stream_type}. ")
            logging.info(f"{broadcaster_name} started streaming with title {stream_title}")
            print(f"{broadcaster_name} started streaming with title {stream_title}")
        elif event_type == 'stream.offline':
            print(f"{broadcaster_name} stopped streaming")
            logging.info(f"{broadcaster_name} stopped streaming")
        # You can use the extracted information for further processing
        
        return jsonify({'status': 'success'})

def send_discord_notification(message):
    payload = {
        'content': message
    }
    response = requests.post(discord_webhook_url, json=payload)
    if response.status_code != 200:
        print(f"Failed to send Discord notification: {response.text}")
        logging.error(f"Failed to send Discord notification {response.text}")

def main():
    setup_logging()
    logging.basicConfig(level="INFO")
    return

if __name__ == '__main__':
    main()
    app.run(debug=True)
    