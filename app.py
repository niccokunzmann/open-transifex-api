#!/usr/bin/env python3
from flask import Flask, render_template, make_response
from flask_caching import Cache
import tempfile
import os
import requests
import json
import urllib.parse

# configuration
CACHE_TIMEOUT = int(os.environ.get("APP_CACHE_TIMEOUT", 60))
TRANSIFEX_PASSWORD = os.environ["TRANSIFEX_PASSWORD"] # from https://www.transifex.com/user/settings/api/

# constants
AUTH = ("api", TRANSIFEX_PASSWORD)

# globals
app = Flask(__name__, template_folder= "templates")
# Check Configuring Flask-Cache section for more details
cache = Cache(app, config={
    'CACHE_TYPE': 'filesystem',
    'CACHE_DIR': tempfile.mktemp(prefix="cache-")})

open_apis = []

def change_name(name):
    """Change the name of a function."""
    def change_to(function):
        function.__name__ = name
        return function
    return change_to

def open_api(url, documentation):
    """Open the call to the API for a user."""
    
    # get the path from a url, see https://stackoverflow.com/a/7894483/1320237
    path = urllib.parse.urlparse(url).path
    url_template = url.replace("<", "{").replace(">", "}")
    print("url_template:", url_template)
    @app.route(path, methods=['GET']) 
    @cache.cached(timeout=CACHE_TIMEOUT, key_prefix="api-{}/%s".format(len(open_apis)))
    @change_name(path)
    def get(**kw):
        request_url = url_template.format(**kw)
        print("curl -i -L --user api:$TRANSIFEX_PASSWORD -X GET '{}'".format(request_url))
        response = requests.get(request_url, auth=AUTH)
        result = response.json()
        # make a response, see https://stackoverflow.com/a/40211663/1320237
        resp = make_response(json.dumps(result, indent=2), ) #here you could use make_response(render_template(...)) too
        # flask response headers, see http://werkzeug.pocoo.org/docs/0.14/datastructures/#werkzeug.datastructures.Headers
        resp.headers['Access-Control-Allow-Origin'] = '*'
        resp.headers['X-Documentation'] = documentation
        resp.headers['X-Url'] = request_url
        resp.headers['X-Url-Template'] = url
        resp.mimetype = "application/json"
        return resp
    
    open_apis.append({
        "url": url,
        "documentation": documentation,
        "path": path
    })
    
    

open_api(
    "https://www.transifex.com/api/2/projects/",
    "https://docs.transifex.com/api/projects")
open_api(
    "https://api.transifex.com/organizations/<organization>/projects/<project>/resources/",
    "https://docs.transifex.com/api/resources")
open_api(
    "https://www.transifex.com/api/2/project/<project>/resource/<resource_slug>/translation/<language>/strings/",
    "https://docs.transifex.com/api/translations")



@app.route("/", methods=['GET']) 
@cache.cached(timeout=CACHE_TIMEOUT)
def index():
    return render_template("index.html", open_apis=open_apis)

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0")

