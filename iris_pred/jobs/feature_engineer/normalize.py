import logging
logger = logging.getLogger(__name__)
import subprocess

from sklearn.preprocessing import StandardScaler
from shared.io_handler import IOHandler

from sklearn.externals import joblib


class FeatureNormalizer:
    def __init__(self, params, load: bool):
        self.params = params

        self.io_handler = IOHandler(params)
        self.interim_output_path, self.final_output_path = \
            self._get_fpath()

        if not load:
            initiate_fn = self._initiate_normalizer
        else:
            initiate_fn = self._load_normalizer
        self.normalizer = initiate_fn()

    def _get_fpath(self):
        interim_output_path = \
            f'../{self.params.io.transformer}/normalizer.joblib'
        final_output_path = \
            f'{self.io_handler.fpath_dict.t_normalizer}/normalizer.joblib'
        return interim_output_path, final_output_path

    def _initiate_normalizer(self):
        name = self.params.feature_engineer.normalizer
        if name == 'standard_scaler':
            normalizer = StandardScaler()
        return normalizer

    def _load_normalizer(self):
        if self.params.env_name != 'local':
            logger.info(f"Downloading {self.final_output_path}...")
            subprocess.check_output([
                'gsutil', '-m', 'cp', '-r',
                self.final_output_path,
                self.interim_output_path])

        normalizer = joblib.load(self.interim_output_path)
        return normalizer

    def _persist_normalizer(self):
        # Temporarily save model to disk
        joblib.dump(self.normalizer, self.interim_output_path)

        # Copy model to GCS
        if self.params.env_name != 'local':
            logger.info(f"Persisting {self.final_output_path}...")
            subprocess.check_output([
                'gsutil', '-m', 'cp', '-r',
                self.interim_output_path,
                self.final_output_path])

    def run(self):
        X_train = self.io_handler.load('X_train')
        self.normalizer.fit(X_train)
        self._persist_normalizer()
