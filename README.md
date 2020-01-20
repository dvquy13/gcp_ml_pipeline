# Machine Learning Pipeline on Google Cloud Platform - Cloud BigQuery, Storage, Dataproc, Firestore

In some scenarios, Machine Learning application means precomputing everything and store predictions in a database. This repo can be used as a template for that purpose.
```
├── configs
│   ├── logging.yaml
│   └── runtime.yaml
├── data
│   ├── interim
│   │   ├── X_pred.parquet
│   │   ├── X_train.parquet
│   │   ├── y_pred.parquet
│   │   └── y_train.parquet
│   └── output
│       ├── pipeline
│       │   └── pipeline.joblib
│       ├── prediction
│       │   └── predictions.parquet
│       └── transformer
│           └── normalizer.joblib
├── dist
│   ├── jobs.zip
│   ├── libs.zip
│   ├── logging.yaml
│   ├── main.py
│   └── runtime.yaml
├── iris_pred
│   ├── jobs
│   │   ├── data_import
│   │   │   ├── data_importer.py
│   │   │   └── entry_point.py
│   │   ├── feature_engineer
│   │   │   ├── entry_point.py
│   │   │   └── normalize.py
│   │   ├── model
│   │   │   ├── entry_point.py
│   │   │   └── train.py
│   │   └── predict
│   │       ├── batch_predict.py
│   │       ├── entry_point.py
│   │       └── write_db.py
│   ├── libs
│   ├── main.py
│   └── shared
│       ├── io_handler.py
│       └── utils.py
├── Makefile
├── README.md
├── requirements.txt
└── scripts
    ├── 00_import_data_to_bigquery.sh
    ├── 01_erase_resources.sh
    ├── 02_disable_resources.sh
    └── 03_delete_project.sh
```

Explanations on the building blocks can be found in this blog post: https://medium.com/@quy.dinh3195/what-i-learned-about-deploying-machine-learning-application-c7bfd654f999

Steps to get yourself start:
    1. Grant execute permission to scripts folder: `chmod -R +x ./scripts`
    2. Change `<PLACEHOLDERS>` in `.project_env` file to the appropriate values. The ones starts with `NAME-` can be defined up to your choice.
    3. Run `./scripts/00_download_iris_data.sh`
    4. Follow steps described in the `Makefile`