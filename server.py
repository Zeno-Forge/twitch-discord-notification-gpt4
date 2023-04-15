import os
import requests
from flask import Flask, request, jsonify, redirect, url_for, render_template
from flask_sslify import SSLify
from dotenv import load_dotenv
import hashlib
import hmac
from cachetools import TTLCache
import time
from dateutil.parser import parse as datetime_parse
from pyngrok import ngrok

# Load .env file
load_dotenv()

app = Flask(__name__)

# Set ngrok authtoken
ngrok_auth_token = os.environ['NGROK_AUTH_TOKEN']
ngrok.set_auth_token(ngrok_auth_token)

# Start the ngrok tunnel and get the public URL
ngrok_url = ngrok.connect(os.environ.get("PORT", "8000"), bind_tls=True).public_url
print(f"ngrok URL: {ngrok_url}")

#Redirects all traffic to https
# sslify = SSLify(app) 

def get_twitch_access_token(client_id, client_secret):
    url = "https://id.twitch.tv/oauth2/token"
    payload = {
        "client_id": client_id,
        "client_secret": client_secret,
        "grant_type": "client_credentials"
    }
    response = requests.post(url, params=payload)
    return response.json()["access_token"]

def get_streamer_id(access_token, streamer_name):
    url = "https://api.twitch.tv/helix/users"
    headers = {
        "Client-ID": os.environ["TWITCH_CLIENT_ID"],
        "Authorization": f"Bearer {access_token}"
    }
    params = {"login": streamer_name}
    response = requests.get(url, headers=headers, params=params)
    data = response.json()["data"]

    return data[0]["id"] if data else None

def subscribe_to_stream_online_events(user_id, streamer_name, access_token, callback_url):
    headers = {
        "Client-ID": os.environ["TWITCH_CLIENT_ID"],
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }
    payload = {
        "type": "stream.online",
        "version": "1",
        "condition": {"broadcaster_user_id": user_id},
        "transport": {
            "method": "webhook",
            "callback": callback_url,
            "secret": os.environ["TWITCH_CLIENT_SECRET"]
        }
    }
    url = "https://api.twitch.tv/helix/eventsub/subscriptions"
    response = requests.post(url, headers=headers, json=payload)
    if response.status_code == 202:
        print(f"Subscribed to {streamer_name}'s stream online events")

        # Add the subscription information to the list
        subscriptions.append({"streamer_name": streamer_name, "event_type": "stream.online"})
    else:
        print(f"Failed to subscribe to {streamer_name}'s stream online events")
        print(response.status_code)
    return response.json()

def get_eventsub_info(access_token):
    headers = {
        "Client-ID": os.environ["TWITCH_CLIENT_ID"],
        "Authorization": f"Bearer {access_token}"
    }
    url = "https://api.twitch.tv/helix/eventsub/subscriptions"
    response = requests.get(url, headers=headers)
    return response.json()

def send_discord_message(streamer_name, stream_title, game_name, profile_picture_url, stream_preview_url):
    webhook_url = os.environ['DISCORD_WEBSOCKET_URL']
    roleID = os.environ['DISCORD_ROLE_ID']
    
    # Format the message as an embedded Discord message
    embed = {
        "title": stream_title,
        "description": f"I am live everybun, please hop on by if you are free!\n\n**Game:**\n{game_name}",
        "url": f"https://www.twitch.tv/{streamer_name}",
        "color": 6570404,  # Twitch purple color
        "thumbnail": {"url": profile_picture_url},
        "image": {"url": stream_preview_url},
        "footer": {
            "text": "Twitch",
            "icon_url": "https://www.freepnglogos.com/uploads/twitch-logo-transparent-png-20.png"
        }
    }
    print(f"{stream_preview_url}")
    payload = {
        #"content": f"<@&{roleID}>",
        "embeds": [embed]
        }
    headers = {"Content-Type": "application/json"}

    # Send the message to Discord
    response = requests.post(webhook_url, json=payload, headers=headers)

    if response.status_code != 204:
        print(f"Failed to send message to Discord: {response.status_code}, {response.text}")

def get_user_name(user_id):
    access_token = get_twitch_access_token(os.environ["TWITCH_CLIENT_ID"], os.environ["TWITCH_CLIENT_SECRET"])
    headers = {
        "Client-ID": os.environ["TWITCH_CLIENT_ID"],
        "Authorization": f"Bearer {access_token}"
    }

    user_url = f"https://api.twitch.tv/helix/users?id={user_id}"
    response = requests.get(user_url, headers=headers)

    if response.status_code == 200:
        return response.json()["data"][0]["login"]
    else:
        print(f"Failed to fetch username for user ID {user_id}: {response.status_code}")
        return None

def get_stream_data(access_token, streamer_id):
    headers = {
        "Client-ID": os.environ["TWITCH_CLIENT_ID"],
        "Authorization": f"Bearer {access_token}"
    }
    url = f"https://api.twitch.tv/helix/streams?user_id={streamer_id}"
    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        return response.json()["data"][0]
    else:
        print(f"Failed to fetch stream data for streamer ID {streamer_id}: {response.status_code}")
        return None

def get_game_data(access_token, game_id):
    headers = {
        "Client-ID": os.environ["TWITCH_CLIENT_ID"],
        "Authorization": f"Bearer {access_token}"
    }
    url = f"https://api.twitch.tv/helix/games?id={game_id}"
    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        return response.json()["data"][0]
    else:
        print(f"Failed to fetch game data for game ID {game_id}: {response.status_code}")
        return None
    
def get_user_data(access_token, streamer_id):
    headers = {
        "Client-ID": os.environ["TWITCH_CLIENT_ID"],
        "Authorization": f"Bearer {access_token}"
    }
    url = f"https://api.twitch.tv/helix/users?id={streamer_id}"
    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        return response.json()["data"][0]
    else:
        print(f"Failed to fetch user data for streamer ID {streamer_id}: {response.status_code}")
        return None

# Fetch existing EventSub subscriptions
def get_existing_subscriptions():
    access_token = get_twitch_access_token(os.environ["TWITCH_CLIENT_ID"], os.environ["TWITCH_CLIENT_SECRET"])
    headers = {
        "Client-ID": os.environ["TWITCH_CLIENT_ID"],
        "Authorization": f"Bearer {access_token}"
    }

    subscription_url = "https://api.twitch.tv/helix/eventsub/subscriptions"
    response = requests.get(subscription_url, headers=headers)

    if response.status_code == 200:
        subscriptions = []
        for sub in response.json()["data"]:
            user_id = sub['condition']['broadcaster_user_id']
            user_name = get_user_name(user_id)
            created_on_date = datetime_parse(sub['created_at'])
            callback_url = sub['transport']['callback']
            if user_name:
                subscriptions.append({
                    "id": sub['id'],
                    "streamer_name": user_name,
                    "streamer_id": user_id,
                    "event_type": sub['type'],
                    "created_on": created_on_date,
                    "callback_url": callback_url,
                    "state": sub['status']
        })
        return subscriptions
    else:
        print(f"Failed to fetch existing subscriptions: {response.status_code}")
        return []
    
def send_info_to_discord(streamer_name, streamer_id):
                # Fetch additional stream data
            access_token = get_twitch_access_token(os.environ["TWITCH_CLIENT_ID"], os.environ["TWITCH_CLIENT_SECRET"])
            stream_data = get_stream_data(access_token, streamer_id)
            game_data = get_game_data(access_token, stream_data['game_id'])
            user_data = get_user_data(access_token, streamer_id)

            stream_title = stream_data['title']
            game_name = game_data['name']
            profile_picture_url = user_data['profile_image_url']
            stream_preview_url = stream_data['thumbnail_url'].replace('{width}', '1280').replace('{height}', '720')

            # Call the function to send a Discord message with the additional data
            response = send_discord_message(streamer_name, stream_title, game_name, profile_picture_url, stream_preview_url)
            return response

@app.route('/', methods=['GET'])
def subscribe_form():
    access_token = get_twitch_access_token(os.environ["TWITCH_CLIENT_ID"], os.environ["TWITCH_CLIENT_SECRET"])
    eventsub_info = get_eventsub_info(access_token)
    total_cost = eventsub_info["total_cost"]
    max_total_cost = eventsub_info["max_total_cost"]
    global subscriptions 
    subscriptions = get_existing_subscriptions()

    return render_template('subscribe_page.html', total_cost=total_cost, max_total_cost=max_total_cost)

@app.route('/table')
def table():
    subscriptions = get_existing_subscriptions()
    return render_template('table.html', subscriptions=subscriptions)

@app.route('/', methods=['POST'])
def subscribe():
    streamer_name = request.form.get('streamer_name')
    if not streamer_name:
        return jsonify({"error": "Please enter a valid streamer name."}), 400

    access_token = get_twitch_access_token(os.environ["TWITCH_CLIENT_ID"], os.environ["TWITCH_CLIENT_SECRET"])
    user_id = get_streamer_id(access_token, streamer_name)

    if not user_id:
        return jsonify({"error": "Streamer not found."}), 404

    callback_url = f"{ngrok_url}/twitch-event"
    subscribe_to_stream_online_events(user_id, streamer_name, access_token, callback_url)

    return jsonify({"success": f"Successfully subscribed to {streamer_name}'s stream online events."})

@app.route('/eventsub-info', methods=['GET'])
def eventsub_info():
    access_token = get_twitch_access_token(os.environ["TWITCH_CLIENT_ID"], os.environ["TWITCH_CLIENT_SECRET"])
    eventsub_info = get_eventsub_info(access_token)
    total_cost = eventsub_info["total_cost"]
    max_total_cost = eventsub_info["max_total_cost"]

    return jsonify({"total_cost": total_cost, "max_total_cost": max_total_cost})

# Cache to store used message IDs with a 10-minute expiration time
message_id_cache = TTLCache(maxsize=100, ttl=600)

@app.route('/twitch-event', methods=['POST'])
def twitch_event():
    headers = request.headers
    body = request.json

    if 'Twitch-Eventsub-Message-Type' not in headers:
        return 'Bad request', 400

    message_type = headers['Twitch-Eventsub-Message-Type']
    message_id = headers['Twitch-Eventsub-Message-Id']
    message_timestamp = headers['Twitch-Eventsub-Message-Timestamp']
    message_signature = headers['Twitch-Eventsub-Message-Signature']

    # Check for replay attacks
    if message_id in message_id_cache:
        return 'Message ID already processed', 400

    # Verify the signature
    payload = message_id + message_timestamp + request.data.decode('utf-8')
    signature = hmac.new(os.environ['TWITCH_CLIENT_SECRET'].encode('utf-8'), payload.encode('utf-8'), hashlib.sha256).hexdigest()
    expected_signature = f'sha256={signature}'

    if message_signature != expected_signature:
        return 'Invalid signature', 400

    # Check if the message_timestamp is older than 10 minutes
    current_timestamp = int(time.time())
    received_datetime = datetime.fromisoformat(message_timestamp.replace("Z", "+00:00"))
    received_timestamp = int(received_datetime.timestamp())

    if current_timestamp - received_timestamp > 600:
        return 'Message timestamp too old', 400

    # Store the message ID in the cache
    message_id_cache[message_id] = True

    if message_type == 'webhook_callback_verification':
        challenge = body['challenge']
        return challenge

    if message_type == 'notification':
        event = body['event']
        event_type = event['type']

        if event_type == 'live':
            streamer_name = event['broadcaster_user_name']
            streamer_id = event['broadcaster_user_id']
            print(f"{streamer_name} just went live on Twitch!")
            
            response = send_info_to_discord(streamer_name, streamer_id)

            return 'OK', 200

    return 'Unsupported message type', 400

@app.route('/remove-subscription', methods=['POST'])
def remove_subscription():
    print(f"Received request to remove subscription: {request.form.get('id')}")
    subscription_id = request.form.get('id')

    if not subscription_id:
        print("Error: Missing subscription ID")
        return "Missing subscription ID", 400

    access_token = get_twitch_access_token(os.environ["TWITCH_CLIENT_ID"], os.environ["TWITCH_CLIENT_SECRET"])
    headers = {
        "Client-ID": os.environ["TWITCH_CLIENT_ID"],
        "Authorization": f"Bearer {access_token}"
    }

    subscription_url = f"https://api.twitch.tv/helix/eventsub/subscriptions?id={subscription_id}"
    response = requests.delete(subscription_url, headers=headers)

    if response.status_code == 204:
        # Remove the subscription from the list
        return "Subscription removed", 200
    else:
        print(f"Error: Failed to remove subscription: {response.status_code}")
        if response.status_code == 404:
            return "Failed to remove subscription: Subscription not found", 404
        else:
            return f"Failed to remove subscription: {response.status_code}", 400
        
@app.route('/test', methods=['POST'])
def test_message():
    streamer_id = request.form.get('streamer_id')
    streamer_name = request.form.get('streamer_name')
    response = send_info_to_discord(streamer_name, streamer_id)
    return "Tested Discord Post", 204
    

if __name__ == '__main__':
    # Set Port
    port = int(os.environ.get("PORT", 5000))
    
    app.run(host='localhost', port=port)