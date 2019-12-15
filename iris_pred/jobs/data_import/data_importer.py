import logging
logger = logging.getLogger(__name__)

from google.cloud import bigquery
import pandas as pd
from shared.io_handler import IOHandler


class DataImporter:
    def __init__(self, params):
        self.params = params

        self.io_handler = IOHandler(params)

    def _initiate_db_client(self):
        self.bq_client = bigquery.Client()

    def _generate_querystr(self):
        querystr = (f"""
            select
            *,
            case
                when rand() < 0.7 then 'train'
                else 'pred'
            end as train_pred
            from `{self.params.GCP_PROJECT}"""
            f".{self.params.BQ_DATASET}.{self.params.BQ_ORG_TABLE}`")

        return querystr

    def _query(self, querystr):
        raw_dat = self.bq_client.query(querystr).to_dataframe()
        return raw_dat

    def _split_train_pred(self, raw_dat: pd.DataFrame):
        train_df = raw_dat.loc[lambda df: df['train_pred'].eq('train')]
        pred_df = raw_dat.loc[lambda df: df['train_pred'].eq('pred')]
        return train_df, pred_df

    def _split_X_y(self, df: pd.DataFrame):
        X = df.drop(columns=['train_pred', 'species'])
        y = df[['species']]
        return X, y

    def run(self):
        self._initiate_db_client()
        querystr = self._generate_querystr()
        raw_dat = self._query(querystr)
        logger.info(raw_dat.head())
        train_df, pred_df = self._split_train_pred(raw_dat)
        X_train, y_train = self._split_X_y(train_df)
        X_pred, y_pred = self._split_X_y(pred_df)
        self.io_handler.save(X_train, 'X_train')
        self.io_handler.save(y_train, 'y_train')
        self.io_handler.save(X_pred, 'X_pred')
        self.io_handler.save(y_pred, 'y_pred')
