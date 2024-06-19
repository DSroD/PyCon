# PyCon
## Frontend for Source RCON

## Building
This repository contains ready-to-use dockerfile and example docker-compose.

Currently only SQLite is implemented - it is required to
run the container with volume mapped to the sqlite file (see Setup)
to ensure data persistence.

## Setup
### Environment variables
| Variable                      | Default value  | Description                                                  |
|-------------------------------|----------------|--------------------------------------------------------------|
| LOG_LEVEL                     | INFO           | Log level (DEBUG, INFO, WARNING, ERROR)                      |
| DEFAULT_USER_NAME             | admin          | Default username for service account                         |
| DEFAULT_USER_PASSWORD         | admin          | Default password for service account                         |
| ACCESS_TOKEN_SECRET           | <<replace-me>> | Secret for generating access tokens. Replace this!           |
| ACCESS_TOKEN_EXPIRE_MINUTES   | 10             | Duration of maximal token validity. Should be greater than 2 |
| DB_CONFIGURATION__DB_PROVIDER | SQLITE         | Currently only SQLITE is supported                           |

### Special environmental variables

When `DB_PROVIDER` is set to `SQLITE` following environmental variables are available

| Variable                  | Default value | Description               |
|---------------------------|---------------|---------------------------|
| DB_CONFIGURATION__DB_NAME | pycon.sqlite3 | Filename of the SQLite DB |


## Usage
Run the docker image with external port mapped to internal port 80.
Connect using browser of your choice. Login using credentials set in
environmental variables.

Default account has permissions to manage both RCON servers and users.

Access to RCON of each server can be limited to a subset of users.

Each user can be granted permission to 
1) Create users and grant permissions to existing users
2) Add RCON connections (servers) and manage users who can access the RCON.

