#!/usr/bin/env python
# coding: utf-8

import requests
import json
import pandas as pd
import gspread
from googleapiclient.discovery import build
from google.auth.transport.requests import Request
from oauth2client.service_account import ServiceAccountCredentials
import configparser
config = configparser.ConfigParser()
config.read('config.ini')


scope = ['https://spreadsheets.google.com/feeds','https://www.googleapis.com/auth/drive']
creds = ServiceAccountCredentials.from_json_keyfile_name('/Users/ryanduecker/projects/triathlon/golden-cheetah-upload-ec5eca7e3cb2.json', scope)

client = gspread.authorize(creds)
spreadsheet = client.open_by_key(key='12HAyrDDvdeWvnLYsAX9PPrk-Jrx5Ax8gYKQOw6nv0EQ')

## Weight
weight = spreadsheet.worksheets()[1]
weight_df = pd.DataFrame(weight.get_all_records())
weight_df['Date'] = pd.to_datetime(weight_df['Date'])

## Load Measures
import datetime
import time
from pathlib import Path
home = str(Path.home())

measures_path = config['athletes']['measures_path'].format(athlete=config['athletes']['name'])
with open(measures_path, 'r') as f:
    original = json.loads(f.read())
    f.close()

## Extract parts of file structure
measures = original['measures']
version = original['version']
## know when the latest date was
latest_date = datetime.datetime.fromtimestamp(pd.DataFrame(measures)['when'].max())

# ## Prep data
needed_cols = list(original['measures'][0].keys())
new_cols = []
rename_dict = {'Weight':'weightkg',
               'Fat':'fatpercent',
               'Date':'when',
               'Data Source':'originalsource'}

# ## Restrict to only new data 
weight_df['Fat'] = weight_df['Fat'].bfill()
new_data = weight_df[weight_df['Date'] > latest_date].copy()
print('{} new weight records'.format(new_data.shape[0]))
# New columns
new_data['fatkg'] = new_data['Weight']*new_data['Fat']/100
new_data['fatkg'] = new_data['fatkg'].apply(lambda x: round(x,2))
new_cols.append('fatkg')

# Data Hardsets
static_data = {'boneskg':3.49,
               'comment':'',
               'leankg':0,
               'musclekg':0,
              'source':3}
for col, val in static_data.items():
    new_data[col] = val

new_data['Date'] = new_data['Date'].apply(lambda x: int(time.mktime(x.timetuple())))

# ## Build Payload
new_json = json.loads(new_data.rename(columns=rename_dict)[needed_cols].to_json(orient='records'))
[measures.append(record) for record in new_json]
payload = {'measures':measures,
          'version':version}

# ## Dump Data to File
with open(measures_path, 'w') as f:
    f.write(json.dumps(payload))
    f.close()
