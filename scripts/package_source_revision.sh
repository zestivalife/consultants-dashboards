#!/bin/sh
set -eu

if [ "$#" -ne 1 ]; then
  echo "Usage: $0 OUTPUT_ROOT" >&2
  exit 2
fi

script_dir=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
if ! repository_root=$(git -C "$script_dir/.." rev-parse --show-toplevel 2>/dev/null); then
  echo "Unable to establish the Git checkout root" >&2
  exit 1
fi
if ! revision=$(git -C "$repository_root" rev-parse --verify HEAD^{commit} 2>/dev/null); then
  echo "Unable to establish the Git HEAD commit" >&2
  exit 1
fi

if ! printf '%s\n' "$revision" | LC_ALL=C grep -Eq '^[0-9a-fA-F]{40}$'; then
  echo "Refusing to package an invalid Git revision" >&2
  exit 1
fi

output_root=$1
service_root="$output_root/services/auth-service"
if [ ! -d "$service_root" ]; then
  echo "Expected packaged service directory is missing: services/auth-service" >&2
  exit 1
fi

destination="$service_root/.source-revision"
printf '%s\n' "$revision" > "$destination"
printf 'Packaged Auth source revision %s\n' "$revision"
