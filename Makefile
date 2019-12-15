#!make
include ./configs/.project_env
export

clean: clean-build clean-pyc
clean-build:
	rm -fr dist/
clean-pyc:
	find . -name '*.pyc' -exec rm -f {} +
	find . -name '*.pyo' -exec rm -f {} +
	find . -name '*~' -exec rm -f {} +
	find . -name '__pycache__' -exec rm -fr {} +

# 3rd party libraries
iris_pred/libs: requirements.txt
	rm -fr ./iris_pred/libs/
	pip install -r requirements.txt -t ./iris_pred/libs

clean-output-cloud:
	gsutil -m rm -r gs://$(GCS_BUCKET)/data/interim
	gsutil -m rm -r gs://$(GCS_BUCKET)/data/output

build: clean iris_pred/libs
	mkdir ./dist
	cp ./main.py ./dist
	cp -r ./configs/*.yaml ./dist
	-cp -r ./configs/*.py ./dist
	cp -r ./configs/.project_env ./dist
	cd ./iris_pred && zip -x \*libs\* -r ../dist/jobs.zip .
	cd ./iris_pred/libs && zip -r ../../dist/libs.zip .

create-dataproc-cluster:
	gcloud beta dataproc clusters create \
		$(CLUSTER_NAME) \
		--project $(GCP_PROJECT) \
		--region $(DATA_LOCATION) \
		--zone $(DATA_LOCATION)-b \
		--image-version 1.4 \
		--single-node \
		--master-machine-type n1-standard-1 --num-masters 1 \
		--max-idle 600s \
		--optional-components=ANACONDA \
		--metadata 'CONDA_PACKAGES=scikit-learn=0.20.0' \
		--metadata "PIP_PACKAGES=google-cloud-firestore firebase-admin python-dotenv==0.10.3 attrdict gcsfs" \
		--initialization-actions \
			gs://dataproc-initialization-actions/python/conda-install.sh,gs://dataproc-initialization-actions/python/pip-install.sh
			

delete-dataproc-cluster:
	gcloud dataproc clusters delete \
		--project $(GCP_PROJECT) \
		--region=$(DATA_LOCATION) \
		--quiet \
		$(CLUSTER_NAME)

submit-job:
ifeq ($(ENV),)
	@echo Missing param ENV!!!
	@exit 1
endif
ifeq ($(MODULE),)
	@echo Missing param TASK!!!
	@exit 1
endif
ifeq ($(TASK),)
	@echo Missing param TASK!!!
	@exit 1
endif
	cd dist && \
	gcloud dataproc jobs submit pyspark \
		--id $(shell date +%s)-iris-pred-$(TASK) \
		--project $(GCP_PROJECT) \
		--cluster $(CLUSTER_NAME) \
		--region $(DATA_LOCATION) \
		--properties 'spark.executorEnv.PYTHONHASHSEED=321' \
		--py-files jobs.zip,libs.zip \
		--files runtime.yaml,logging.yaml,.project_env \
		main.py \
		-- \
		--job $(MODULE).entry_point \
		--job-args \
			env=$(ENV) \
			yaml_params_fpath=runtime.yaml \
			task=$(TASK)
