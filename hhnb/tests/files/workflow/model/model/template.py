"""Run simple cell optimisation"""

"""
Copyright (c) 2016, EPFL/Blue Brain Project

 This file is part of BluePyOpt <https://github.com/BlueBrain/BluePyOpt>

 This library is free software; you can redistribute it and/or modify it under
 the terms of the GNU Lesser General Public License version 3.0 as published
 by the Free Software Foundation.

 This library is distributed in the hope that it will be useful, but WITHOUT
 ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
 FOR A PARTICULAR PURPOSE.  See the GNU Lesser General Public License for more
 details.

 You should have received a copy of the GNU Lesser General Public License
 along with this library; if not, write to the Free Software Foundation, Inc.,
 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.
"""
# pylint: disable=R0914

import os

try:
    import simplejson as json
except:
    import json

import bluepyopt.ephys as ephys

script_dir = os.path.join(os.path.dirname(__file__), '../')
config_dir = os.path.join(script_dir, 'config')

# TODO store definition dicts in json
# TODO rename 'score' into 'objective'
# TODO add functionality to read settings of every object from config format

import collections

import logging
logger = logging.getLogger(__name__)

def multi_locations(sectionlist):
    """Define mechanisms"""

    if sectionlist == "alldend":
        seclist_locs = [
            ephys.locations.NrnSeclistLocation("apical", seclist_name="apical"),
            ephys.locations.NrnSeclistLocation("basal", seclist_name="basal")
            ]
    elif sectionlist == "allnoaxon":
        seclist_locs = [
            ephys.locations.NrnSeclistLocation("apical", seclist_name="apical"),
            ephys.locations.NrnSeclistLocation("basal", seclist_name="basal"),
            ephys.locations.NrnSeclistLocation("somatic", seclist_name="somatic")
            ]
    else:
        seclist_locs = [ephys.locations.NrnSeclistLocation(
            sectionlist,
            seclist_name=sectionlist)]

    return seclist_locs


def define_mechanisms(etype):
    """Define mechanisms"""

    params_path = os.path.join(config_dir, 'parameters.json')
    with open(params_path, 'r') as params_file:
        mech_definitions = json.load(
            params_file,
            object_pairs_hook=collections.OrderedDict)[etype]["mechanisms"]

    mechanisms = []
    for sectionlist, channels in mech_definitions.items():
        seclist_locs = multi_locations(sectionlist)
        for channel in channels:
            mechanisms.append(ephys.mechanisms.NrnMODMechanism(
                name='%s.%s' % (channel, sectionlist),
                mod_path=None,
                prefix=channel,
                locations=seclist_locs,
                preloaded=True))

    return mechanisms


def define_parameters(etype):
    """Define parameters"""

    params_path = os.path.join(config_dir, 'parameters.json')
    with open(params_path, 'r') as params_file:
        definitions = json.load(
            params_file,
            object_pairs_hook=collections.OrderedDict)[etype]

    # set distributions
    distributions = collections.OrderedDict()
    distributions["uniform"] = ephys.parameterscalers.NrnSegmentLinearScaler()

    distributions_definitions = definitions["distributions"]
    for distribution, definition in distributions_definitions.items():
        distributions[distribution] = ephys.parameterscalers.NrnSegmentSomaDistanceScaler(
                                            distribution=definition)

    parameters = []

    # set fixed parameters
    fixed_params_definitions = definitions["fixed"]
    for sectionlist, params in fixed_params_definitions.items():
        if sectionlist == 'global':
            for param_name, value in params:
                parameters.append(
                    ephys.parameters.NrnGlobalParameter(
                        name=param_name,
                        param_name=param_name,
                        frozen=True,
                        value=value))
        else:
            seclist_locs = multi_locations(sectionlist)

            for param_name, value, dist in params:

                if dist == "secvar": # this is a section variable, no distribution possible
                    parameters.append(ephys.parameters.NrnSectionParameter(
                        name='%s.%s' % (param_name, sectionlist),
                        param_name=param_name,
                        value=value,
                        frozen=True,
                        locations=seclist_locs))

                else:
                    parameters.append(ephys.parameters.NrnRangeParameter(
                        name='%s.%s' % (param_name, sectionlist),
                        param_name=param_name,
                        value_scaler=distributions[dist],
                        value=value,
                        frozen=True,
                        locations=seclist_locs))

    # Compact parameter description
    # Format ->
    # - Root dictionary: keys = section list name,
    #                    values = parameter description array
    # - Parameter description array: prefix, parameter name, minbound, maxbound

    parameter_definitions = definitions["optimized"]

    for sectionlist, params in parameter_definitions.items():
        seclist_loc = ephys.locations.NrnSeclistLocation(
            sectionlist,
            seclist_name=sectionlist)

        seclist_locs = multi_locations(sectionlist)

        for param_name, min_bound, max_bound, dist in params:

            if dist == "secvar": # this is a section variable, no distribution possible
                parameters.append(ephys.parameters.NrnSectionParameter(
                    name='%s.%s' % (param_name, sectionlist),
                    param_name=param_name,
                    bounds=[min_bound, max_bound],
                    locations=seclist_locs))

            else:
                parameters.append(ephys.parameters.NrnRangeParameter(
                    name='%s.%s' % (param_name, sectionlist),
                    param_name=param_name,
                    value_scaler=distributions[dist],
                    bounds=[min_bound, max_bound],
                    locations=seclist_locs))

            logger.debug('Setting %s.%s in model.template.define_parameters()',
                         param_name, sectionlist)


    return parameters

from bluepyopt.ephys.morphologies import NrnFileMorphology

class NrnFileMorphologyCustom(NrnFileMorphology):
    @staticmethod
    def replace_axon(sim=None, icell=None):
        """Replace axon"""

        L_target = 60  # length of stub axon
        nseg0 = 5  # number of segments for each of the two axon sections

        nseg_total = nseg0 * 2
        chunkSize = L_target / nseg_total

        diams = []
        lens = []

        count = 0
        for section in icell.axonal:
            L = section.L
            nseg = 1 + int(L / chunkSize / 2.) * 2  # nseg to get diameter
            section.nseg = nseg

            for seg in section:
                #seg.x, seg.diam
                diams.append(seg.diam)
                lens.append(L / nseg)
                if count == nseg_total:
                    break
            if count == nseg_total:
                break

        for section in icell.axonal:
            sim.neuron.h.delete_section(sec=section)

        #  new axon array
        sim.neuron.h.execute('create axon[2]', icell)

        L_real = 0
        count = 0

        for index, section in enumerate(icell.axon):
            section.nseg = int(nseg_total / 2)
            section.L = L_target / 2

            for seg in section:
                seg.diam = diams[count]
                L_real = L_real + lens[count]
                count = count + 1
                # print seg.x, seg.diam

            icell.axonal.append(sec=section)
            icell.all.append(sec=section)

        icell.axon[0].connect(icell.soma[0], 1.0, 0.0)
        icell.axon[1].connect(icell.axon[0], 1.0, 0.0)

        logger.debug(
            'Replace axon with tapered AIS of length %f, target length was %f, diameters are %s' %
            (L_real, L_target, diams))

        

def define_morphology(etype):
    """Define morphology"""
    default_replace_axon_hoc = """
        proc replace_axon(){ local nSec, L_chunk, dist, i1, i2, count, L_target, chunkSize, L_real localobj diams, lens

            L_target = 60  // length of stub axon
            nseg0 = 5  // number of segments for each of the two axon sections

            nseg_total = nseg0 * 2
            chunkSize = L_target/nseg_total

            nSec = 0
            forsec axonal{nSec = nSec + 1}

            // Try to grab info from original axon
            if(nSec < 1){ //At least two axon sections have to be present!

                execerror("Less than two axon sections are present! Add an axon to the morphology and try again!")

            } else {

                diams = new Vector()
                lens = new Vector()

                access axon[0]
                i1 = v(0.0001) // used when serializing sections prior to sim start

                access axon[1]
                i2 = v(0.0001) // used when serializing sections prior to sim start

                count = 0
                forsec axonal{ // loop through all axon sections

                    nseg = 1 + int(L/chunkSize/2.)*2  //nseg to get diameter

                for (x) {
                    if (x > 0 && x < 1) {
                        count = count + 1
                        diams.resize(count)
                        diams.x[count-1] = diam(x)
                        lens.resize(count)
                        lens.x[count-1] = L/nseg
                        if( count == nseg_total ){
                            break
                        }
                    }
                }
                if( count == nseg_total ){
                    break
                }
            }

                // get rid of the old axon
                forsec axonal{delete_section()}
                execute1("create axon[2]", CellRef)

                L_real = 0
                count = 0

                // new axon dependant on old diameters
                for i=0,1{
                    access axon[i]
                    L =  L_target/2
                    nseg = nseg_total/2

                    for (x) {
                        if (x > 0 && x < 1) {
                            diam(x) = diams.x[count]
                            L_real = L_real+lens.x[count]
                            count = count + 1
                        }
                    }

                    all.append()
                    axonal.append()

                    if (i == 0) {
                        v(0.0001) = i1
                    } else {
                        v(0.0001) = i2
                    }
                }

                nSecAxonal = 2
                soma[0] connect axon[0](0), 1
                axon[0] connect axon[1](0), 1

                //print 'Target stub axon length:', L_target, 'um, equivalent length: ', L_real 'um'
            }
        }
        """

    morph_path = os.path.join(config_dir, 'morph.json')
    with open(morph_path, 'r') as morphologies_file:
        morphologies = json.load(
            morphologies_file,
            object_pairs_hook=collections.OrderedDict)

    return NrnFileMorphologyCustom(
        str(os.path.join(
            script_dir,
            'morphology/',
            morphologies[etype])),
        do_replace_axon=True,
        replace_axon_hoc=default_replace_axon_hoc)


def create(etype):
    """Create cell model"""

    cell = ephys.models.CellModel(
        etype,
        morph=define_morphology(etype),
        mechs=define_mechanisms(etype),
        params=define_parameters(etype))

    return cell
