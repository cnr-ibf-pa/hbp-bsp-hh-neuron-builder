"""
This module provides a useful class to fetch all statics paths used by the Efel 
"""


from hh_neuron_builder.settings import BASE_DIR, MEDIA_ROOT

import os


def createDirIfNotExists(mpath):
    """Create directory if not exists

    Parameters
    ----------
    mpath : str
        full path of the directory 
    """
    if not os.path.exists(mpath):
        os.makedirs(mpath)


class EfelStorage():

    @staticmethod
    def getMainJsonDir():
        """Get main json directory

        Returns
        -------
        str
        """
        mpath = os.path.join(MEDIA_ROOT, 'efel_data', 'eg_json_data')
        return mpath

    @staticmethod
    def getTracesBaseUrl():
        """Get endpoint used to fetch traces from server

        Returns
        -------
        str
        """
        return "https://object.cscs.ch:443/v1/AUTH_c0a333ecf7c045809321ce9d9ecdfdea/web-resources-bsp/data/NFE/eg_json_data/traces/"

    @staticmethod
    def getUserBaseDir(username, timestamp):
        """Get user's base directory

        Parameters
        ----------
        username : str
            identify the user
        timestamp : str
            identify the correct workspace

        Returns
        -------
        str
        """
        mpath = os.path.join(MEDIA_ROOT, 'efel_data', 'efel_gui', 'results', username, 'data_' + timestamp)
        createDirIfNotExists(mpath)
        return mpath

    @staticmethod
    def getUserFilesDir(username, timestamp):
        """Get user's files directory

        Parameters
        ----------
        username : str
            identify the user
        timestamp : str
            identify the correct workspace

        Returns
        -------
        str
        """
        mpath = os.path.join(MEDIA_ROOT, 'efel_data', 'efel_gui', 'results', username, 'data_' + timestamp, 'u_data')
        createDirIfNotExists(mpath)
        return mpath

    @staticmethod
    def getUploadedFilesDir(username, timestamp):
        """Get user's uploaded directory

        Parameters
        ----------
        username : str
            identify the user
        timestamp : str
            identify the correct workspace

        Returns
        -------
        str
        """
        mpath = os.path.join(MEDIA_ROOT, 'efel_data', 'efel_gui', 'results', username, 'data_' + timestamp, 'uploaded')
        createDirIfNotExists(mpath)
        return mpath

    @staticmethod
    def getResultsDir(username, timestamp):
        """Get user's results directory

        Parameters
        ----------
        username : str
            identify the user
        timestamp : str
            identify the correct workspace

        Returns
        -------
        str
        """
        mpath = os.path.join(MEDIA_ROOT, 'efel_data', 'efel_gui', 'results', username, 'data_' + timestamp, 'u_res')
        createDirIfNotExists(mpath)
        return mpath

