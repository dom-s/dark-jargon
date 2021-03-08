# Webapp

This folder contains all code related to the DarkJargon.net web application.

## Data Sources

The required data sources can be downloaded here: https://uofi.box.com/s/7g4whulw7awfqg8mznqk0a4a7sy0sr44

After download:

- extract files: `tar -xf darkjargon_net-data.tar.gz`
- copy `data` folder: `cp -r data <repository-root>/webapp/static/`


## Run on localhost

- in repository root folder, type
```
export FLASK_APP=webapp
export FLASK_ENV=development
export FLASK_DEBUG=true
```
- then run `flask run` and check `http://127.0.0.1:5000/`

## Launch to production:
https://flask.palletsprojects.com/en/1.1.x/deploying/mod_wsgi/

