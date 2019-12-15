import logging
logger = logging.getLogger(__name__)
import pandas as pd

import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore

from shared.io_handler import IOHandler


class DBWriter:
    def __init__(self, params):
        self.params = params

        self.io_handler = IOHandler(params)
        self.init_writer(params.db_engine)

    def init_writer(self, db_engine: str):
        if db_engine == 'Firestore':
            self.writer = FirestoreWriter(project_id=self.params.GCP_PROJECT)

    def _load_predictions(self):
        predictions = self.io_handler.load('predictions')
        return predictions

    def _prepare_db_format(self, data: pd.DataFrame):
        fmt_data = \
            data \
                .reset_index() \
                .assign(
                    id=lambda df:
                        df['id'].astype(str)) \
                .to_dict(orient='record')

        return fmt_data

    def run(self):
        predictions = self._load_predictions()
        predictions_doc = self._prepare_db_format(predictions)
        self.writer.write(
            collection='iris', data=predictions_doc, key='id')


class FirestoreWriter:
    def __repr__(self):
        return "Firestore"

    def __init__(self, project_id, service_account_fpath=None):
        if (not len(firebase_admin._apps)):
            if not service_account_fpath:
                # Use the application default credentials
                cred = credentials.ApplicationDefault()
            else:
                cred = credentials.Certificate(service_account_fpath)
            firebase_admin.initialize_app(cred, {'projectId': project_id})

        self.client = firestore.client()

    def write(self, collection, data, key, num_write=500, verbose=False):
        doc_ref = self.client.collection(collection)

        max_write = num_write
        if len(data) % max_write == 0:
            iteration = len(data) // max_write 
        else:
            iteration = (len(data) // max_write) + 1

        # Start batch
        batch = self.client.batch()
        for idx in range(iteration):
            data_ext = data[ idx*max_write : (idx+1)*max_write ]
            for d in data_ext:
                record_ref = doc_ref.document(d[key])
                batch.set(record_ref, d)

            batch.commit()
            if verbose and (idx % 500 == 0):
                logger.info(
                    f"Done uploading {idx + 1} batches to Firestore,"
                    f" {iteration - (idx + 1)} batches left.")
            batch = self.client.batch()

        logger.info(
            f"Done writing {len(data):,.0f} records to Firestore collection"
            f" {collection}")
        return None

    def delete_collection(self, collection, batch_size, i=0):
        coll_ref = self.client.collection(collection)
        docs = coll_ref.limit(batch_size).get()
        deleted = 0

        for doc in docs:
            if i < 50:
                logger.info(f'Deleting doc {doc.id} => {doc.to_dict()}')
            doc.reference.delete()
            deleted = deleted + 1
            i += 1

        if deleted >= batch_size:
            logger.info(f">> Deleted {i} documents.")
            return self.delete_collection(collection, batch_size, i)
