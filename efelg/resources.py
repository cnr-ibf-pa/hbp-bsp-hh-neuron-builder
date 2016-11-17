from datetime import datetime
import json
import collections
# create logger



def valid_abf_file(filepath):
    import neo # to leave here or to move somewhere else

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



def string_for_log(page_name, request, page_spec_string = ''):
    RU = request.META['REQUEST_URI']
    #HXFF = request.META['HTTP_X_FORWARDED_FOR']
    USER = str(request.user)
    DT = str(datetime.now())
    PSS = page_spec_string
    final_dict = collections.OrderedDict()

    final_dict['DT'] = DT
    final_dict['USER'] = USER
    #final_dict['HXFF'] = HXFF
    final_dict['RU'] = RU
    final_dict['PSS'] = PSS



    if '?ctx=' in RU:
        PAGE_NAME = 'EFELG_HOMEPAGE'
        #HXFS = request.META['HTTP_X_FORWARDED_SERVER']
        QS = request.META['QUERY_STRING']
        HUA = request.META['HTTP_USER_AGENT']
        HC = request.META['HTTP_COOKIE']
        SN = request.META['SERVER_NAME']
        RA = request.META['REMOTE_ADDR']
        CC = request.META['CSRF_COOKIE']
        final_dict['PAGE'] = PAGE_NAME
        #final_dict['HXFS'] = HXFS
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











