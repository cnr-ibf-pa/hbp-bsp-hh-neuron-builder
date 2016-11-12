from datetime import datetime

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



def string_for_log(page_name, request):
    HXFF = request.META['HTTP_X_FORWARDED_FOR']
    HXFS = request.META['HTTP_X_FORWARDED_SERVER']
    QS = request.META['QUERY_STRING']
    HUA = request.META['HTTP_USER_AGENT']
    HC = request.META['HTTP_COOKIE']
    SN = request.META['SERVER_NAME']
    RA = request.META['REMOTE_ADDR']
    RU = request.META['REQUEST_URI']
    CC = request.META['CSRF_COOKIE']
    final_str = ['PAGE : ' + page_name + ' ' + ' HTTP_X_FORWARDED_FOR ' + HXFF + ' HTTP_X_FORWARDED_SERVER ' + HXFS+ ' QUERY_STRING ' + QS + ' HTTP_USER_AGENT ' + HUA + ' HTTP_COOKIE ' + HC + ' SERVER_NAME ' + SN + ' REMOTE_ADDR ' + RA + ' REQUEST_URI ' + RU + ' CSRF_COOKIE ' + CC + ' user ' + str(request.user) + ' datetime ' + str(datetime.now())]
    return final_str











