import logging
import sys
import traceback
from handlers.debug import LogDebug


def error_handler(error):
    if error is not None:
        try:
            LogDebug(f"Error: {str(error)}")
            LogDebug(f"Error Type: {str(error.__class__.__name__)}")
            LogDebug(f"Error Traceback: {str(error.__traceback__)}")
            LogDebug(f"Error Message: {str(error)}")
            LogDebug(f"Stack Trace: {''.join(traceback.format_exception(None, error, error.__traceback__))}")
        except Exception as e:
            raise Exception(f"Error in error handler: {str(e)}")
    else:
        LogDebug("Error: None")
