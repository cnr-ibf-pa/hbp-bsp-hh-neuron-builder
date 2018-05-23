import os
import sys
import json
import collections
import neo
import pprint
from datetime import datetime
from . import stimulus_extraction
import requests
from django.conf import settings
if not settings.DEBUG:
    from hbp_app_python_auth.auth import get_auth_header
# create logger
import logging

# set logging up
logging.basicConfig(stream=sys.stdout)
logger = logging.getLogger()
logger.setLevel(logging.DEBUG)

def valid_abf_file(filepath):
    #
    try:
        data = neo.io.AxonIO(filepath)
        segments = data.read_block(lazy=False, cascade=True).segments
       
        assert len(segments[0].analogsignals) >= 2
            
        volt_unit = segments[0].analogsignals[0].units
        volt_unit = str(volt_unit.dimensionality)
        assert volt_unit == 'mV'
        
        amp_unit = segments[0].analogsignals[1].units
        amp_unit = str(amp_unit.dimensionality)
        assert amp_unit == 'nA'

        return True
    except:
        return False


##### check file validity
def check_file_validity(filepath):
    extension = os.path.splitext(os.path.basename(filepath))
    extension = str(extension[1])
    try:
        if extension == '.abf':
            data = neo.io.AxonIO(filepath)
            segments = data.read_block(lazy=False, cascade=True).segments

            volt_unit = segments[0].analogsignals[0].units
            volt_unit = str(volt_unit.dimensionality)
            assert volt_unit == 'mV'
            
            stim_res = stimulus_extraction.stim_feats_from_header(data.read_header()) 
            assert stim_res[0]

            return True
    except:
        return False


##### create string to be printed to log files
def string_for_log(page_name, request, page_spec_string = ''):
    RU = request.META['REQUEST_URI']
    USER = str(request.user)
    DT = str(datetime.now())
    PSS = page_spec_string
    final_dict = collections.OrderedDict()

    final_dict['DT'] = DT
    final_dict['USER'] = USER
    final_dict['RU'] = RU
    final_dict['PSS'] = PSS

    if '?ctx=' in RU:
        PAGE_NAME = 'EFELG_HOMEPAGE'
        QS = request.META['QUERY_STRING']
        HUA = request.META['HTTP_USER_AGENT']
        HC = request.META['HTTP_COOKIE']
        SN = request.META['SERVER_NAME']
        RA = request.META['REMOTE_ADDR']
        CC = request.META['CSRF_COOKIE']
        final_dict['PAGE'] = PAGE_NAME
        final_dict['QS'] = QS
        final_dict['HUA'] = HUA
        final_dict['HC'] = HC
        final_dict['SN'] = SN
        final_dict['RA'] = RA
        final_dict['CC'] = CC
    else:
        PAGE_NAME = RU
        final_dict['PAGE'] = PAGE_NAME

    final_str = json.dumps(final_dict)
        
    return final_str

# author: Luca Leonardo Bologna
def stim_feats_from_meta(stim_feats, num_segments, idx_file):
    if not stim_feats:
        return (0, "Empty metadata in file")
    elif len(stim_feats) - 1 < idx_file and len(stim_feats) !=1: 
        return (0, "Stimulus dictionaries are different from the number of files")
    else: 
        # array for storing all stimulus features 
        all_stim_feats = [] 
        # for every segment in the axon file
        for i in range(num_segments):
            # read current stimulus dict
            if len(stim_feats) == 1:
                crr_dict = stim_feats[0]
            else: 
                crr_dict = stim_feats[idx_file]
                # read stimulus information
            ty = str(crr_dict['stimulus_type'])
            tu = crr_dict['stimulus_time_unit']
            st = crr_dict['stimulus_start']
            en = crr_dict['stimulus_end']
            u = str(crr_dict['stimulus_unit'])
            fa = float(format(crr_dict['stimulus_first_amplitude'], '.3f'))
            inc = float(format(crr_dict['stimulus_increment'], '.3f'))
            ru = crr_dict['sampling_rate_unit']
            r = crr_dict['sampling_rate']
            if tu == 's': 
                st = st * 1e3
                en = en * 1e3
            # compute current stimulus amplitude
            crr_val = float(format(fa + inc * float(format(i, '.3f')), '.3f'))
            crr_stim_feats = (ty, st, en, crr_val, u)
            # store current tuple
            all_stim_feats.append(crr_stim_feats)  
        return (1, all_stim_feats)


# author Luca Leonardo Bologna
def stim_feats_from_header(self, header):
    sampling_rate = 1.e6 / header['protocol']['fADCSequenceInterval'] # read sampling rate
    version = header['fFileVersionNumber'] # read file version
    # extract protocol for version >=.2
    if version >= 2.:     
        #prot = r.read_protocol() # read protocol        
        dictEpochInfoPerDAC = header['dictEpochInfoPerDAC'] # read info for DAC

        # if field is empty
        if not (dictEpochInfoPerDAC):
            return (0, "No 'dictEpochInfoPerDAC' field")
     
        # if field is not empty, read all stimulus segments
        else:     
            valid_epoch_dicts = [k for k, v in dictEpochInfoPerDAC.iteritems() if bool(v)]
     
            # if more than one channel is activated for the stimulus 
            # or a number of epochs different than 3 is found
            if len(valid_epoch_dicts) != 1 or len(dictEpochInfoPerDAC[0]) != 3: 
                return (0, 'Exiting. More than one channel used for stimulation')     
            else:
                stim_epochs = dictEpochInfoPerDAC[k] # read all stimulus epochs                
                stim_ch_info = [(i['DACChNames'], i['DACChUnits'], i['nDACNum']) for i in header['listDACInfo'] if bool(i['nWaveformEnable'])] # read enabled waveforms

                # if epoch initial levels and increment are not compatible with a step stimulus
                if (stim_epochs[0]['fEpochInitLevel'] != stim_epochs[2]['fEpochInitLevel'] or
                    stim_epochs[0]['fEpochLevelInc'] != stim_epochs[2]['fEpochLevelInc'] or
                    float(format(stim_epochs[0]['fEpochLevelInc'], '.3f')) != 0 or 
                    (len(stim_ch_info) != 1 or stim_ch_info[0][2] != k)): 
                        # return 0 with message      
                        return (0, "A stimulus different from the steps has been detected") 

	   	else:
                    ty = "step"
                    u = stim_ch_info[0][1]
                    nADC = header['sections']['ADCSection']['llNumEntries'] # number of ADC channels
                    nDAC = header['sections']['DACSection']['llNumEntries'] # number of DAC channels
                    nSam = header['protocol']['lNumSamplesPerEpisode']/nADC # number of samples per episode
                    nEpi = header['lActualEpisodes'] # number of actual episodes

                    e_zero = header['dictEpochInfoPerDAC'][stim_ch_info[0][2]][0] # read first stimulus epoch
                    e_one = header['dictEpochInfoPerDAC'][stim_ch_info[0][2]][1] # read second stimulus epoch
                    e_two = header['dictEpochInfoPerDAC'][stim_ch_info[0][2]][2] # read third stimulus epoch

                    i_last = int(nSam*15625/10**6) # index of stimulus beginning

                    all_stim_info = [] # create array for all stimulus info

                    e_one_inc = float(format(e_one['fEpochLevelInc'] , '.3f')) # step increment
                    e_one_init_level = float(format(e_one['fEpochInitLevel'] , '.3f')) # step initial level

                    # for every episode, compute stimulus start, stimulus end, stimulus value
                    for epiNum in range(nEpi):
                        st = i_last + e_zero['lEpochInitDuration'] + e_zero['lEpochDurationInc'] * epiNum
                        en = st + e_one['lEpochInitDuration'] +  e_one['lEpochDurationInc'] * epiNum
                        crr_val_full = float(format(e_one_init_level + e_one_inc * epiNum, '.3f'))
                        crr_val = float(format(crr_val_full, '.3f'))
                        st = 1/sampling_rate * st * 1e3
                        en = 1/sampling_rate * en * 1e3
                        all_stim_info.append((ty, st, en, crr_val, u))
                    return (1, all_stim_info)


def user_collab_list(my_collabs_url, social_auth):
    auth_data_list = []
    headers = {'Authorization': get_auth_header(social_auth)}
    res_mine = requests.get(my_collabs_url, headers = headers)
                   
    resp_mine = res_mine.json()
    for i in resp_mine['results']:
        auth_data_list.append(i['id'])

    return auth_data_list


def print_citations(json_file_list, conf_file, final_file):
    final_citations = {}
    with open(conf_file) as f:
        all_citations = json.load(f)

    for i in json_file_list:
        fin_key = i + '.json'
        if not fin_key in all_citations:
            continue
        crr_ref = all_citations[fin_key]
        crr_cit = crr_ref.keys()[0]
        if crr_cit not in final_citations:
            final_citations[crr_cit] = []
            final_citations[crr_cit].append(i)
        else:
            final_citations[crr_cit].append(i)

    with open(final_file, 'w') as tf:
        for key, val in final_citations.iteritems():
            tf.write("For the following data:\n")
            for i in val:
                tf.write(i + "\n")
            tf.write("\n")
            tf.write("Use the following reference:\n\n")
            tf.write(key + "\n\n")
            tf.write("===========\n\n")







