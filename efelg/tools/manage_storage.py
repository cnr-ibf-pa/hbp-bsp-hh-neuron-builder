from hh_neuron_builder.settings import BASE_DIR, MEDIA_ROOT

import os
import shutil


def createDirIfNotExists(mpath):
    try:
        if not os.path.exists(mpath):
            os.makedirs(mpath)
    except FileExistsError:
        pass


class EfelStorage():

    @staticmethod
    def getTracesBaseUrl():
        return "https://object.cscs.ch:443/v1/AUTH_c0a333ecf7c045809321ce9d9ecdfdea/web-resources-bsp/data/NFE/eg_json_data/traces/"

    @staticmethod
    def isThereEnoughFreeSpace():
        _, _, free = shutil.disk_usage(MEDIA_ROOT)
        # if there are more than 10 Gb, there is enough free space
        return free // (2**30) > 500

    @staticmethod
    def getMainJsonDir():
        mpath = os.path.join(MEDIA_ROOT, 'efel_data', 'eg_json_data')
        createDirIfNotExists(mpath)
        return mpath

    @staticmethod
    def getTracesDir():
        mpath = os.path.join(MEDIA_ROOT, 'efel_data', 'efel_gui', 'traces')
        createDirIfNotExists(mpath)
        return mpath

    @staticmethod
    def getUserBaseDir(username, timestamp):
        mpath = os.path.join(MEDIA_ROOT, 'efel_data', 'efel_gui', 'results', username, 'data_' + timestamp)
        createDirIfNotExists(mpath)
        return mpath

    @staticmethod
    def getUserFilesDir(username, timestamp):
        mpath = os.path.join(MEDIA_ROOT, 'efel_data', 'efel_gui', 'results', username, 'data_' + timestamp, 'u_data')
        createDirIfNotExists(mpath)
        return mpath

    @staticmethod
    def getUploadedFilesDir(username, timestamp):
        mpath = os.path.join(MEDIA_ROOT, 'efel_data', 'efel_gui', 'results', username, 'data_' + timestamp, 'uploaded')
        createDirIfNotExists(mpath)
        return mpath

    @staticmethod
    def getResultsDir(username, timestamp):
        mpath = os.path.join(MEDIA_ROOT, 'efel_data', 'efel_gui', 'results', username, 'data_' + timestamp, 'u_res')
        createDirIfNotExists(mpath)
        return mpath

