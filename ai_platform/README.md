# Setup your Environment

## Setup your GCP Environment

Steps to setup the GCP account and environment.

1- Have a GCP account and create/select a GCP project on [GCP Console](https://console.cloud.google.com).

2- Enable the billing for your GCP project. Click [here](https://cloud.google.com/billing/docs/how-to/modify-project) for more information.

3- Download and install [Google Cloud SDK](https://cloud.google.com/sdk/docs/).

4- Configure the SDK by running the following command from your terminal:

```shell
gcloud init
```
   
and follow the instructions.
   
5- Enable the API for the following services:

  * [Compute Engine](https://console.cloud.google.com/compute)
  * [Storage](https://console.cloud.google.com/storage)
  * [AI Platform](https://console.cloud.google.com/mlengine)

From your terminal, run:

```bash
gcloud services enable compute.googleapis.com
gcloud services enable storage-component.googleapis.com
gcloud services enable ml.googleapis.com
```

6- Set and export the required environment variables. The samples in this repository rely on a 
number of environment variables to run properly, namely:
  * `RUNTIME_VERSION`: Which AI Platform runtime version to choose
  * `PYTHON_VERSION`: Which Python version to use for training
  * `REGION`: Which region should be used for training
  * `PROJECT_ID`: Your GCP project ID
  * `BUCKET_NAME`: The GCS bucket name for exporting models
  * `GOOGLE_APPLICATION_CREDENTIALS`: Full path to your service account key
  
Use [variables.sh](./setup/variables.sh)
which sets up the first three variables with reasonable values, and enables you to
set the other three variables based on your configuration.

In your terminal, and from the root directory of the repository, run:

```bash
source ./setup/variables.sh
```

*Note:* The service account key is a json file. If you do not yet have a service account key downloaded,
please follow the instructions in the next step to create and download one.


7- Create and download a service account key.
A [service account](https://cloud.google.com/iam/docs/service-accounts) is a special Google account that belongs to your application or a virtual machine (VM), instead of to an individual end user.

In order to create a service account key, you may follow the instructions [here](https://cloud.google.com/iam/docs/creating-managing-service-account-keys#iam-service-account-keys-create-gcloud).
Alternatively, you may run this in your terminal, after setting the values for the 3 environment variables:


```bash
# A name for the service account you are about to create:
export SERVICE_ACCOUNT_NAME=your-service-account-name

# Create service account:
gcloud iam service-accounts create ${SERVICE_ACCOUNT_NAME} --display-name="Service Account for ai-platform-samples repo"

# Grant the required roles:
gcloud projects add-iam-policy-binding ${PROJECT_ID} --member serviceAccount:${SERVICE_ACCOUNT_NAME}@${PROJECT_ID}.iam.gserviceaccount.com --role roles/ml.developer
gcloud projects add-iam-policy-binding ${PROJECT_ID} --member serviceAccount:${SERVICE_ACCOUNT_NAME}@${PROJECT_ID}.iam.gserviceaccount.com --role roles/storage.objectAdmin

# Download the service account key and store it in a file specified by GOOGLE_APPLICATION_CREDENTIALS:
gcloud iam service-accounts keys create ${GOOGLE_APPLICATION_CREDENTIALS} --iam-account ${SERVICE_ACCOUNT_NAME}@${PROJECT_ID}.iam.gserviceaccount.com
```


## Install Dependencies

Each application folder has a `setup.py` file, containing all the dependencies.
To run each sample, install the python dependencies using the following command:
 
 ```bash
python setup.py install
 ```
 
