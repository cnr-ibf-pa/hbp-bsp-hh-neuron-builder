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


class MechanismsProcessError(CalledProcessError):
    pass


class AnalysisProcessError(CalledProcessError):
    pass


class UnknownParametersTemplate(Exception):
    pass