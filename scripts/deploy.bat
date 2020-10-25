cd /d %~dp0
cd ..
:: gcloud components update
:: gcloud auth login
:: gcloud datastore indexes create index.yaml
:: gcloud auth application-default login
gcloud app deploy --project=skojjt
gcloud app deploy queue.yaml
gcloud app deploy index.yaml
