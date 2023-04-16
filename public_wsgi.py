import os
from dotenv import load_dotenv
from gunicorn.app.base import BaseApplication
from proxy import proxy_app

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
port = os.environ.get("PORT", "8001")

if __name__ == "__main__":
    options = {
        "bind": f"0.0.0.0:{port}",
    }
    gunicorn_app = FlaskApplication(proxy_app, options)  
    gunicorn_app.run()
    print("proxy ran")