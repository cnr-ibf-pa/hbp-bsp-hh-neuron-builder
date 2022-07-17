# Model exception definition

class NoModelInstance(Exception):
    pass

class TooManyInstance(Exception):
    pass

class NoMorphologyConfig(Exception):
    pass

class MorphologyConfigError(Exception):
    pass

class InvalidMorphologyDirectory(Exception):
    pass

class InvalidMorphologyFile(Exception):
    pass

class InvalidMechanismFile(Exception):
    pass