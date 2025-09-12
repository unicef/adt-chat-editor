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

# Validation functions
validate_openai_key() {
  local key_value="$1"
  if [[ -n "$key_value" && ! "$key_value" =~ ^sk- ]]; then
    echo "❌ OPENAI_API_KEY must start with 'sk-'"
    return 1
  fi
  return 0
}

validate_github_token() {
  local token_value="$1"
  if [[ -n "$token_value" && ! "$token_value" =~ ^github_pat ]]; then
    echo "❌ GITHUB_TOKEN must start with 'github_pat'"
    return 1
  fi
  return 0
}

validate_env_value() {
  local key="$1"
  local value="$2"
  
  case "$key" in
    "OPENAI_API_KEY")
      validate_openai_key "$value"
      ;;
    "GITHUB_TOKEN")
      validate_github_token "$value"
      ;;
    *)
      return 0
      ;;
  esac
}

while IFS= read -r line; do
  # Skip comments and blank lines
  [[ -z "$line" || "$line" =~ ^[[:space:]]*# ]] && continue

  # Extract key (left side of first =) - portable across BSD/GNU
  key=$(printf '%s' "$line" | awk -F'=' '{k=$1; gsub(/^\s+|\s+$/, "", k); print k}')
  [[ -z "$key" ]] && continue

  # Skip ADT_UTILS_REPO - automatically use default value without prompting
  if [[ "$key" == "ADT_UTILS_REPO" ]]; then
    # Get current value in .env (if any) and default from example
    current=$(grep -E "^${key}=" "$ENV_FILE" | sed "s/^${key}=//" || true)
    default=$(grep -E "^${key}=" "$EXAMPLE_FILE" | sed "s/^${key}=//" || true)
    value=${current:-$default}
    
    # Update or append the key in .env silently
    if grep -qE "^${key}=" "$ENV_FILE"; then
      tmp_file=$(mktemp)
      awk -v k="${key}" -v v="${value}" 'BEGIN{changed=0} {
        if ($0 ~ "^"k"=") { print k"="v; changed=1 } else { print }
      } END{ exit (changed?0:0) }' "$ENV_FILE" > "$tmp_file"
      mv "$tmp_file" "$ENV_FILE"
    else
      printf "\n%s=%s\n" "$key" "$value" >> "$ENV_FILE"
    fi
    
    echo "✅ ADT_UTILS_REPO automatically set to: $value"
    continue
  fi

  # Handle ADTS interactively - collect one by one
  if [[ "$key" == "ADTS" ]]; then
    echo "🔗 Setting up ADTS (Accessible Digital Textbooks)"
    echo "Enter ADT repository URLs one by one. Press Enter with empty input to finish."
    
    # Get current ADTS value and split into array
    current_adts=$(grep -E "^${key}=" "$ENV_FILE" | sed "s/^${key}=//" || true)
    adts_array=()
    
    # If current value exists, populate array
    if [[ -n "$current_adts" ]]; then
      echo "Current ADTs:"
      count=1
      while IFS= read -r adt_url; do
        if [[ -n "$adt_url" ]]; then
          echo "  $count. $adt_url"
          adts_array+=("$adt_url")
          ((count++))
        fi
      done <<< "$(echo "$current_adts" | tr ' ' '\n')"
      echo
    fi
    
    echo "Add new ADTs (or press Enter to keep current list):"
    adt_count=${#adts_array[@]}
    
    while true; do
      ((adt_count++))
      printf -- "- Enter ADT #%d URL (or press Enter to finish): " "$adt_count"
      
      if ! read -r adt_input < "$TTY_IN"; then
        adt_input=""
      fi
      
      # If empty input, we're done
      if [[ -z "$adt_input" ]]; then
        break
      fi
      
      # Add to array
      adts_array+=("$adt_input")
      echo "  ✅ Added: $adt_input"
    done
    
    # Join array into space-separated string
    value=$(printf "%s " "${adts_array[@]}")
    value=${value% }  # Remove trailing space
    
    # Update or append the key in .env
    if grep -qE "^${key}=" "$ENV_FILE"; then
      tmp_file=$(mktemp)
      awk -v k="${key}" -v v="${value}" 'BEGIN{changed=0} {
        if ($0 ~ "^"k"=") { print k"="v; changed=1 } else { print }
      } END{ exit (changed?0:0) }' "$ENV_FILE" > "$tmp_file"
      mv "$tmp_file" "$ENV_FILE"
    else
      printf "\n%s=%s\n" "$key" "$value" >> "$ENV_FILE"
    fi
    
    if [[ ${#adts_array[@]} -gt 0 ]]; then
      echo "✅ ADTS configured with ${#adts_array[@]} repositories"
    else
      echo "✅ ADTS left empty"
    fi
    continue
  fi

  # Current value in .env (if any) and default from example
  current=$(grep -E "^${key}=" "$ENV_FILE" | sed "s/^${key}=//" || true)
  default=$(grep -E "^${key}=" "$EXAMPLE_FILE" | sed "s/^${key}=//" || true)
  show=${current:-$default}
  
  # Truncate sensitive values for display
  if [[ "$key" == "OPENAI_API_KEY" || "$key" == "GITHUB_TOKEN" ]]; then
    if [[ -n "$show" ]]; then
      show="${show:0:15}..."
    fi
  fi

  # Interactive input loop with validation
  while true; do
    # Prompt
    printf -- "- Enter value for %s [%s]: " "$key" "$show"
    # Read from TTY to avoid consuming the .env.example stream
    if ! read -r input < "$TTY_IN"; then
      input=""
    fi

    # Required key enforcement (for mandatory keys) - ADT_UTILS_REPO removed
    if [[ "$key" == "OPENAI_API_KEY" || "$key" == "OPENAI_MODEL" ]]; then
      while [[ -z "$input" && -z "$current" ]]; do
        printf -- "  (Required) Enter value for %s: " "$key"
        if ! read -r input < "$TTY_IN"; then
          input=""
        fi
      done
    fi

    value=${input:-$show}
    
    # Skip validation if value is empty (for optional fields)
    if [[ -z "$value" ]]; then
      break
    fi
    
    # Validate the input value
    if validate_env_value "$key" "$value"; then
      break
    else
      echo "  Please enter a valid value."
      # Reset show to avoid confusion in the next prompt
      show=""
    fi
  done

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
