import os

Template = None
moduleDirectory = os.path.dirname(__file__) + "/cache"

class View(object):
    viewCallbacks = []
    def __init__(self, viewCallbacks):
        self.viewCallbacks = viewCallbacks
        
    def invoke(self, obj):
        global moduleDirectory
        global Template
        result = ""
        for viewCallback in self.viewCallbacks:
            if isinstance(viewCallback, str):
                if Template is None:
                    Template = __import__('mako.template', fromlist=['Template'])
                template = Template(filename=viewCallback, moduleDirectory=moduleDirectory)
                result = result + template.render(obj=obj)
            elif hasattr(viewCallback, '__call__'):
                result = result + viewCallback(obj)
        return result
    
    @staticmethod    
    def render(obj, templateName):
        global Template
        if Template is None:
            Template = __import__('mako.template', fromlist=['Template'])
        template = Template(filename=viewCallback, moduleDirectory=moduleDirectory)
        return template.render(obj=obj)            