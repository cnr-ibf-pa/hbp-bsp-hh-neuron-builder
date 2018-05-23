# hbp-bsp-hh-neuron-builder

This project contains the Hodgkin-Huxley Neuron Builder web application integrated in the Human Brain Project - Brain Simulation Platform.

The Web App allows to go through the entire pipeline of a single neuronal cell building: 1) feature extraction; 2) cell optimization; 3) simulation.

The project is implemented via the Django framework and consists of two applications:
  - efelg: to extract electrophysiological features from recorded and/or simulated traces
  - hh-neuron-builder: to go through the neuron builder pipeline. This app integrates efelg in the feature extraction step
  
The project also contains the bsp_monitor web app aiming at visualizing the Brain Simulation Platform usage statistics.
