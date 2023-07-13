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


# pylint: disable=R0914, W0633

import os
import pickle
import numpy as np
import bluepyopt.ephys as ephys

import logging
logger = logging.getLogger(__name__)

import time

script_dir = os.path.join(os.path.dirname(__file__), '../')
config_dir = os.path.join(script_dir, 'config')

# Parameters in release circuit model
test_params = {
    'g_pas.all': 4.99851e-05,
    'e_pas.all': -109.762,
    'Ra.all': 100,
    'gk_bar_kdr2_hip.axonal': 0.351052,
    'gna_bar_na_hip.axonal': 1.77172,
    'gk_bar_km2_hip.axonal': 0.000200398,
    'gk_bar_kap2_hip.axonal': 0.00117191,
    'gk_bar_kdr2_hip.somatic': 0.409262,
    'gna_bar_na_hip.somatic': 0.0020003,
    'gk_bar_km2_hip.somatic': 2.02927e-06,
    'gk_bar_kap2_hip.somatic': 3.28558e-05,
    'gh_bar_h_hip.somatic': 0.000106515,
    'gca_bar_cahva_hip.somatic': 0.00251479,
    'gca_bar_calva_hip.somatic': 0.00021593,
    'gk_bar_sk_hip.somatic': 0.01,
    'gk_bar_kap2_hip.basal': 0.000463984,
    'gk_bar_kad2_hip.apical': 7.02041e-05,
    'gh_bar_h_hip.basal': 1.78331e-05,
    'gh_bar_h_hip.apical': 1.78331e-05,
    'gk_bar_kdr2_hip.alldend': 0.00468222,
    'gna_bar_na_hip.alldend': 0.00582477,
    'gca_bar_cahva_hip.alldend': 4.10514e-06,
    'gca_bar_calva_hip.alldend': 0.000109139,
    'gk_bar_sk_hip.alldend': 0.01,
}


def set_rcoptions(func):
    '''decorator to apply custom matplotlib rc params to function, undo after'''
    import matplotlib

    def wrap(*args, **kwargs):
        """Wrap"""
        options = {'axes.linewidth': 2, }
        with matplotlib.rc_context(rc=options):
            func(*args, **kwargs)
    return wrap


def get_responses(cell_evaluator, individuals, filename):

    responses = []
    if filename and os.path.exists(filename):
        with open(filename) as fd:
            return pickle.load(fd)

    for individual in individuals:
        individual_dict = cell_evaluator.param_dict(individual)
        responses.append(
            cell_evaluator.run_protocols(
                cell_evaluator.fitness_protocols.values(),
                param_values=individual_dict))

    if filename:
        with open(filename, 'w') as fd:
            pickle.dump(responses, fd)

    return responses


@set_rcoptions
def analyse_evo(cp_filename, figs):
    """Analyse optimisation results"""
    (evol_fig, evol_box) = figs

    cp = pickle.load(open(cp_filename, "r"))
    plot_log(cp['logbook'], fig=evol_fig, box=evol_box)


@set_rcoptions
def analyse_cp(opt, cp_filename, responses_filename, figs, nrhof):
    """Analyse optimisation results"""
    (model_fig, model_box), (objectives_fig, objectives_box), (
        evol_fig, evol_box) = figs

    cp = pickle.load(open(cp_filename, "rb"),encoding="latin1")

    hof = cp['halloffame']
    #responses = get_responses(opt.evaluator, hof, responses_filename)
    replace_axon_hoc = """
    proc replace_axon(){local nSec, L_chunk, dist, i1, i2, count, L_target, chunkSize, L_real localobj diams, lens

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

//         access axon[0]
//         i1 = v(0.0001) // used when serializing sections prior to sim start

//         access axon[1]
//         i2 = v(0.0001) // used when serializing sections prior to sim start

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

         print "Target stub axon length:", L_target, "um, equivalent length: ", L_real "um"
     }

 }

    """
    #opt.evaluator.cell_model.morphology.replace_axon.func_globals['NrnFileMorphology'].default_replace_axon_hoc=replace_axon_hoc
    opt.evaluator.cell_model.morphology.replace_axon_hoc=replace_axon_hoc
    # objectives
    print('nrhof',nrhof)
    parameter_values = opt.evaluator.param_dict(hof[nrhof])
    fitness_protocols = opt.evaluator.fitness_protocols
    responses = {}

    hoccode =  opt.evaluator.cell_model.create_hoc(param_values=parameter_values)
    cp_dir = os.path.dirname(cp_filename)

    with open(cp_dir + "/cell_"+os.path.split(cp_filename)[1][:os.path.split(cp_filename)[1].find('.pkl')]+'_'+str(nrhof)+'.hoc', "w") as f:
        f.write(hoccode)

    logger.info('Running best model with sum %s',
                sum(hof[nrhof].fitness.values))

    logger.info('Objectives: %s',
                opt.evaluator.objective_dict(hof[nrhof].fitness.values))
    traces=[]
    for protocol in fitness_protocols.values():
        start_time = time.time()
        response = protocol.run(
            cell_model=opt.evaluator.cell_model,
            param_values=parameter_values,
            sim=opt.evaluator.sim)
        responses.update(response)
        logger.info(" Ran protocol in %f seconds",
                        time.time() - start_time)
        traces.append(list(response.keys())[0])
    objectives = opt.evaluator.fitness_calculator.calculate_scores(responses)

    plot_objectives(objectives, fig=objectives_fig, box=objectives_box)
    stimord={} 
    for i in range(len(traces)): 
        stimord[i]=traces[i]
    import operator 
    sorted_stimord = sorted(stimord.items(), key=operator.itemgetter(1)) 
    traces2=[] 
    for i in range(len(sorted_stimord)): 
        traces2.append(traces[sorted_stimord[i][0]])     
    traces=traces2 
    plot_multiple_responses([responses], cp_filename, fig=model_fig, traces=traces)

    plot_log(cp['logbook'], fig=evol_fig, box=evol_box)


def plot_log(log, fig=None, box=None):
    """Plot logbook"""

    gen_numbers = log.select('gen')
    mean = np.array(log.select('avg'))
    std = np.array(log.select('std'))
    minimum = np.array(log.select('min'))

    left_margin = box['width'] * 0.1
    right_margin = box['width'] * 0.05
    top_margin = box['height'] * 0.05
    bottom_margin = box['height'] * 0.1

    axes = fig.add_axes(
        (box['left'] + left_margin,
         box['bottom'] + bottom_margin,
         box['width'] - left_margin - right_margin,
         box['height'] - bottom_margin - top_margin))

    stdminus = mean - std
    stdplus = mean + std
    axes.plot(
        gen_numbers,
        mean,
        color='black',
        linewidth=2,
        label='population average')

    axes.fill_between(
        gen_numbers,
        stdminus,
        stdplus,
        color='lightgray',
        linewidth=2,
        label=r'population standard deviation')

    axes.plot(
        gen_numbers,
        minimum,
        color='red',
        linewidth=2,
        label='population minimum')

    axes.set_xlim(min(gen_numbers) - 1, max(gen_numbers) + 1)
    axes.set_xlabel('Generation #')
    axes.set_ylabel('Sum of objectives')
    axes.set_ylim([0, max(stdplus)])
    axes.legend()


def plot_history(history):
    """Plot the history of the individuals"""

    import networkx

    import matplotlib.pyplot as plt
    plt.figure()

    graph = networkx.DiGraph(history.genealogy_tree)
    graph = graph.reverse()     # Make the grah top-down
    # colors = [\
    #        toolbox.evaluate(history.genealogy_history[i])[0] for i in graph]
    positions = networkx.graphviz_layout(graph, prog="dot")
    networkx.draw(graph, positions)


def plot_objectives(objectives, fig=None, box=None):
    """Plot objectives of the cell model"""

    import collections
    objectives = collections.OrderedDict(sorted(objectives.items()))
    left_margin = box['width'] * 0.4
    right_margin = box['width'] * 0.05
    top_margin = box['height'] * 0.05
    bottom_margin = box['height'] * 0.1

    axes = fig.add_axes(
        (box['left'] + left_margin,
         box['bottom'] + bottom_margin,
         box['width'] - left_margin - right_margin,
         box['height'] - bottom_margin - top_margin))

    ytick_pos = [x + 0.5 for x in range(len(objectives.keys()))]

    axes.barh(ytick_pos,
              objectives.values(),
              height=0.5,
              align='center',
              color='#779ECB')
    axes.set_yticks(ytick_pos)
    axes.set_yticklabels(objectives.keys(), size='x-small')
    axes.set_ylim(-0.5, len(objectives.values()) + 0.5)
    axes.set_xlabel('Objective value (# std)')
    axes.set_ylabel('Objectives')

    logger.info('Sum of objectives %f (# std)',
                sum(objectives.values()))


def plot_responses(responses, fig=None, box=None):
    """Plot responses of the cell model"""
    rec_rect = {}
    rec_rect['left'] = box['left']
    rec_rect['width'] = box['width']
    rec_rect['height'] = float(box['height']) / len(responses)
    rec_rect['bottom'] = box['bottom'] + \
        box['height'] - rec_rect['height']
    last = len(responses) - 1
    for i, (_, recording) in enumerate(sorted(responses.items())):
        plot_recording(recording, fig=fig, box=rec_rect, xlabel=(last == i))
        rec_rect['bottom'] -= rec_rect['height']


def get_slice(start, end, data):
    return slice(np.searchsorted(data, start),
                 np.searchsorted(data, end))


def plot_multiple_responses(responses, cp_filename, fig, traces):
    import pandas as pd
    '''creates subplots'''
   
   
   
    plot_count = len(traces)
    ax = [fig.add_subplot(plot_count, 1, i + 1) for i in range(plot_count)]
    overlay_count = len(responses)
    for i, response in enumerate(reversed(responses[:overlay_count])):
        crr_resp_str = 'r_' +os.path.split(cp_filename)[1][:os.path.split(cp_filename)[1].find('.pkl')]+'_'+str(i) # llb
        data_fold_name = crr_resp_str 
        if not os.path.exists(data_fold_name):
            os.makedirs(data_fold_name)
        color = 'lightblue'
        if i == overlay_count - 1:
            color = 'blue'

        for i, name in enumerate(traces):
            crr_t = response[name]['time']
            crr_v = response[name]['voltage']
            # llb start
           
            fin_na = np.array(crr_t)
            fin_na = np.c_[fin_na, crr_v]
            filename = os.path.join(data_fold_name, name + '.txt')
            df = pd.DataFrame(fin_na, columns=['t', 'v']) # llb
            df.to_csv(filename, index=False, header=True, sep=' ') # llb
        
            # llb end   
            #sl = get_slice(0, 3000, response[name]['time'])
            ax[i].plot(
                response[name]['time'],  # [sl],
                response[name]['voltage'],  # [sl],
                color=color,
                linewidth=1)
            ax[i].set_ylabel(name + '\nVoltage (mV)')
            ax[i].set_autoscaley_on(True)
            ax[i].set_autoscalex_on(True)
            #ax[i].set_ylim((-85, 50))
        ax[-1].set_xlabel('Time (ms)')
    

def plot_recording(recording, fig=None, box=None, xlabel=False):
    """Plot responses of the cell model"""

    import matplotlib.pyplot as plt

    left_margin = box['width'] * 0.25
    right_margin = box['width'] * 0.05
    top_margin = box['height'] * 0.1
    bottom_margin = box['height'] * 0.25

    axes = fig.add_axes(
        (box['left'] + left_margin,
         box['bottom'] + bottom_margin,
         box['width'] - left_margin - right_margin,
         box['height'] - bottom_margin - top_margin))

    recording.plot(axes)
    axes.set_ylim(-100, 40)
    axes.spines['top'].set_visible(False)
    axes.spines['right'].set_visible(False)
    axes.tick_params(
        axis='both',
        bottom='on',
        top='off',
        left='on',
        right='off')

    name = recording.name
    if name.endswith('.v'):
        name = name[:-2]

    axes.set_ylabel(name + '\n(mV)', labelpad=25)
    yloc = plt.MaxNLocator(2)
    axes.yaxis.set_major_locator(yloc)

    if xlabel:
        axes.set_xlabel('Time (ms)')


@set_rcoptions
def analyse_test_model(opt, figs, box=None, hoc=False):
    """Analyse test model"""
    (release_responses_fig, response_box), (
        release_objectives_fig, objectives_box) = figs

    fitness_protocols = opt.evaluator.fitness_protocols

    nrn = ephys.simulators.NrnSimulator(cvode_active=False, dt=0.025)

    morph = opt.evaluator.cell_model.morphology.morphology_path
    if hoc:
        nrn.neuron.h.celsius = 34
        nrn.neuron.h.v_init = -80
        cell_model = ephys.models.HocCellModel('hoc', morph, hoc)
    else:
        cell_model = opt.evaluator.cell_model

    responses = {}
    for protocol in fitness_protocols.values():
        response = protocol.run(
            cell_model=cell_model,
            param_values=test_params,
            sim=nrn)
        responses.update(response)

    plot_multiple_responses([responses], fig=release_responses_fig)

    objectives = opt.evaluator.fitness_calculator.calculate_scores(responses)
    plot_objectives(objectives, fig=release_objectives_fig, box=objectives_box)


FITNESS_CUT_OFF = 5


def plot_individual_params(
        ax,
        params,
        marker,
        color,
        markersize=40,
        plot_bounds=False,
        fitness_cut_off=FITNESS_CUT_OFF):
    '''plot the individual parameter values'''
    observations_count = len(params)
    param_count = len(params[0])

    results = np.zeros((observations_count, param_count))
    good_fitness = 0
    for i, param in enumerate(params):
        if fitness_cut_off < max(param.fitness.values):
            continue
        results[good_fitness] = param
        good_fitness += 1

    results = np.log(results)

    for c in range(good_fitness):
        x = np.arange(param_count)
        y = results[c, :]
        ax.scatter(x=x, y=y, s=float(markersize), marker=marker, color=color)

    if plot_bounds:
        def plot_tick(column, y):
            col_width = 0.25
            x = [column - col_width,
                 column + col_width]
            y = [y, y]
            ax.plot(x, y, color='black')

        # plot min and max
        for i in range(param_count):
            min_value = np.min(results[0:good_fitness, i])
            max_value = np.max(results[0:good_fitness, i])
            plot_tick(i, min_value)
            plot_tick(i, max_value)


def plot_diversity(checkpoint_file, fig, param_names):
    '''plot the whole history, the hall of fame, and the best individual
    from a unpickled checkpoint
    '''
    import matplotlib.pyplot as plt
    checkpoint = pickle.load(open(checkpoint_file, "r"))

    ax = fig.add_subplot(1, 1, 1)
    plot_individual_params(ax, checkpoint['history'].genealogy_history.values(),
                           marker='.', color='grey', plot_bounds=True)
    plot_individual_params(ax, checkpoint['halloffame'],
                           marker='o', color='black')
    plot_individual_params(ax, [checkpoint['halloffame'][0]], markersize=150,
                           marker='x', color='blue')

    labels = [name.replace('.', '\n') for name in param_names]

    param_count = len(checkpoint['halloffame'][0])
    x = range(param_count)
    for xline in x:
        ax.axvline(xline, linewidth=1, color='grey', linestyle=':')

    plt.xticks(x, labels, rotation=80, ha='center', size='small')
    ax.set_xlabel('Parameters')
    ax.set_ylabel('log Parameter value')
    ax.set_ylim((-15, 8))

    plt.tight_layout()
    plt.plot()
    ax.set_autoscalex_on(True)
    
    
def plot_multiple_responses2(responses, traces, fig):
    import pandas as pd
    '''creates subplots'''
    plot_count = len(traces)
    ax = [fig.add_subplot(plot_count, 1, i + 1) for i in range(plot_count)]
    overlay_count = len(responses)
    for i, response in enumerate(reversed(responses[:overlay_count])):
        crr_resp_str = 'r_' + str(i) # llb
        data_fold_name = crr_resp_str 
        if not os.path.exists(data_fold_name):
            os.makedirs(data_fold_name)
        color = 'lightblue'
        if i == overlay_count - 1:
            color = 'blue'

        for i, name in enumerate(traces):
            crr_t = response[name]['time']
            crr_v = response[name]['voltage']
            crr_v=crr_v[crr_t[crr_t>=500].index[0]:crr_t[crr_t<=1031].index[len(crr_t[crr_t<=1031].index)-1]]
            crr_t=crr_t[crr_t[crr_t>=500].index[0]:crr_t[crr_t<=1031].index[len(crr_t[crr_t<=1031].index)-1]]
            # llb start
           
            fin_na = np.array(crr_t)
            fin_na = np.c_[fin_na, crr_v]
            filename = os.path.join(data_fold_name, name + '.txt')
            df = pd.DataFrame(fin_na, columns=['t', 'v']) # llb
            df.to_csv(filename, index=False, header=True, sep=' ') # llb
        
            # llb end   
            #sl = get_slice(0, 3000, response[name]['time'])
            ax[i].plot(
                crr_t,  # [sl],
                crr_v,  # [sl],
                color=color,
                linewidth=1)
            ax[i].set_title(name,position=(0.9, 0.6))
            ax[i].set_autoscaley_on(True)
            ax[i].set_autoscalex_on(True)
            ax[i].set_xlim((500, 1031))
        ax[-1].set_xlabel('Time (ms)')
        ax[1].set_ylabel('Voltage (mV)')
