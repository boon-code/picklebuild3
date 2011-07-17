
class PickleBuildException(Exception):
    """
    Basic picklebuild exception.
    """
    
    def __init__(self, *args):
        """
        Basic picklebuild exception constructor.
        @param args: These parameter will be passed
                     to the Exception class.
        """
        super(PickleBuildException, self).__init__(*args)


class BasicXmlException(PickleBuildException):
    
    def __init__(self, *args):
        super(BasicXmlException, self).__init__(*args)


class XmlMissingAttributesError(BasicXmlException):
    
    def __init__(self, *args):
        super(XmlMissingAttributesError, self).__init__(*args)
        self.attribute_list = []


class NotYetWorkingWarning(UserWarning):
    pass
