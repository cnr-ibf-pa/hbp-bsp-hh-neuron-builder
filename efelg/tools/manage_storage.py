from hh_neuron_builder.settings import BASE_DIR, MEDIA_ROOT

import os
import shutil


def createDirIfNotExists(mpath):
    """
    Check if a directory exists, if not, create it
    """

    if not os.path.exists(mpath):
        os.makedirs(mpath, exist_ok=True)


class EfelStorage():

    @staticmethod
    def getTracesBaseUrl():
        """Get the URL of the directory where all the traces are contained

        Returns
        -------
        str
            URL of the directory
        """

        return "https://object.cscs.ch:443/v1/AUTH_c0a333ecf7c045809321ce9d9ecdfdea/web-resources-bsp/data/NFE/eg_json_data/traces/"

    @staticmethod
    def getMetadataTracesUrl():
        """Get the URL of the file containing all traces metadata

        Returns
        -------
        str
            URL of all traces metadata
        """

        return "https://object.cscs.ch:443/v1/AUTH_c0a333ecf7c045809321ce9d9ecdfdea/web-resources-bsp/data/NFE/eg_json_data/traces/all_traces_metadata.json"

    @staticmethod
    def isThereEnoughFreeSpace():
        """If there are more than 10 Gb, there is enough free space

        Returns
        -------
        bool
            True if there is enough space, otherwise False
        """

        _, _, free = shutil.disk_usage(MEDIA_ROOT)
        return free // (2**30) > 10

    @staticmethod
    def getMainJsonDir():
        """Get the path to the main local directory

        Returns
        -------
        str
            path to the main local directory
        """

        mpath = os.path.join(MEDIA_ROOT, 'efel_data', 'eg_json_data')
        createDirIfNotExists(mpath)
        return mpath

    @staticmethod
    def getTracesDir():
        """Get the path to the local directory containing the traces

        Returns
        -------
        str
            path to the local directory containing the traces
        """

        mpath = os.path.join(MEDIA_ROOT, 'efel_data', 'efel_gui', 'traces')
        createDirIfNotExists(mpath)
        return mpath

    @staticmethod
    def getUserBaseDir(username, timestamp):
        """Get the path to the local unique user base directory

        Parameters
        ----------
        username : str
            the username of the user
        timestamp : str
            the timestamp registered when the user started the application

        Returns
        -------
        str
            path to the local unique user base directory
        """

        mpath = os.path.join(MEDIA_ROOT, 'efel_data', 'efel_gui',
                             'results', username, 'data_' + timestamp)
        createDirIfNotExists(mpath)
        return mpath

    @staticmethod
    def getUserFilesDir(username, timestamp):
        """Get the path to the local unique user directory
           containing the files that are used by the user

        Parameters
        ----------
        username : str
            the username of the user
        timestamp : str
            the timestamp registered when the user started the application

        Returns
        -------
        str
            path to the local unique user directory containing the files
            that are used by the user
        """

        mpath = os.path.join(MEDIA_ROOT, 'efel_data', 'efel_gui',
                             'results', username, 'data_' + timestamp, 'u_data')
        createDirIfNotExists(mpath)
        return mpath

    @staticmethod
    def getUploadedFilesDir(username, timestamp):
        """Get the path to the local unique user directory
           containing the user uploaded files

        Parameters
        ----------
        username : str
            the username of the user
        timestamp : str
            the timestamp registered when the user started the application

        Returns
        -------
        str
            path to the local unique user directory containing the user
            uploaded files
        """

        mpath = os.path.join(MEDIA_ROOT, 'efel_data', 'efel_gui', 'results',
                             username, 'data_' + timestamp, 'uploaded')
        createDirIfNotExists(mpath)
        return mpath

    @staticmethod
    def getResultsDir(username, timestamp):
        """Get the path to the local unique user directory
           containing the results

        Parameters
        ----------
        username : str
            the username of the user
        timestamp : str
            the timestamp registered when the user started the application

        Returns
        -------
        str
            path to the local unique user directory containing the results
        """

        mpath = os.path.join(MEDIA_ROOT, 'efel_data', 'efel_gui',
                             'results', username, 'data_' + timestamp, 'u_res')
        createDirIfNotExists(mpath)
        return mpath
