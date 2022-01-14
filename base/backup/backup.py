import gzip
import subprocess
from subprocess import PIPE, Popen
import configparser
import time
import shutil
import os
from backup.send_drive import searchFile
from logger import log

config = configparser.ConfigParser()
config.read('config.ini')

db_name = config['BASE']['DB_NAME']
db_port = config['BASE']['DB_PORT']
bu_name = config['BACKUP']['BU_NAME']
db_drive = eval(config['BACKUP']['BU_DRIVE'])

file_name = bu_name +'.backup'
gz_name = file_name +'.gz'

def backup():    
    if os.path.isfile(file_name):
        today = time.localtime()
        today = time.strftime("%Y-%m-%d", today)
        lastdate_modified = time.localtime(os.path.getmtime(file_name))
        lastdate_modified = time.strftime("%Y-%m-%d", lastdate_modified)
        if today == lastdate_modified:
            log.info('Backup already done')
        else:
            _create_file()          
    else:        
        _create_file()

def _create_file():
    log.info('Backup...')
    cmd ='pg_dump -d '+ db_name +' -p '+ db_port +' -U comercial -F t -f '+ file_name
    with gzip.open(file_name, 'wb') as f:
        popen = subprocess.Popen(cmd, stdout=subprocess.PIPE, universal_newlines=True)    
    for stdout_line in iter(popen.stdout.readline, ""):
        f.write(stdout_line.encode('utf-8'))    
    popen.stdout.close()
    popen.wait()
    
    with open(file_name, 'rb') as f_in:
        with gzip.open(gz_name, 'wb') as f_out:
            shutil.copyfileobj(f_in, f_out)
    time.sleep(1)
    if db_drive:
            searchFile(100, "name = '"+gz_name+"'", gz_name)