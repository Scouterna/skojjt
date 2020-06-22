az acr repository show-tags --name scouterna --repository skojjt --orderby time_desc --output tsv \
  | grep master \
  | tail -n +2 \
  | xargs -I A az acr repository delete --name scouterna --image skojjt:A --yes
