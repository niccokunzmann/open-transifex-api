#!/usr/bin/env python3
from flask import Flask, render_template, make_response, request
from flask_caching import Cache
import tempfile
import os
import requests
import json
import urllib.parse

# configuration
CACHE_TIMEOUT = int(os.environ.get("APP_CACHE_TIMEOUT", 60))
TRANSIFEX_PASSWORD = os.environ["TRANSIFEX_PASSWORD"] # from https://www.transifex.com/user/settings/api/
TRANSIFEX_USERNAME = os.environ.get("TRANSIFEX_USERNAME", "niccokunzmann3") # from https://www.transifex.com/user/settings/api/

# constants
AUTH = ("api", TRANSIFEX_PASSWORD)
EXAMPLE_ENTRIES = {
    "resource_slug": "07-better-to-be-hopeful-txt",
    "project_slug": "12-characters-play",
    "organization_slug": "12-characters",
    "language": "de"
}

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

def open_api(name, role, url, documentation):
    """Open the call to the API for a user."""
    
    # get the path from a url, see https://stackoverflow.com/a/7894483/1320237
    path = urllib.parse.urlparse(url).path
    url_template = url.replace("<", "{").replace(">", "}")
    print("url_template:", url_template)
    @app.route(path, methods=['GET']) 
    # use query string in cache, see https://stackoverflow.com/a/47181782/1320237
    @cache.cached(timeout=CACHE_TIMEOUT, key_prefix="{}/%s".format(name), query_string=True)
    @change_name(name)
    def get(**kw):
        # request query string, see http://werkzeug.pocoo.org/docs/0.14/wrappers/#werkzeug.wrappers.BaseRequest.args
        request_url = url_template.format(**kw)
        print("request.path", request.path)
        params = ("?" + urllib.parse.urlencode(request.args) if request.args else "")
        print("curl -i -L --user api:$TRANSIFEX_PASSWORD -X GET '{}{}'".format(request_url, params))
        response = requests.get(request_url, auth=AUTH, params=request.args)
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
    
    example_url = "http://{host}" + urllib.parse.urlparse(url_template.format(**EXAMPLE_ENTRIES)).path
    
    open_apis.append({
        "url": url,
        "documentation": documentation,
        "path": path,
        "name": name,
        "example": example_url,
        "role": role
    })
    
    

open_api(
    "Projects", "Translator", 
    "https://www.transifex.com/api/2/projects/",
    "https://docs.transifex.com/api/projects")
open_api(
    "Resources", "Translator", 
    "https://api.transifex.com/organizations/<organization_slug>/projects/<project_slug>/resources/",
    "https://docs.transifex.com/api/resources")
open_api(
    "Translations", "Translator", 
    "https://www.transifex.com/api/2/project/<project_slug>/resource/<resource_slug>/translation/<language>/strings/",
    "https://docs.transifex.com/api/translations")
open_api(
    "Reports", "Translator", 
    "https://api.transifex.com/organizations/<organization_slug>/reports/activity/",
    "https://docs.transifex.com/api/reports")
open_api(
    "Statistics", "Translator", 
    "https://www.transifex.com/api/2/project/<project_slug>/resource/<resource_slug>/stats/",
    "https://docs.transifex.com/api/statistics")
open_api(
    "Languages", "Project Maintainer", 
    "https://www.transifex.com/api/2/project/<project_slug>/languages/",
    "https://docs.transifex.com/api/languages")




@app.route("/", methods=['GET']) 
def index():
    return render_template("index.html", open_apis=open_apis, host=request.host, username=TRANSIFEX_USERNAME)

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0")

