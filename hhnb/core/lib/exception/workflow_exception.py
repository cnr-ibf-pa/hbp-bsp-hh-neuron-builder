# Workflow exception definition

class WorkflowExists(Exception):
    pass


class PathExists(Exception):
    pass


class NoWorkflowFound(Exception):
    pass


class EmptyWorkflow(Exception):
    pass