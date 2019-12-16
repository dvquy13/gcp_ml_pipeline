import logging
logger = logging.getLogger(__name__)
import subprocess
import pandas as pd

from shared.io_handler import IOHandler
from sklearn.externals import joblib


class BatchPredictor:
    def __init__(self, params):
        self.params = params

        self.io_handler = IOHandler(params)
        self.interim_output_path, self.final_output_path = \
            self._get_fpath()

        self.pipeline = self._load_pipeline()

    def _get_fpath(self):
        interim_output_path = \
            f'../{self.params.io.pipeline}/pipeline.joblib'
        final_output_path = \
            f'{self.io_handler.fpath_dict.pipeline}/pipeline.joblib'
        return interim_output_path, final_output_path

    def _load_pred_data(self):
        X_pred = self.io_handler.load('X_pred')
        return X_pred

    def _load_pipeline(self):
        if self.params.env_name != 'local':
            logger.info(f"Downloading {self.final_output_path}...")
            subprocess.check_output([
                'gsutil', '-m', 'cp', '-r',
                self.final_output_path,
                self.interim_output_path])

        pipeline = joblib.load(self.interim_output_path)
        return pipeline

    def _batch_predict(self, X_pred):
        predictions = self.pipeline.predict_proba(X_pred)
        predictions_df = pd.DataFrame(
            data=predictions,
            index=X_pred.index,
            columns=[
                f'score_{x}' for x in
                self.pipeline.steps[-1][1].classes_
                ])
        return predictions_df

    def _store_predictions(self, predictions_df):
        self.io_handler.save(predictions_df, 'predictions')

    def run(self):
        X_pred = self._load_pred_data()
        self._load_pipeline()
        predictions_df = self._batch_predict(X_pred)
        self._store_predictions(predictions_df)