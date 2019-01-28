#!/usr/bin/env python3
from flask import Flask, render_template, make_response, request, jsonify, redirect
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
HAS_HTTPS = os.environ.get("APP_HAS_HTTPS", "false").lower() == "true"

# constants
AUTH = ("api", TRANSIFEX_PASSWORD)
EXAMPLE_ENTRIES = {
    "resource_slug": "07-better-to-be-hopeful-txt",
    "project_slug": "12-characters-play",
    "organization_slug": "12-characters",
    "language_code": "de",
    "color": "green",
    "label": "label",
    "extension": "svg",
    "stat": "reviewed"
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
PROTOCOL = "http" + ("s" if HAS_HTTPS else "") + "://"

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
    
    example_url = PROTOCOL + "{host}" + urllib.parse.urlparse(url_template.format(**EXAMPLE_ENTRIES)).path
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
            "url": PROTOCOL + host + app_path.format(**args),
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

def fraction_to_color(fraction):
    i = int(255 * fraction)
    # hex format, see https://stackoverflow.com/a/19996754/1320237
    return "#{:02X}{:02X}00".format(255 - i, i)

badges = []

DEFAULT_BADGE = {
    "schemaVersion": 1,
    "label": "Translation"
}

def badge(path):
    template_path = path.replace("<", "{").replace(">", "}")
    def add_endpoint(function):
        example_url = PROTOCOL + "{host}" + template_path.format(**EXAMPLE_ENTRIES)
        url = PROTOCOL + "{host}" + path
        json_url = PROTOCOL + "{host}" + path.replace("<extension>", "json")
        badges.append({
            "name": function.__name__,
            "path": path,
            "description": function.__doc__,
            "example_url": example_url,
            "template_url": url,
            "json_url": json_url,
        })
        @app.route(path, methods=['GET'])
        # use query string in cache, see https://stackoverflow.com/a/47181782/1320237
        @cache.cached(timeout=CACHE_TIMEOUT, query_string=True)
        @change_name(function.__name__ + "_" + str(len(badges)))
        def get(extension, **kw):
            if extension == "json":
                result = DEFAULT_BADGE.copy()
                badge = function(**kw)
                result.update(badge)
                return jsonify(result)
            kw["extension"] = "json"
            query = request.args.copy()
            query["url"] = PROTOCOL + request.host + template_path.format(**kw)
            query_string = urllib.parse.urlencode(query)
            redirect_url = SHIELDS_API + "/badge/endpoint." + extension + "?" + query_string
            return redirect(redirect_url)
        return function
    return add_endpoint

@badge("/badge/<organization_slug>/project/<project_slug>/<stat>.<extension>")
def project_progress(organization_slug, project_slug, stat):
    """Summarize the project progress.
    
    <ul>
        <li>organization_slug - the organization name from the URL</li>
        <li>project_slug - the project name from the URL</li>
        <li>stat - either "translated" or "reviewed"</li>
    </ul>
    """
    return project_language_progress(organization_slug, project_slug, stat)

@badge("/badge/<organization_slug>/project/<project_slug>/language/<language_code>/<stat>.<extension>")
def project_language_progress(organization_slug, project_slug, stat, language_code=None):
    """Summarize the project progress of a language.
    
    <ul>
        <li>organization_slug - the organization name from the URL</li>
        <li>project_slug - the project name from the URL</li>
        <li>stat - either "translated" or "reviewed"</li>
        <li>language_code - the language you want to summarize</li>
    </ul>
    """
    url = "https://api.transifex.com/organizations/" + organization_slug + "/projects/" + project_slug + "/resources/"
    if language_code:
        url += "?language_code=" + language_code
    api = requests.get(url, auth=AUTH, params=request.args)
    resources = api.json()
    fraction = 0
    assert stat in ("reviewed", "translated")
    for resource in resources:
        for statistic in resource["stats"].values():
            if isinstance(statistic, dict) and statistic["name"] == stat:
                    fraction += statistic["percentage"]
    fraction /= len(resources)
    # provide json service interface
    # see https://shields.io/#/endpoint
    result = {
      "label": project_slug,
      "message": str(int(round(fraction * 100))) + "%",
      "color": fraction_to_color(fraction)
    }
    return result

@app.route("/", methods=['GET']) 
def index():
    return render_template(
        "index.html",
        open_apis=open_apis,
        host=request.host,
        username=TRANSIFEX_USERNAME,
        dynamic_badges=dynamic_badges,
        badges=badges)

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0")

