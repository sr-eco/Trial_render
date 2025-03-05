from flask_caching import Cache
from flask import Flask

app = Flask(__name__)  # Ensure there's a Flask app
app.config["CACHE_TYPE"] = "SimpleCache"  # Or use "filesystem", "redis", etc.

cache = Cache(app)  # Bind cache to the app
