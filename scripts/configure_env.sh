#!/usr/bin/env bash
set -euo pipefail

EXAMPLE_FILE=${1:-.env.example}
ENV_FILE=${2:-.env}

if [[ ! -f "$EXAMPLE_FILE" ]]; then
  echo "❌ $EXAMPLE_FILE not found. Cannot configure environment." >&2
  exit 1
fi

# Create .env if missing by copying the example
if [[ ! -f "$ENV_FILE" ]]; then
  cp "$EXAMPLE_FILE" "$ENV_FILE"
fi

echo "🔧 Configuring environment variables from $EXAMPLE_FILE"
echo "(Press Enter to accept the shown value. Leave blank to clear optional values.)"

# Determine TTY for interactive input
TTY_IN="/dev/tty"
if [[ ! -r "$TTY_IN" ]]; then
  TTY_IN="/dev/stdin"
fi

while IFS= read -r line; do
  # Skip comments and blank lines
  [[ -z "$line" || "$line" =~ ^[[:space:]]*# ]] && continue

  # Extract key (left side of first =) - portable across BSD/GNU
  key=$(printf '%s' "$line" | awk -F'=' '{k=$1; gsub(/^\s+|\s+$/, "", k); print k}')
  [[ -z "$key" ]] && continue

  # Current value in .env (if any) and default from example
  current=$(grep -E "^${key}=" "$ENV_FILE" | sed "s/^${key}=//" || true)
  default=$(grep -E "^${key}=" "$EXAMPLE_FILE" | sed "s/^${key}=//" || true)
  show=${current:-$default}

  # Prompt
  printf -- "- Enter value for %s [%s]: " "$key" "$show"
  # Read from TTY to avoid consuming the .env.example stream
  if ! read -r input < "$TTY_IN"; then
    input=""
  fi

  # Required key enforcement (for mandatory keys)
  if [[ "$key" == "OPENAI_API_KEY" || "$key" == "OPENAI_MODEL" || "$key" == "ADT_UTILS_REPO" ]]; then
    while [[ -z "$input" && -z "$current" ]]; do
      printf -- "  (Required) Enter value for %s: " "$key"
      if ! read -r input < "$TTY_IN"; then
        input=""
      fi
    done
  fi

  value=${input:-$show}

  # Update or append the key in .env
  if grep -qE "^${key}=" "$ENV_FILE"; then
    # Use temp file to be portable across sed variants
    tmp_file=$(mktemp)
    awk -v k="${key}" -v v="${value}" 'BEGIN{changed=0} {
      if ($0 ~ "^"k"=") { print k"="v; changed=1 } else { print }
    } END{ exit (changed?0:0) }' "$ENV_FILE" > "$tmp_file"
    mv "$tmp_file" "$ENV_FILE"
  else
    printf "\n%s=%s\n" "$key" "$value" >> "$ENV_FILE"
  fi
done < "$EXAMPLE_FILE"

echo "✅ Environment configured and saved to $ENV_FILE"
