#! /usr/bin/python3

import argparse
import os
import datetime
import shutil


DRY_RUN = False


STORAGE_TO_CLEAN = {
    'HHNB': [
        'hhnb/workflows/',
        'hhnb/tmp/',
    ],
    'NFE': [
        'efel_data/efel_gui/uploaded/',
        'efel_data/efel_gui/results/',
        'efel_data/efel_gui/traces/'
    ]
}


DATETIME_FORMAT = '%Y%m%d%H%M%S'


def check_and_clean(storage, recreate=True):
    print('Checking for %s...' % storage, end='')
    if os.path.exists(storage):
        if not DRY_RUN:
            shutil.rmtree(storage)
        print(' cleaned.')
        if not os.path.exists(storage) and recreate:
            os.mkdir(storage)
    else:
        print(' not found.')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Storage cleaner tool for HHNB and NFE.')
    parser.add_argument('MEDIA_ROOT', type=str, help='Set MEDIA_ROOT path as the same for HHNB')
    parser.add_argument('--dry-run', dest='DRY_RUN', action='store_true', help='Run without any modification in the filesystem')
    args = parser.parse_args()
    
    media_root = os.path.abspath(args.MEDIA_ROOT)
    hhnb_storage = [os.path.join(media_root, d) for d in STORAGE_TO_CLEAN['HHNB']]
    nfe_storage = [os.path.join(media_root, d) for d in STORAGE_TO_CLEAN['NFE']]

    # clean NFE storages
    for s in nfe_storage:
        check_and_clean(s) 

    check_and_clean(hhnb_storage[1]) # clean "hhnb/tmp"
    
    # set datetime now
    time_now = datetime.datetime.now()

    users_wf = [os.path.join(hhnb_storage[0], d) for d in os.listdir(hhnb_storage[0])] 
    for user_wf in users_wf:
        wfs = [os.path.join(user_wf, wf) for wf in os.listdir(user_wf)]
        for wf in wfs:
            wf_time = (os.path.split(wf)[1])[2:]
            wf_datetime = datetime.datetime.strptime(wf_time, DATETIME_FORMAT)
            if (time_now - wf_datetime).days > 2:
                check_and_clean(wf, False)