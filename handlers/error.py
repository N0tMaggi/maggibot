import logging
import sys
import traceback
import handlers.debug as DH


def error_handler(error):
    if error is not None:
        try:
            DH.LogError(f"Error: {str(error)}")
            DH.LogError(f"Error Type: {str(error.__class__.__name__)}")
            DH.LogError(f"Error Traceback: {str(error.__traceback__)}")
            DH.LogError(f"Error Message: {str(error)}")
            DH.LogError(f"Stack Trace: {''.join(traceback.format_exception(None, error, error.__traceback__))}")
        except Exception as e:
            raise Exception(f"Error in error handler: {str(e)}")
    else:
        DH.LogError("Error: None")
