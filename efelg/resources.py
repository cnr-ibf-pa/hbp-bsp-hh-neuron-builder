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
