#!make
include ./configs/.project_env
export

# Main flow
step-0:
	make create-dataproc-cluster
step-1:
	make submit-job ENV=dev MODULE=data_import TASK=query_train_pred
step-2:
	make submit-job ENV=dev MODULE=feature_engineer TASK=normalize
step-3:
	make submit-job ENV=dev MODULE=model TASK=fit
step-4:
	make submit-job ENV=dev MODULE=predict TASK=batch_predict
step-5:
	make submit-job ENV=dev MODULE=predict TASK=store_predictions
step-99:
	make delete-dataproc-cluster

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
	cp ./iris_pred/main.py ./dist
	cp -r ./configs/*.yaml ./dist
	-cp -r ./configs/*.py ./dist
	cp -r ./configs/.project_env ./dist
	cd ./iris_pred && zip -x \*libs\* main.py -r ../dist/jobs.zip .
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
			gs://dataproc-initialization-actions/python/conda-install.sh,gs://dataproc-initialization-actions/python/pip-install.sh \
		--scopes=storage-full,datastore

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
ifeq ($(ENV),local)
	cd dist && \
	spark-submit \
		--py-files jobs.zip,libs.zip \
		--conf 'spark.executorEnv.PYTHONHASHSEED=321' \
		--files runtime.yaml,logging.yaml,.project_env \
		main.py \
		--job $(MODULE).entry_point \
		--job-args \
			env=$(ENV) \
			yaml_params_fpath=runtime.yaml \
			task=$(TASK)
else
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
endif


# Some extra commands
list-gcp-account-role:
ifeq ($(GCP_ACCOUNT),)
	@echo Missing param GCP_ACCOUNT!!!
	@exit 1
endif
	gcloud projects get-iam-policy $(GCP_PROJECT) \
		--flatten="bindings[].members" \
		--format='table(bindings.role)' \
		--filter="bindings.members:$(GCP_ACCOUNT)"

# Refer to this doc: https://cloud.google.com/sdk/gcloud/reference/projects/add-iam-policy-binding
# --member can take one of the following identity: {serviceAccount, user, group}
remove-gcp-account-role:
ifeq ($(GCP_ACCOUNT),)
	@echo Missing param GCP_ACCOUNT!!!
	@exit 1
endif
ifeq ($(ROLE),)
	@echo Missing param ROLE!!! Example role: roles/datastore.user
	@exit 1
endif
	gcloud projects remove-iam-policy-binding \
		$(GCP_PROJECT) \
		--member=serviceAccount:$(GCP_ACCOUNT) \
		--role=$(ROLE)

add-gcp-account-role:
ifeq ($(GCP_ACCOUNT),)
	@echo Missing param GCP_ACCOUNT!!!
	@exit 1
endif
ifeq ($(ROLE),)
	@echo Missing param ROLE!!! Example role: roles/datastore.user
	@exit 1
endif
	gcloud projects add-iam-policy-binding \
		$(GCP_PROJECT) \
		--member=serviceAccount:$(GCP_ACCOUNT) \
		--role=$(ROLE)
