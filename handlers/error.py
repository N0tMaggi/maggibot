# universal erro handler for all errors

import logging
import sys
import traceback
import json
from debug import LogDebug



def error_handler(error):
    if error != None:
        try:
            LogDebug("Error: " + str(error))
            LogDebug("Error: " + str(error.__class__.__name__))
            LogDebug("Error: " + str(error.__cause__))
            LogDebug("Error: " + str(error.__context__))
            LogDebug("Error: " + str(error.__dict__))
            LogDebug("Error: " + str(error.__traceback__))
            LogDebug("Error: " + str(error.__str__()))
            LogDebug("Error: " + str(error.__repr__()))
            LogDebug("Error: " + str(error.__module__))
            LogDebug("Error: " + str(error.__class__))
            LogDebug("Error: " + str(error.__doc__))
            LogDebug("Error: " + str(error.__name__))
            LogDebug("Error: " + str(error.__qualname__))
            LogDebug("Error: " + str(error.__annotations__))
            LogDebug("Error: " + str(error.__defaults__))
            LogDebug("Error: " + str(error.__code__))
            LogDebug("Error: " + str(error.__globals__))
            LogDebug("Error: " + str(error.__closure__))
            LogDebug("Error: " + str(error.__kwdefaults__))
        except Exception as e:
            raise "Error in error handler" + str(e)
    else:
        LogDebug("Error: None")
        
