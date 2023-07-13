import matplotlib
matplotlib.use('Agg')
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

"""
This optimisation is based on neuron optimisations developed by Etay Hay in the
context of the BlueBrain project
"""

# pylint: disable=R0914, W0403
import os
import sys

import argparse
# pylint: disable=R0914
import logging
logging.basicConfig(stream=sys.stdout)
logger = logging.getLogger()
logger.setLevel(logging.DEBUG)

import bluepyopt

parser = argparse.ArgumentParser(description='Neuron optimization')
parser.add_argument('--start', action="store_true")
parser.add_argument('--resume', action="store_true", default=False)
parser.add_argument(
    '--checkpoint',
    required=False,
    default="./checkpoints/default.pkl",
    help='Checkpoint pickle to avoid recalculation')
parser.add_argument('--offspring_size', type=int, required=False, default=2,
                    help='number of individuals in offspring')
parser.add_argument('--max_ngen', type=int, required=False, default=2,
                    help='maximum number of generations')
parser.add_argument('--nnhof', type=int, required=False, default=1,
                    help='maximum number of analysis')
parser.add_argument('--responses', required=False, default=None,
                    help='Response pickle file to avoid recalculation')
parser.add_argument('--analyse', action="store_true")
parser.add_argument('--evolution', action="store_true")
parser.add_argument('--test', action="store_true")

args = parser.parse_args()


# TODO store definition dicts in json
# TODO rename 'score' into 'objective'
# TODO add functionality to read settings of every object from config format


from model.evaluator import *
from model.template import *
from model.analysis import *

# if args.analyse:
# evaluator = model.evaluator.create('CA1PC', cvode_active=True)
#     evaluator = model.evaluator.create('CA1PC', cvode_active=False, dt=0.025)
# else:

evaluator = model.evaluator.create('W_20230701165623', cvode_active=True, dt=0.025)
#evaluator = model.evaluator.create('CA1PC', cvode_active=True, cvode_minstep=0.025)


def evaluate(parameter_array):
    """Global evaluate function"""

    return evaluator.evaluate(parameter_array)

if os.getenv('USEIPYP') == '1':
    from ipyparallel import Client
    rc = Client(profile=os.getenv('IPYTHON_PROFILE'))
    lview = rc.load_balanced_view()

    map_function = lview.map_sync
else:
    map_function = None

opt = bluepyopt.optimisations.DEAPOptimisation(
    evaluator=evaluator,
    map_function=map_function,
    seed=os.getenv('BLUEPYOPT_SEED'))


def main():
    """Main"""

    if args.start or args.resume:
        logger.debug('Doing start or continue')
        opt.run(max_ngen=args.max_ngen,
                offspring_size=args.offspring_size,
                continue_cp=args.resume,
                cp_filename=args.checkpoint)

    if args.test:
        logger.debug('Doing test')
        import model
        import matplotlib.pyplot as plt

        box = {'left': 0.0,
               'bottom': 0.0,
               'width': 1.0,
               'height': 1.0}

        test_responses_fig = plt.figure(figsize=(10, 10), facecolor='white')
        test_objectives_fig = plt.figure(figsize=(10, 10), facecolor='white')

        model.analysis.analyse_test_model(opt=opt,
                                          figs=((test_responses_fig, box),
                                                (test_objectives_fig, box),
                                                ),
                                          box=box)
        test_objectives_fig.savefig('figures/test_objectives.pdf')
        test_responses_fig.savefig('figures/test_responses.pdf')

    if args.evolution:
        logger.debug('Plotting evolution')
        import model
        import matplotlib.pyplot as plt

        box = {'left': 0.0,
               'bottom': 0.0,
               'width': 1.0,
               'height': 1.0}

        if args.checkpoint is not None and os.path.isfile(args.checkpoint):
            evol_fig = plt.figure(figsize=(10, 10), facecolor='white')

            model.analysis.analyse_evo(cp_filename=args.checkpoint,
                                       figs=(evol_fig, box),)

            evol_fig.savefig('figures/neuron_evolution.pdf')

        else:
            print('No checkpoint file available run optimization '
                  'first with --start')

        plt.show()

    if args.analyse:
        logger.debug('Doing analyse')
        import model
        import matplotlib.pyplot as plt

        box = {'left': 0.0,
               'bottom': 0.0,
               'width': 1.0,
               'height': 1.0}
        setpkl=[f for f in os.listdir(args.checkpoint) if f.endswith('.pkl')]
        if args.checkpoint is not None and not(setpkl)==False : #and os.path.isfile(args.checkpoint):
            a=args.checkpoint
            for l in range(len(setpkl)):
                for j in range(0,args.nnhof):
                    responses_fig = plt.figure(figsize=(10, 10), facecolor='white')
                    objectives_fig = plt.figure(figsize=(10, 10), facecolor='white')
                    evol_fig = plt.figure(figsize=(10, 10), facecolor='white')

                    model.analysis.analyse_cp(opt=opt,
                                              cp_filename=args.checkpoint+os.path.sep+setpkl[l],
                                              responses_filename=args.responses,
                                              figs=((responses_fig, box),
                                                    (objectives_fig, box),
                                                    (evol_fig, box),),nrhof=j)
                
                    responses_fig.savefig('figures/neuron_responses_'+setpkl[l][:setpkl[l].find('.pkl')]+'_'+str(j)+'-'+a[a.find('run'):a.find('r000')-1]+'.pdf')
                    objectives_fig.savefig('figures/neuron_objectives_'+setpkl[l][:setpkl[l].find('.pkl')]+'_'+str(j)+'-'+a[a.find('run'):a.find('r000')-1]+'.pdf')
                    evol_fig.savefig('figures/neuron_evolution_'+setpkl[l][:setpkl[l].find('.pkl')]+'_'+str(j)+'-'+a[a.find('run'):a.find('r000')-1]+'.pdf')
        else:
            print('No checkpoint file available run optimization '
                  'first with --start')

        plt.show()


if __name__ == '__main__':
    main()
