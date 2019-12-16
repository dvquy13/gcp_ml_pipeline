__author__ = 'dvquy.13@gmail.com'

import argparse
import importlib
import time
import os
import sys
from attrdict import AttrDict

from shared import utils

if os.path.exists('libs.zip'):
    sys.path.insert(0, 'libs.zip')
else:
    sys.path.insert(0, './libs')

if os.path.exists('jobs.zip'):
    sys.path.insert(0, 'jobs.zip')
else:
    sys.path.insert(0, './jobs')


class ArgParser:
    @staticmethod
    def parse_args():
        parser = argparse.ArgumentParser(description='Run a job')
        parser.add_argument('--job', type=str, required=True, dest='job_name', help="The name of the job module you want to run. (ex: poc will run job on jobs.poc package)")
        parser.add_argument('--job-args', nargs='*', help="Extra arguments to send to the job (example: --job-args template=manual-email1 foo=bar")
        args = parser.parse_args()
        return args

    @staticmethod
    def parse_job_args(args):
        job_args = dict()
        if args.job_args:
            job_args_tuples = [arg_str.split('=') for arg_str in args.job_args]
            logger.info('job_args_tuples: {}'.format(job_args_tuples))
            job_args = {}
            for a in job_args_tuples:
                job_args[a[0]] = utils.convert_to_bool_if_is(a[1])
        return job_args

    @staticmethod
    def prepare_executor_env_vars(args):
        environment = {
            'JOB_ARGS': ' '.join(args.job_args) if args.job_args else ''
        }
        return environment


if __name__ == '__main__':
    logger = utils.get_logger(__name__, 'logging.yaml')

    args = ArgParser.parse_args()
    job_args = ArgParser.parse_job_args(args)
    environment = ArgParser.prepare_executor_env_vars(args)

    logger.info("Called with arguments: {}".format(args))
    os.environ.update(environment)

    logger.info(f'Running job {args.job_name}... Environment is {environment}')

    logger.info(f"os.curdir: {os.path.abspath(os.curdir)}")
    logger.info(f"os.listdir: {os.listdir()}")

    logger.info(f"Initializing job_name: jobs.{args.job_name}...")
    job_module = importlib.import_module('jobs.{}'.format(args.job_name))

    # Parse config file
    env = job_args.pop('env')
    utils.load_env('.project_env')
    yaml_params_fpath = job_args.pop('yaml_params_fpath')
    params = AttrDict(utils.read_yaml(yaml_params_fpath).env.get(env))

    start = time.time()
    job_module.analyze(params, **job_args)
    end = time.time()

    logger.info(f"Execution of job {args.job_name} took {end-start:,.2f}s.")
