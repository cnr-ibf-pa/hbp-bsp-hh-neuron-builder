from hh_neuron_builder.settings import BASE_DIR, MEDIA_ROOT

import os


class EfelStorage():

    @staticmethod
    def __createDirIfNotExists(mpath):
        if not os.path.exists(mpath):
            os.makedirs(mpath)

    @staticmethod
    def getMainJsonDir():
        mpath = os.path.join(MEDIA_ROOT, 'efel_data', 'eg_json_data')
        return mpath

    @staticmethod
    def geTracesBaseUrl():
        return "https://object.cscs.ch:443/v1/AUTH_c0a333ecf7c045809321ce9d9ecdfdea/web-resources-bsp/data/NFE/eg_json_data/traces/"

    @staticmethod
    def getUserBaseDir(username, timestamp):
        mpath = os.path.join(MEDIA_ROOT, 'efel_data', 'efel_gui', 'results', username, 'data_' + timestamp)
        __createDirIfNotExists(mpath)
        return mpath

    @staticmethod
    def getUserFilesDir(username, timestamp):
        mpath = os.path.join(MEDIA_ROOT, 'efel_data', 'efel_gui', 'results', username, 'data_' + timestamp, 'u_data')
        __createDirIfNotExists(mpath)
        return mpath

    @staticmethod
    def getUploadedFilesDir(username, timestamp):
        mpath = os.path.join(MEDIA_ROOT, 'efel_data', 'efel_gui', 'results', username, 'data_' + timestamp, 'uploaded')
        __createDirIfNotExists(mpath)
        return mpath

    @staticmethod
    def getResultsDir(username, timestamp):
        mpath = os.path.join(MEDIA_ROOT, 'efel_data', 'efel_gui', 'results', username, 'data_' + timestamp, 'u_res')
        __createDirIfNotExists(mpath)
        return mpath

