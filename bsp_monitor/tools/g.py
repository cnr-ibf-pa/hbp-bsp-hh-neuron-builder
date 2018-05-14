from oauth2client.service_account import ServiceAccountCredentials
import gspread
import json
import datetime

class GoogleStatManager:

    # The scope for the OAuth2 request.
    SCOPE = 'https://www.googleapis.com/auth/analytics.readonly'

    # The location of the key file with the key data.
    KEY_FILEPATH = 'bspg/bspg_keys/credentials.json'

    # The scope for the OAuth2 request.
    SCOPE_GSHEET = ['https://spreadsheets.google.com/feeds',\
        'https://www.googleapis.com/auth/drive']

    # The location of the key file with the key data.
    KEY_FILEPATH_GSHEET = 'bspg/bspg_keys/BSP-Analytics-05a7ae680dc8.json'

    # Defines a method to get an access token from the ServiceAccount object.
    @classmethod
    def get_token(cls,token_type):
        if token_type == "ganalytics":
            return ServiceAccountCredentials.from_json_keyfile_name(cls.KEY_FILEPATH, cls.SCOPE).get_access_token().access_token
        elif token_type == "gsheet":
            return ServiceAccountCredentials.from_json_keyfile_name(cls.KEY_FILEPATH_GSHEET, cls.SCOPE_GSHEET).get_access_token().access_token

    @classmethod
    def get_gs_client(cls):
        creds = ServiceAccountCredentials.from_json_keyfile_name(cls.KEY_FILEPATH_GSHEET, cls.SCOPE_GSHEET)
        client = gspread.authorize(creds)
        return client

    @classmethod
    def get_gs_sheet(cls):
        creds = ServiceAccountCredentials.from_json_keyfile_name(cls.KEY_FILEPATH_GSHEET, cls.SCOPE_GSHEET)
        client = gspread.authorize(creds)
        sheet = client.open('Usecases - Collabs (Responses)').sheet1
        return sheet


    @classmethod
    def convert_to_datetime(cls, data, ftype = "long"):
        dates = []
        for i in data:
            if not i:
                continue
            else:
                if ftype == "long":
                    dates.append(datetime.datetime.strptime(i, '%m/%d/%Y %H:%M:%S'))
                elif ftype == "short":
                    dates.append(datetime.datetime.strptime(i, '%Y-%m-%d'))
        return dates


class FileManager:
    '''
    Manage file reading and writing for the 'bsp_monitor' app
    '''

    # usecase list
    USECASES_JSON = 'bsp_monitor/tools/assets/usecases.json'  
    NAME_CONVENTION = { 
            "brainareacircuitinsilicoexperiments": "Brain Area Circuit In Silico Experiments",
            "mooc": "MOOC", 
            "singlecellmodeling": "Single Cell Modeling",
            "highlyintegratedworkflows": "Highly Integrated Workflows",
            "traceanalysis": "Trace Analysis", 
            "circuitbuilding": "Circuit Building",
            "singlecellinsilicoexperiments": "Single Cell In Silico Experiments",
            "smallcircuitinsilicoexperiments": "Small Circuit In Silico Experiments",
            "morphology": "Morphology",
            "analysisandvisualization": "Analysis and Visualization",
            "modelvalidation": "Model Validation"
            }
    OLD_UC = {
            "Optimize a cerebellar granule cell multicompartmental model with BluePyOpt running on Neuro Science Gateway (NSG)": "singlecellmodeling",
            "Optimise a fast spiking interneuron in the Basal Ganglia":"singlecellmodeling",
            "Synaptic events fitting (user's model)":"traceanalysis",
            "Synaptic events fitting (user's data)":"traceanalysis",
            "singlecellinsilicoexperimentsundercurrent":"singlecellinsilicoexperiments",
            "Single cell in silico experiments under current/voltage clamp":"singlecellinsilicoexperiments",
            "Hodgkin-Huxley Neuron Builder - CDP2 Product 1":"highlyintegratedworkflows",
            "Morphology Analysis":"morphology",
            "Morphology Visualization":"morphology"
            }

    @classmethod
    def get_name_convention(cls):
        return cls.NAME_CONVENTION

    @classmethod
    def get_old_uc_names(cls):
        return cls.OLD_UC

    @classmethod
    def get_uc_json(cls):
        uc_dict = {}
        ff = open(cls.USECASES_JSON)
        uc_main = json.load(ff)
        uc_main = uc_main[0]
        ff.close()
        
        for key in uc_main:
            for crr_uc_k in uc_main[key]:
                uc_dict[crr_uc_k['title']] =  key

        return uc_dict
