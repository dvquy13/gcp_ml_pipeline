import sys
import os
import subprocess
import re
from dotenv import load_dotenv
from pathlib import Path
import logging
import logging.config
logger = logging.getLogger(__name__)
import numpy as np
import yaml
from attrdict import AttrDict
import traceback
import datetime as pydt
import time
import pandas as pd

from functools import wraps

def get_logger(logger_name, yaml_config_fpath='./configs/logging.yaml'):
    with open(yaml_config_fpath, 'r') as f:
        config = yaml.safe_load(f.read())
        config['disable_existing_loggers'] = False
        logging.config.dictConfig(config)
    logger = logging.getLogger(logger_name)
    return logger

def convert_to_bool_if_is(s):
    if s in ('False', 'false', '0', 0):
        b = False
    elif s in ('True', 'true', '1', 1):
        b = True
    else:
        return s
    return b

def load_env(env_fpath: str):
    env_path = Path(env_fpath)
    load_dotenv(dotenv_path=env_path)

def replace_yaml_placeholders(yaml_str_file: str):
    yaml_rep = yaml_str_file
    ph_iter = re.finditer(r'<(\w+)>', yaml_str_file)
    for ph in ph_iter:
        rep = os.environ.get(ph.group(1))
        print(f"Replacing {ph.group(0)} with {rep}...")
        yaml_rep = yaml_rep.replace(ph.group(0), rep)
    return yaml_rep

def read_yaml(filepath):
    with open(filepath) as f:
        yaml_str_file = f.read()
        yaml_rep = replace_yaml_placeholders(yaml_str_file)
        params = yaml.load(yaml_rep, Loader=yaml.FullLoader)
    return AttrDict(params)

def align_number_print_format(small, big):
    num_chars_diff = f"{big:,.0f}".__len__() - f"{small:,.0f}".__len__()
    returned_format = f"{' '*(num_chars_diff)}{small:,.0f}"
    if small >= 0 or num_chars_diff >= 0:
        # This is to ensure negative and positive number aligned with each other,
        # because negative number has an minus sign on its left
        returned_format = f' {returned_format}'
    return returned_format

def timeit(get_time=False, printer=print):
    """
    Parameters
    ---
    printer: function to print, [print, logging.info]
    """
    def _timeit(method):
        @wraps(method)
        def timed(*args, **kw):
            ts = time.time()
            result = method(*args, **kw)
            te = time.time()
            walltime = te - ts
            printer(f'>> fn {method.__qualname__} run duration: {te - ts:.2f}s')
            if get_time:
                return result, walltime
            else:
                return result
        return timed
    return _timeit

def print_num_diff_rows(
        df_arg_index=0,
        change_kind='rows',
        printer=print):
    """
    df_type: {'spark', 'pandas'}
    """
    def _calc_diff(method):
        @wraps(method)
        def _calc(*args, **kw):
            old_df = args[df_arg_index]
            result_df = method(*args, **kw)
            # Get num_rows for old and new df
            old_df_num_rows = old_df.shape[0]
            new_df_num_rows = result_df.shape[0]
            num_changed = new_df_num_rows - old_df_num_rows
            # Format
            bigger = max(old_df_num_rows, new_df_num_rows)
            old_df_num_rows_fmt = align_number_print_format(old_df_num_rows, bigger)
            new_df_num_rows_fmt = align_number_print_format(new_df_num_rows, bigger)
            delta_fmt = align_number_print_format(num_changed, bigger)
            printer(f">> Function {method.__qualname__} caused change in number of {change_kind}:\n\tOld:\t{old_df_num_rows_fmt}\n\tDelta:\t{delta_fmt} ({num_changed / old_df_num_rows:.2%})\n\tNew:\t{new_df_num_rows_fmt}")
            return result_df
        return _calc
    return _calc_diff

def print_num_diff_unique_values(
        df_arg_index=0,
        cols=[],
        printer=print):
    def _calc_diff(method):
        @wraps(method)
        def _calc(*args, **kw):
            old_df = args[df_arg_index]
            result_df = method(*args, **kw)
            for col in cols:
                col_metric_name = "nunique_{}".format(col)
                old_num_values = old_df.select(F.approx_count_distinct(col).alias(col_metric_name)).collect()[0][col_metric_name]
                new_num_values = result_df.select(F.approx_count_distinct(col).alias(col_metric_name)).collect()[0][col_metric_name]
                num_unique_values_changed = new_num_values - old_num_values
                # Format
                bigger = max(old_num_values, new_num_values)
                old_num_values_fmt = align_number_print_format(old_num_values, bigger)
                new_num_values_fmt = align_number_print_format(new_num_values, bigger)
                delta_fmt = align_number_print_format(num_unique_values_changed, bigger)
                logger.info(f">> Function {method.__qualname__} caused change in number of unique values in column {col}:\n\tOld:\t{old_num_values_fmt}\n\tDelta:\t{delta_fmt} ({num_unique_values_changed / old_num_values:.2%})\n\tNew:\t{new_num_values_fmt}")
            return result_df
        return _calc
    return _calc_diff
