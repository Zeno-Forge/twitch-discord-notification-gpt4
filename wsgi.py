import os
from dotenv import load_dotenv
from gunicorn.app.base import BaseApplication
from server import app
from pyngrok import ngrok

class FlaskApplication(BaseApplication):
    def __init__(self, app, options=None):
        self.options = options or {}
        self.application = app
        super().__init__()

    def load_config(self):
        config = {key: value for key, value in self.options.items()
                  if key in self.cfg.settings and value is not None}
        for key, value in config.items():
            self.cfg.set(key.lower(), value)

    def load(self):
        return self.application

load_dotenv()
port = os.environ.get("PORT", "5000")

if __name__ == "__main__":
    options = {
        "bind": f"0.0.0.0:{port}",
    }
     
    # Set ngrok authtoken
    ngrok_auth_token = os.environ['NGROK_AUTH_TOKEN']
    ngrok.set_auth_token(ngrok_auth_token)

    # Start the ngrok tunnel and get the public URL
    ngrok_url = ngrok.connect(port, bind_tls=True).public_url
    print(f"ngrok URL: {ngrok_url}")

    gunicorn_app = FlaskApplication(app, options)
    gunicorn_app.run()