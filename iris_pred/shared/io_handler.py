import os
import logging
logger = logging.getLogger(__name__)
from attrdict import AttrDict

import pandas as pd

class _ParquetIOHandler:
    def load_from_file(self, filepath: str):
        logger.info(f'Loading {filepath}...')
        df = pd.read_parquet(filepath)
        return df

    def save_to_file(self, df: pd.DataFrame, filepath: str):
        logger.info(f'Saving to {filepath}...')
        df.to_parquet(filepath)

class IOHandler:
    verbose = 1

    def __init__(self, params):
        self.params = params
        self._setup(params.env_name)

        self.filetype_handler = \
            self._initiate_filetype_handler(params.filetype_handler)
        self.fpath_dict = self._init_global_fpath()

    def _setup(self, env_name: str):
        os.makedirs(self.params.io.transformer, exist_ok=True)
        os.makedirs(self.params.io.pipeline, exist_ok=True)
        if env_name == 'local':
            self.base_dir = './'
        else:
            self.base_dir = f"gs://{self.params.GCS_BUCKET}"

    def _assemble_input_fpath(self, main_fpath: str):
        return (
            f"{self.base_dir}"
            f"/{main_fpath}.{self.params.filetype_handler}")

    def _init_global_fpath(self):
        input_fpath_dict = dict(
            X_train=f"{self.params.io.input}/X_train",
            y_train=f"{self.params.io.input}/y_train",
            X_pred=f"{self.params.io.input}/X_pred",
            y_pred=f"{self.params.io.input}/y_pred",
            predictions=f"{self.params.io.output}/predictions"
        )
        input_fpath_dict = {
            k: self._assemble_input_fpath(v)
            for k, v in input_fpath_dict.items()
        }
        fpath_dict = dict(
            **input_fpath_dict,
            t_normalizer=
                f"{self.base_dir}/{self.params.io.transformer}",
            pipeline=
                f"{self.base_dir}/{self.params.io.pipeline}"
        )
        return AttrDict(fpath_dict)

    def _initiate_filetype_handler(self, handler: str):
        if handler == 'parquet':
            return _ParquetIOHandler()

    def save(self, df: pd.DataFrame, name: str):
        return self.filetype_handler.save_to_file(
            df, self.fpath_dict.get(name))

    def load(self, name: str):
        return self.filetype_handler.load_from_file(self.fpath_dict.get(name))
