import os
import json
import logging
from docopt import docopt
from pipeline.logger import setup_logging

from pipeline.usage import USAGE
from pipeline.version import VERSION





def main():
    if os.getenv("DEBUG", False):
        print("-"*100)

    setup_logging()
    log = logging.getLogger()


    MY_DIR = os.path.dirname(os.path.realpath(__file__))
    log.debug(f"MY_DIR: {MY_DIR}")


    DATA_DIR = os.path.join( os.path.dirname(MY_DIR), 'data/raw')
    log.debug(f"DATA_DIR: {DATA_DIR}")
    os.environ.setdefault('DATA_DIR', DATA_DIR)

    PROCESSED_DATA_DIR = os.path.join( os.path.dirname(MY_DIR), 'data/processed')
    log.debug(f"PROCESSED_DATA_DIR: {PROCESSED_DATA_DIR}")
    os.environ.setdefault('PROCESSED_DATA_DIR', PROCESSED_DATA_DIR)

    RESULTS_DIR = os.path.join( os.path.dirname(MY_DIR), 'data/results')
    log.debug(f"RESULTS_DIR: {RESULTS_DIR}")
    os.environ.setdefault('RESULTS_DIR', RESULTS_DIR)

    # args = docopt(__doc__, version='Analysis Pipeline Module 1.0')
    args = docopt(USAGE, version=f"analysis_pipeline {VERSION}")

    passed_args = {k: v for k, v in args.items() if v not in (False, [], None)}
    log.debug(f"passed args: {passed_args}")


    #####################################
    ### COMMANDS ########################
    #####################################
    if args.get("version", False):
        print(f"analysis_pipeline {VERSION}")

    elif args['waittimes']:
        # filename = args['<filename>']
        from pipeline.wait_times.wait_times import process_wait_times
        process_wait_times(args)

    elif args['levelstatus']:
        # filename = args['<filename>']
        from pipeline.levelstatus.levelstatus import process_levelstatus
        process_levelstatus(args)
