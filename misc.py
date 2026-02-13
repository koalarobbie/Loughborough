# -*- coding: utf-8 -*-
from datetime import datetime


LOG_FILE_PATH = "running_log.log"

global log_file 

def openlog():
    log_file = open(LOG_FILE_PATH, 'w', encoding='utf-8')


def log(log_str):
    now_time = datetime.now()
    str_time = now_time.strftime("%Y-%m-%d %H:%M:%S")
    log_str = str_time + " " + log_str + "\n"
    print(log_str)
    log_file.write(log_str)

def closelog():
    log_file.close()

