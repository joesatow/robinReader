import os

# Set these variables to your corresponding environmental variables.  This is the source location for API keys throughout the program.

sc_cookie = os.environ['sc_cookie']

# Function to grab keys 
def getKey(key):
    if key == "sc_cookie":
        return sc_cookie