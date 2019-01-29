# Open Transifex API

[![](https://dockerbuildbadges.quelltext.eu/status.svg?repository=open-transifex-api&organization=niccokunzmann)](https://hub.docker.com/r/niccokunzmann/open-transifex-api/)

This project aims at making it easy for people to share their open
projects on Transifex with an open API to services on the Internet.

It includes:

- Open Endpoints of the Transifex API
- Example usage of the Transifex API by [shields.io] through dynamic badges
- Badge endpoints for projects

To open your API, you need to invite the account to your project which runs
the endpoint.

If you run an endpoint, you can list it here:
- [transifex.quelltext.eu][quelltext] (daily deployment)

## Configuration

Need to be set:

- `TRANSIFEX_PASSWORD`  
  Is the API token from [the user settings](https://www.transifex.com/user/settings/api/).
  This is required to access the API.
- `TRANSIFEX_USERNAME` defaults to `niccokunzmann3`  
  Is the user of the API token. This is required so
  that the displayed documentation allows people to invite the user
  to their project so the project can publish its API.

Optional:

- `APP_CACHE_TIMEOUT` defaults to 1 day  
  The time the response should be cached, so we do not use up the
  quota of the transifex user.
- `SHIELDS_API` defaults to `https://img.shields.io`  
  This is the endpoint used to generate badges.
  If you want to test your badges as a developer,
  you can set this to `http://localhost:8080` and install
  [shields.io](https://github.com/badges/shields/#development).
- `APP_HAS_HTTPS` defaults to `false`  
  If your app is behind HTTPS, you can enable this.

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

