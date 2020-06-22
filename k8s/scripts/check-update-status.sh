#!/bin/bash -e

target=$(echo "${MONOREPO_BUILD_TARGET:-$1}" | tr '[:upper:]' '[:lower:]')
subpath="${SUBPATH:-$2}"

if [[ "$target" == "" ]] || [[ "$subpath" == "" ]]; then
	echo "Usage: ./$0 [<build target> [<subpath>]]"
	echo "Arguments can also be provided through the environment variables"
	echo "\$MONOREPO_BUILD_TARGET and \$SUBPATH"
	exit 1
fi

tag="$(git tag | grep "$target" | tail -n 1 | tr -d '\n')"

updated='false'

if [[ "$tag" == "" ]] || [[ "$(git log "$tag"..HEAD --format=%h -- "$subpath" | tr -d '\n')" != "" ]]; then
	updated='true'
fi

echo "The $target project is $([[ "$updated" == 'true' ]] && echo 'updated' || echo 'not updated') since the last build."

for setter in "##vso[task.setvariable variable=updated]$updated" "##vso[task.setvariable variable=updated;isOutput=true]$updated"; do
	echo "$setter"
	echo "'$setter"
done
