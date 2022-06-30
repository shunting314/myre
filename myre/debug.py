import os

ENABLE_DEBUG = os.environ.get("DEBUG", None) is not None

def debug(msg):
    if ENABLE_DEBUG:    
        print(msg)
