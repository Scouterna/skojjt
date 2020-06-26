cd "$(dirname "$0")"

echo "$PIPELINE_ACR/$SYSTEM_TEAMPROJECT:$BUILD_SOURCEBRANCHNAME-$BUILD_SOURCEVERSION"

sed aks.yaml.template \
    -e "s@%IMAGE%@$PIPELINE_ACR/$SYSTEM_TEAMPROJECT:$BUILD_SOURCEBRANCHNAME-$BUILD_SOURCEVERSION@" \
    -e "s@%NAMESPACE%@skojjt@" \
    > aks.yaml

sed aks.yaml.template \
    -e "s@%IMAGE%@$PIPELINE_ACR/$SYSTEM_TEAMPROJECT:$BUILD_SOURCEBRANCHNAME-$BUILD_SOURCEVERSION@" \
    -e "s@%NAMESPACE%@skojjt-staging@" \
    > aks.staging.yaml
