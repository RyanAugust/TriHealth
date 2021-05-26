import configparser
config = configparser.ConfigParser()

config['athletes'] = {'hrv_save_dir':'/Users/ryanduecker/Dropbox/Apps/HRV4Training/',
					  'hrv_path':'/Library/Mobile Documents/com~apple~CloudDocs/GoldenCheetah/{athlete}/config/hrvmeasures.json',
					  'measures_path':'/Library/Mobile Documents/com~apple~CloudDocs/GoldenCheetah/{athlete}/config/bodymeasures.json',
					  'name':'Ryan Duecker'}


with open('config.ini', 'w') as configfile:
	config.write(configfile)