#!/usr/bin/env python
# Migrate users from one Docker UCP to another
# Kyle Squizzato <kyle.squizzato@docker.com>

import argparse
import sys
import os
import requests
import logging
import validators
from time import sleep
from requests.packages.urllib3.exceptions import InsecureRequestWarning


requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

"""
Perform retrying for error handling.
Specify componentName which is breaking.
retrySecs is the number of seconds each retry will increment by.
doSomething handles a function to call at the > 3 retry mark.
maxAttempts is an int representing the max number of tries before exiting
(defaults to 1).
"""
def retry_this(componentName, retrySecs, retries, maxAttempts=1,
               doSomething=None):
    retry_time = int(retries)*retrySecs
    if retries > 3:
        # if doSomething isn't given then assume we don't need to run anything
        # at retries > 3
        if not doSomething == None:
            doSomething
    if retries > maxAttempts:
        # Notify user we failed
        logging.error('Unable to access {0} after {1} connection attempts, exiting'.format(componentName, maxAttempts))
        sys.exit(1)
    else:
        logging.info('Unable to access {0}, attempting to reconnect to {0} in {1} seconds'.format(componentName, retry_time))
        sleep(retry_time)
        logging.info("Attempting to reconnect to {0} -- retry {1} of {2}".format(componentName, retries, maxAttempts))

"""
Get and return an authtoken from a given UCP URL
"""
def get_token(username, password, url, retries=0):
    data='{{"username":"{0}","password":"{1}"}}'.format(username, password)
    logging.info('Authenticating with UCP {}...'.format(url))
    try:
        r = requests.post(
            url+'/auth/login',
            data=data,
            verify=False)
    except requests.exceptions.RequestException as e:
        logging.error('Failed to authenticate with UCP {0}: {1}'.format(url, e))
        retries+=1
        retry_this('UCP', 10, retries, 3, get_token(username, password, url))
    logging.debug('Got response: {}'.format(r.text))
    if "unauthorized" in r.text:
        logging.error('Unable to authenticate with UCP {}, are the admin credentials correct?'.format(url))
        sys.exit(1)
    a = json.loads(r.text)
    try:
        token = str(a["auth_token"])
    except KeyError:
        logging.error('No authtoken was received from UCP {0}'.format(url))
        sys.exit(1)
    return token

def main():
    # argument parsing
    parser = argparse.ArgumentParser(description='Get an authtoken from a \
    given UCP url.')
    parser.add_argument("-u",
                        "--ucp-url",
                        dest="ucpUrl",
                        required=True,
                        help="UCP FQDN")
    parser.add_argument("-U",
                        "--user",
                        dest="ucpUser",
                        required=True,
                        help="UCP username")
    parser.add_argument("-P",
                        "--password",
                        dest="userPassword",
                        required=True,
                        help="UCP password")
    parser.add_argument("-D",
                        "--debug",
                        dest="debug",
                        help="Enable debug mode")

    args = parser.parse_args()

    # basic logging
    if not args.debug:
        logger = logging.getLogger(name=None)
        logging.basicConfig(format='%(levelname)s: %(message)s',
                            level=logging.INFO)
    else:
        logger = logging.getLogger(name=None)
        logging.basicConfig(format='%(levelname)s: %(message)s',
                            level=logging.DEBUG)

    """
    Flag Verification
    """
    if not validators.url(args.ucpUrl):
        logging.error('Please enter a valid UCP URL (ex. https://example.com)')
        sys.exit(1)

    """
    Get Token
    """
    # Get an auth token against the --from UCP
    ucpAuthtoken = get_token(args.ucpUser, args.userPassword, args.ucpUrl)
    print ucpAuthtoken

"""
Main
"""
if __name__ == '__main__':
    sys.exit(main())
