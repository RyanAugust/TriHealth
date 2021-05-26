#!/usr/bin/env python
# coding: utf-8

# # HRV
# ___
# ## Import Records
import datetime
import pytz
import time
import os
from pathlib import Path
import pandas as pd
import json
import configparser

config = configparser.ConfigParser()
config.read('config.ini')

for a,b,c in os.walk(hrv_save_dir):
    csvs = []
for file in c:
    if '.csv' in file:
        csvs.append(file)

## Fix dates to search for up to date file
date_dict = {}
for file in csvs:
    year, month, day = [int(val) for val in file.split('_')[:3]]
    if year in date_dict.keys():
        if month in date_dict[year].keys():
            date_dict[year][month].append(day)
        else:
            date_dict[year][month] = [day]
    else:
        date_dict[year] = {month:[day]}
max_year = max(list(date_dict.keys()))
max_month = max(list(date_dict[max_year].keys()))
max_day = max(date_dict[max_year][max_month])
max_date = '{}_{}_{}'.format(max_year,max_month,max_day)


target_file = '{}{}_myMeasurements.csv'.format(hrv_save_dir,max_date)

hrv_df = pd.read_csv(target_file)
hrv_df = hrv_df.replace('-',pd.NA).dropna(subset=['rMSSD']).copy()


hrv_df['date'] = hrv_df['date'].apply(lambda x: x.replace('0000','0800'))
hrv_df['date'] = pd.to_datetime(hrv_df['date'])
hrv_df['timestamp_measurement'] = hrv_df['timestamp_measurement'].apply(lambda x: x.replace('0000','0800'))
hrv_df['timestamp_measurement'] = pd.to_datetime(hrv_df['timestamp_measurement'])


## Load Measures
hrv_path = config['athletes']['hrv_path'].format(athlete=config['athletes']['name'])

with open(hrv_path, 'r') as f:
    original = json.loads(f.read())
    f.close()
measures = original['measures']
version = original['version']

latest_date = datetime.datetime.fromtimestamp(measures[-1]['when'],tz=pytz.timezone('US/Pacific'))

needed_cols = list(measures[0].keys())

## Prep data
new_hrv_data = hrv_df[hrv_df['timestamp_measurement'] > latest_date].copy()
print('{} new HRV records'.format(new_hrv_data.shape[0]))
rename_dict = {'AVNN':'avnn',
                'HF':'hf',
                'HR':'hr',
                'LF':'lf',
                'pNN50':'pnn50',
                'HRV4T_Recovery_Points':'recovery_points',
                'rMSSD':'rmssd',
                'SDNN':'sdnn',
                'timestamp_measurement':'when'}

## Data Hardsets
static_data = {'originalsource':'HRV4Training',
               'comment':'',
               'source':3}

for col, val in static_data.items():
    new_hrv_data[col] = val

new_hrv_data['timestamp_measurement'] = new_hrv_data['timestamp_measurement'].apply(lambda x: int(time.mktime(x.timetuple())))


## Build Payload
for col in list(rename_dict.keys()):
    try:
        new_hrv_data[col] = new_hrv_data[col].astype(float)
    except:
        pass

new_json = json.loads(new_hrv_data.rename(columns=rename_dict)[needed_cols].to_json(orient='records'))
[measures.append(record) for record in new_json]
payload = {'measures':measures,
          'version':version}

## Dump Data to File
with open(hrv_path, 'w') as f:
    f.write(json.dumps(payload))
    f.close()
