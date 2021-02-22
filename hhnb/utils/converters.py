# Useful class to convert urls parameter


class ExcConverter:
    regex = 'tab_[0-9]{14}'

    def to_python(self, value):
        return value

    def to_url(self, value):
        return value


class CtxConverter:
    """
    Unsed due to uuid built-in converter
    """
    regex = '[0-9a-zA-Z]{8}-[0-9a-zA-Z]{4}-[0-9a-zA-Z]{4}-[0-9a-zA-Z]{4}-[0-9a-zA-Z]{12}'

    def to_python(self, value):
        return value

    def to_url(self, value):
        return value


class AnyCharConvert:
    regex = '.*'

    def to_python(self, value):
        return value

    def to_url(self, value):
        return value


class NewOrCloneConvert:
    regex = 'new|cloned'

    def to_python(self, value):
        return value

    def to_url(self, value):
        return value


class FeatOrOptsetOrModsimConverter:
    regex = 'feat|optset|modsim'

    def to_python(self, value):
        print(self.__class__, value)
        return value

    def to_url(self, value):
        print(self.__class__, value)
        return value


class FeatOrOptsetOrModsimOrOptresConverter:
    regex = 'feat|optset|modsim|optres'

    def to_python(self, value):
        return value

    def to_url(self, value):
        return value


class SourceOptConverter:
    regex = '[_a-zA-Z0-9\-.]*'

    def to_python(self, value):
        return value

    def to_url(self, value):
        return value


class WorkflowIdConverter:
    regex = '[0-9]{14}_[0-9]+'

    def to_python(self, value):
        return value

    def to_url(self, value):
        return value


class CurrentOrStorageCollabConverter:
    regex = 'current_collab|storage_collab'

    def to_python(self, value):
        return value

    def to_url(self, value):
        return value

class HpcConverter:
    regex = 'DAINT-CSCS|SA-CSCS|NSG'

    def to_python(self, value):
        return value

    def to_url(self, value):
        return value
