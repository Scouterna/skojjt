cd /d %~dp0
cd ..
:: gcloud components update
:: gcloud auth login
:: gcloud datastore indexes create index.yaml
:: gcloud auth application-default login
gcloud app deploy --project=skojjt-staging
gcloud app deploy queue.yaml --project=skojjt-staging
gcloud app deploy index.yaml --project=skojjt-staging
