# commands.md

## create venv

python3 -m venv venv

## activate venv

source venv/bin/activate

## install requirements

pip install requests python-dotenv

## freeze requirements

pip freeze > requirements.txt

## fetch OAuth token (run first)

python api_calls/fetch_token.py

## fetch dams list

python api_calls/fetch_dams.py

## fetch individual dam details

python api_calls/fetch_dam_details.py

## fetch dam resources (last year)

python api_calls/fetch_dam_resources.py

## fetch latest dam resources

python api_calls/fetch_dam_resources_latest.py

## check date range

python api_calls/check_history_depth.py
