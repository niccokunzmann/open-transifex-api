#!/usr/bin/env python3
from flask import Flask, render_template, make_response, request
from flask_caching import Cache
import tempfile
import os
import requests
import json
import urllib.parse

# configuration
CACHE_TIMEOUT = int(os.environ.get("APP_CACHE_TIMEOUT", 60 * 60 * 24))
TRANSIFEX_PASSWORD = os.environ["TRANSIFEX_PASSWORD"] # from https://www.transifex.com/user/settings/api/
TRANSIFEX_USERNAME = os.environ.get("TRANSIFEX_USERNAME", "niccokunzmann3") # the user for the TRANSIFEX_PASSWORD
SHIELDS_API = os.environ.get("SHIELDS_API", "https://img.shields.io") # replace this, if you run shields locally

# constants
AUTH = ("api", TRANSIFEX_PASSWORD)
EXAMPLE_ENTRIES = {
    "resource_slug": "07-better-to-be-hopeful-txt",
    "project_slug": "12-characters-play",
    "organization_slug": "12-characters",
    "language_code": "de",
    "color": "green",
    "label": "label"
}
TEMPLATE_ENTRIES = {
    "resource_slug": "RESOURCE",
    "project_slug": "PROJECT",
    "organization_slug": "ORGANIZATION",
    "language_code": "LANGUAGE",
    "color": "COLOR",
    "label": "LABEL"
}
PARAM_MODIFICATION = "modification"

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

def open_api(name, role, url, documentation, modifications={}):
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
        args = request.args.copy()
        if PARAM_MODIFICATION in args:
            modification_name = args.pop(PARAM_MODIFICATION)
            modification = modifications[modification_name]
        else:
            def modification(x):
                return x
        print("request.path", request.path)
        params = ("?" + urllib.parse.urlencode(args) if args else "")
        full_request_url = request_url + params
        print("curl -i -L --user api:$TRANSIFEX_PASSWORD -X GET '{}'".format(full_request_url))
        response = requests.get(request_url, auth=AUTH, params=args)
        result = response.json()
        result = modification(result)
        # make a response, see https://stackoverflow.com/a/40211663/1320237
        resp = make_response(json.dumps(result, indent=2), ) #here you could use make_response(render_template(...)) too
        # flask response headers, see http://werkzeug.pocoo.org/docs/0.14/datastructures/#werkzeug.datastructures.Headers
        for header in response.headers:
            if header.lower().startswith("x-transifex"):
                resp.headers[header] = response.headers[header]
        resp.headers['Access-Control-Allow-Origin'] = '*'
        resp.headers['X-App-Documentation'] = documentation
        resp.headers['X-App-Url'] = full_request_url
        resp.headers['X-App-Url-Template'] = url
        resp.mimetype = "application/json"
        return resp
    
    example_url = "http://{host}" + urllib.parse.urlparse(url_template.format(**EXAMPLE_ENTRIES)).path
    mods = []
    for modification_name in sorted(modifications):
        function = modifications[modification_name]
        mod_query = "?" + PARAM_MODIFICATION + "=" + modification_name
        mods.append({
            "name": modification_name,
            "description": function.__doc__,
            "example": example_url + mod_query,
            "path": path + mod_query
        })
    open_apis.append({
        "url": url,
        "documentation": documentation,
        "path": path,
        "name": name,
        "example": example_url,
        "role": role,
        "get": get,
        "modifications": mods
    })
    
def modify_resources_summary(data):
    """Summarize the resources into one joint statistic."""
    result = {
        "stats": {
            "reviewed_1":{
                "name": "reviewed"
            },
            "translated":{
                "name":"translated"
            },
            "language_code": data[0]["stats"].get("language_code")
        }
    }
    for attribute in ["stringcount", "wordcount", "percentage"]:
        if attribute in data[0]:
            result[attribute] = sum(entry[attribute] for entry in data)
        for stat in ["reviewed_1", "translated"]:
            value = sum(entry["stats"][stat][attribute] for entry in data)
            if attribute == "percentage":
                value /= len(data) * 1.0
            result["stats"][stat][attribute] = value
    return result

open_api(
    "Projects", "Translator", 
    "https://www.transifex.com/api/2/projects/",
    "https://docs.transifex.com/api/projects")
open_api(
    "Resources", "Translator", 
    "https://api.transifex.com/organizations/<organization_slug>/projects/<project_slug>/resources/",
    "https://docs.transifex.com/api/resources",
    modifications={"summary": modify_resources_summary})
open_api(
    "Translations", "Translator", 
    "https://www.transifex.com/api/2/project/<project_slug>/resource/<resource_slug>/translation/<language_code>/strings/",
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
    "Language Statistics", "Translator", 
    "https://www.transifex.com/api/2/project/<project_slug>/resource/<resource_slug>/stats/<language_code>",
    "https://docs.transifex.com/api/statistics")
open_api(
    "Languages", "Project Maintainer", 
    "https://www.transifex.com/api/2/project/<project_slug>/languages/",
    "https://docs.transifex.com/api/languages")
open_api(
    "Organizations", "Translator", 
    "https://api.transifex.com/organizations/",
    "https://docs.transifex.com/api/organizations")

dynamic_badges = []
def dynamic_badge(name, description, app_path, query):
    """Create a badge."""
    def template_url(host, args=TEMPLATE_ENTRIES):
        badge_query = {
            "url": "http://" + host + app_path.format(**args),
            "label": args["label"],
            "query": query.format(**args),
            "colorB": args["color"]}
        for attr in ["prefix", "suffix"]:
            if attr in args: 
                badge_query[attr] = args[attr]
        url = SHIELDS_API
        url += "/badge/dynamic/json.svg?"
        url += urllib.parse.urlencode(badge_query)
        return url
    
    def example_url(host):
        url = template_url(host, EXAMPLE_ENTRIES)
        return url
        
    def show_url(host):
        url = template_url(host)
        for variable in TEMPLATE_ENTRIES.values():
            url = url.replace(variable, "<strong>" + variable + "</strong>")
        return url
    dynamic_badges.append({ 
        "name": name,
        "description": description,
        "app_path": app_path,
        "query": query,
        "example_url": example_url,
        "template_url": template_url,
        "show_url": show_url      
    })

dynamic_badge(
    "Resource: overall translation",
    "How much of the resource is translated.",
    "/organizations/{organization_slug}/projects/{project_slug}/resources/",
    '$[?(@.slug=="{resource_slug}")].stats[?(@.name=="translated")].percentage')
dynamic_badge(
    "Resource: translation of a language",
    "How much of the resource is translated in one language.",
    "/organizations/{organization_slug}/projects/{project_slug}/resources/?language_code={language_code}",
    '$[?(@.slug=="{resource_slug}")].stats[?(@.name=="translated")].percentage')
dynamic_badge(
    "Project: overall translation",
    "How much of a project is translated.",
    "/organizations/{organization_slug}/projects/{project_slug}/resources/?modification=summary",
    '$.stats[?(@.name=="translated")].percentage')
dynamic_badge(
    "Project: translation of a language",
    "How much of a project is translated in a certain language.",
    "/organizations/{organization_slug}/projects/{project_slug}/resources/?modification=summary&language_code={language_code}",
    '$.stats[?(@.name=="translated")].percentage')

dynamic_badge(
    "Resource: overall review progress",
    "How much of the resource is reviewed.",
    "/organizations/{organization_slug}/projects/{project_slug}/resources/",
    '$[?(@.slug=="{resource_slug}")].stats[?(@.name=="reviewed")].percentage')
dynamic_badge(
    "Resource: review progress of a language",
    "How much of the resource is reviewed in one language.",
    "/organizations/{organization_slug}/projects/{project_slug}/resources/?language_code={language_code}",
    '$[?(@.slug=="{resource_slug}")].stats[?(@.name=="reviewed")].percentage')
dynamic_badge(
    "Project: overall review progress",
    "How much of a project is reviewed.",
    "/organizations/{organization_slug}/projects/{project_slug}/resources/?modification=summary",
    '$.stats[?(@.name=="reviewed")].percentage')
dynamic_badge(
    "Project: review progress of a language",
    "How much of a project is reviewed in a certain language.",
    "/organizations/{organization_slug}/projects/{project_slug}/resources/?modification=summary&language_code={language_code}",
    '$.stats[?(@.name=="reviewed")].percentage')

@app.route("/", methods=['GET']) 
def index():
    return render_template(
        "index.html",
        open_apis=open_apis,
        host=request.host,
        username=TRANSIFEX_USERNAME,
        badges=dynamic_badges)

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0")

