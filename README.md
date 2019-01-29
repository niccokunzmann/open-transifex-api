# Open Transifex API

[![](https://img.shields.io/docker/build/niccokunzmann/open-transifex-api.svg)](https://hub.docker.com/r/niccokunzmann/open-transifex-api/)
[![](https://transifex.quelltext.eu/badge/projects.svg)][quelltext]

This project aims at making it easy for people to share their open
projects on Transifex with an open API to services on the Internet.

It includes:

- Open Endpoints of the Transifex API
- Example usage of the Transifex API by [shields.io] through dynamic badges
- Badge endpoints for projects

To open your API, you need to invite the account to your project which runs
the endpoint.

If you run an endpoint, you can list it here:
- [transifex-open-api.herokuapp.com/](https://transifex-open-api.herokuapp.com/)
  (instant deployment)
- [transifex.quelltext.eu][quelltext] (daily deployment)

## Deployment

You can deploy the app using Heroku.
There is a free plan.

[![Deploy](https://www.herokucdn.com/deploy/button.svg)](https://heroku.com/deploy)

You can enable automatic deployments when the repository is updated in the
Deploy Section of the app management.

[Heroku Button Documentation](https://devcenter.heroku.com/articles/heroku-button)


## Configuration

Need to be set:

- `TRANSIFEX_PASSWORD`  
  Is the API token from [the user settings](https://www.transifex.com/user/settings/api/).
  This is required to access the API.
- `TRANSIFEX_USERNAME` defaults to `secret-user`  
  Is the user of the API token. This is required so
  that the displayed documentation allows people to invite the user
  to their project so the project can publish its API.
  E.g. the user of [here][quelltext] is `open_api`.

Optional:

- `APP_CACHE_TIMEOUT` defaults to 1 day  
  The time in seconds the response should be cached, so we do not use up the
  quota of the transifex user.
- `SHIELDS_API` defaults to `https://img.shields.io`  
  This is the endpoint used to generate badges.
  If you want to test your badges as a developer,
  you can set this to `http://localhost:8080` and install
  [shields.io](https://github.com/badges/shields/#development).
- `APP_HAS_HTTPS` defaults to `false`  
  If your app is behind HTTPS, you can enable this.
  Note that [shields.io requires HTTPS for badges](https://github.com/badges/shields/issues/2891).
- `PORT` defaults to `5000`  
  Is the port the app uses.
  This is required by [Heroku](https://devcenter.heroku.com/articles/runtime-principles#web-servers).

All configuration must be duplicated to [app.json](app.json) in order for
Heroku to correctly display the values.

## Development

Install Python3 and Pip.

```
pip install -r requirements.txt
```

Set environment variables.

```
export TRANSIFEX_PASSWORD=...
export TRANSIFEX_USERNAME=...
```

Start the app.

```
python3 app.py
```

## Docker

Use the image:

```
docker run --rm                                \
           -p 5000:5000                        \
           -e "TRANSIFEX_PASSWORD=..."         \
           -e "TRANSIFEX_USER=..."             \
           niccokunzmann/open-transifex-api
```

Build the image:

```
docker build . -t niccokunzmann/open-transifex-api
```


## Related Work

- https://github.com/transifex/transifex/issues/319
- https://github.com/greatislander/tenpercent

[quelltext]: https://transifex.quelltext.eu

