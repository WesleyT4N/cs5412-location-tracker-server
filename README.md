# CS-5412-Location-Traffic-Tracker-Server

## Setup Instructions:

- Make sure you have Python 3.7+ installed
- (optional): Make a python3 virtual environment for this project using something like `virtualenvwrapper`
- Within the project directory run `pip install -r requirements.txt`. This will install all the necessary dependencies.

## How to Run:

- Within the project directory make sure you first call `source .env` this will export all the necessary env vars for the application
- Run `flask run` which will start up the server in development mode.
- The application will run on port 8080 by default but can be changed within the `.env` file by changing the `FLASK_RUN_PORT` env variable.

## How to Run Tests:

This project uses `pytest` for unit testing.

- Within the project directory make sure you first call `source .env` this will export all the necessary env vars for the application
- Run `pytest` which will run all available tests within the `tests/` directory

## Where to access

Temporarily hosted at [https://loc-traffic-tracker.azurewebsites.net]
