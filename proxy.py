import os
from flask import Flask, request, jsonify, make_response
import requests
from pyngrok import ngrok
from dotenv import load_dotenv
import smtplib
from email.mime.text import MIMEText
import traceback

# Load .env file
load_dotenv()

proxy_app = Flask(__name__)

# Set ngrok authtoken
ngrok_auth_token = os.environ['NGROK_AUTH_TOKEN']
ngrok.set_auth_token(ngrok_auth_token)

# Start the ngrok tunnel and get the public URL
ngrok_url = ngrok.connect(os.environ.get("PORT", "8001"), bind_tls=True).public_url
print(f"ngrok URL: {ngrok_url}")

def send_email(subject, body):
    # Set up the email message
    message = MIMEText(body)
    message['Subject'] = subject
    message['From'] = os.environ['SMTP_USERNAME']
    message['To'] = os.environ['EMAIL_TO']

    # Connect to the SMTP server
    smtp_server = os.environ['SMTP_SERVER']
    smtp_port = os.environ['SMTP_PORT']
    smtp_username = os.environ['SMTP_USERNAME']
    smtp_password = os.environ['SMTP_PASSWORD']
    server = smtplib.SMTP_SSL(smtp_server, smtp_port)
    server.login(smtp_username, smtp_password)
    # Send the email
    server.sendmail(smtp_username, os.environ['EMAIL_TO'], message.as_string())
    # Disconnect from the SMTP server
    server.quit()

def send_url():
    server_port = int(os.environ.get("SERVER_PORT", "8000"))
    url_info = {"ngrok_url": ngrok_url}
    response = requests.post(f'http://private_app:{server_port}/url', json=url_info)
    print("URL Sent to sever. Response:", response.json())
    
send_url()
@proxy_app.route('/twitch-event', methods=['POST'])
def twitch_forward():
    server_port = int(os.environ.get("SERVER_PORT", "8000"))
    # Preserve headers from the original request
    headers = dict(request.headers)
    # Remove the 'Host' header to avoid potential conflicts
    headers.pop('Host', None)
    # Forward the request with the same headers and body
    response = requests.post(f'http://private_app:{server_port}/twitch-event', headers=headers, data=request.data)

    # Check if the response has JSON content before decoding
    if response.headers.get('Content-Type') == 'application/json' and response.text:
        resp = jsonify(response.json())
    else:
        resp = make_response(response.text, response.status_code)

    resp.status_code = response.status_code
    
    if resp.status_code == 400:
        send_email('Error in Twitch Event', str(resp))
        resp = jsonify({'error':'bad request'}), 400 #clear traceback information from sending out to client

    if resp.status_code == 500:
        error_message = resp.json().get('error', '')
        traceback_message = resp.json().get('traceback', '')
        email_body = f"Error: {error_message}\n\nTraceback:\n{traceback_message}"
        send_email('Error in Twitch Event', email_body)
        resp = jsonify({'error':'bad request'}), 500 #clear traceback information from sending out to client
        
    for header, value in response.headers.items():
        resp.headers[header] = value
    return resp

if __name__ == '__main__':
    # Set Port
    port = int(os.environ.get("PORT", 8001))
    
    proxy_app.run(host='localhost', port=port)
    