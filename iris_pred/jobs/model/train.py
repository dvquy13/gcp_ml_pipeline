import logging
logger = logging.getLogger(__name__)
import subprocess

from shared.io_handler import IOHandler
from jobs.feature_engineer.normalize import FeatureNormalizer
from sklearn.externals import joblib
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import make_pipeline


class Trainer:
    def __init__(self, params, load: bool):
        self.params = params

        self.io_handler = IOHandler(params)
        self.interim_output_path, self.final_output_path = \
            self._get_fpath()

        self.normalizer = None
        self.learner = None
        self.pipeline = None

    def _get_fpath(self):
        interim_output_path = \
            f'../{self.params.io.pipeline}/pipeline.joblib'
        final_output_path = \
            f'{self.io_handler.fpath_dict.pipeline}/pipeline.joblib'
        return interim_output_path, final_output_path

    def _load_train_data(self):
        X_train = self.io_handler.load('X_train')
        y_train = self.io_handler.load('y_train')['species']
        return X_train, y_train

    def _load_transformer(self):
        normalizer_wrapper = FeatureNormalizer(self.params, load=True)
        self.normalizer = normalizer_wrapper.normalizer

    def _initiate_learner(self):
        self.learner = LogisticRegression()

    def _make_pipeline(self):
        self.pipeline = make_pipeline(
            self.normalizer,
            self.learner)

    def _fit(self, X_train, y_train):
        self.pipeline.fit(X_train, y_train)

    def _persist_pipeline(self):
        # Temporarily save model to disk
        joblib.dump(self.pipeline, self.interim_output_path)

        # Copy model to GCS
        if self.params.env_name != 'local':
            logger.info(f"Persisting {self.final_output_path}...")
            subprocess.check_output([
                'gsutil', '-m', 'cp', '-r',
                self.interim_output_path,
                self.final_output_path])

    def run(self):
        X_train, y_train = self._load_train_data()
        self._load_transformer()
        self._initiate_learner()
        self._make_pipeline()
        self._fit(X_train, y_train)
        self._persist_pipeline()
