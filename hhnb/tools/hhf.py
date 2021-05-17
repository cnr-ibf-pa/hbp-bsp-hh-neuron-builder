# Hippocampus Facility Hub library

import os

from hh_neuron_builder.settings import HHF_TEMPLATE_DIR as HHF_DIR


class HHF:

    def __init__(self):
        self.config_dir = HHF_DIR

    def set_morphology(self, key, name):
