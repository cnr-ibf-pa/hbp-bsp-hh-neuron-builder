from subprocess import CalledProcessError


# Workflow exception definition

class WorkflowExists(Exception):
    pass


class PathExists(Exception):
    pass


class NoWorkflowFound(Exception):
    pass


class EmptyWorkflow(Exception):
    pass


class MechanismsProcessError(Exception): # CalledProcessError):
    pass


class AnalysisProcessError(Exception): # CalledProcessError):
    pass


class UnknownParametersTemplate(Exception):
    pass