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

# Function to read input safely across different environments
safe_read() {
  local input_var="$1"
  local prompt="$2"
  
  if [[ -n "$prompt" ]]; then
    printf "%s" "$prompt"
  fi
  
  # Simple approach: always try to read from /dev/tty first, then stdin
  if [[ -c "/dev/tty" ]]; then
    read -r "$input_var" < /dev/tty 2>/dev/null || read -r "$input_var" 2>/dev/null || printf -v "$input_var" ""
  else
    read -r "$input_var" 2>/dev/null || printf -v "$input_var" ""
  fi
}

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
    
    # Show OS detection for debugging
    if grep -qEi "(microsoft|wsl)" /proc/version 2>/dev/null || [[ -n "${WSL_DISTRO_NAME:-}" ]]; then
      echo "🔍 Detected: WSL environment"
      is_wsl=true
    else
      echo "🔍 Detected: Non-WSL environment ($(uname -s))"
      is_wsl=false
    fi
    
    # Debug information
    echo "📊 Debug info:"
    echo "  - stdin is terminal: $([ -t 0 ] && echo 'yes' || echo 'no')"
    echo "  - /dev/tty exists: $([ -c '/dev/tty' ] && echo 'yes' || echo 'no')"
    echo "  - /dev/tty readable: $([ -r '/dev/tty' ] && echo 'yes' || echo 'no')"
    echo "  - TERM: ${TERM:-unset}"
    echo "  - SHELL: ${SHELL:-unset}"
    echo "  - Current process tree:"
    ps -o pid,ppid,comm -p $$ -p $PPID 2>/dev/null || echo "    ps command failed"
    echo
    
    adt_count=${#adts_array[@]}
    echo "[DEBUG: Starting loop, adt_count=${adt_count}]"
    
    # Disable exit on error temporarily for the input loop 
    echo "[DEBUG: Disabling exit on error for input loop]"
    set +e  # Disable exit on error
    
    while true; do
      ((adt_count++))
      printf -- "- Enter ADT #%d URL (or press Enter to finish): " "$adt_count"
      
      # Debug before reading
      echo -n " [DEBUG: about to read, TTY available: $([ -c '/dev/tty' ] && echo 'yes' || echo 'no')] "
      
      # Input handling with TTY fallback for Makefile execution
      adt_input=""
      
      # Simple approach: try to read from tty directly, fallback to stdin
      if [[ -c "/dev/tty" ]]; then
        echo "[DEBUG: Trying /dev/tty read...]"
        # Use a more direct approach - open /dev/tty as file descriptor 3
        if exec 3< /dev/tty && read -r adt_input <&3 2>/dev/null; then
          exec 3<&- # Close the file descriptor
          echo "[DEBUG: /dev/tty read succeeded, got: '${adt_input}']"
        else
          exec 3<&- 2>/dev/null || true # Close the file descriptor if it was opened
          echo "[DEBUG: /dev/tty read failed, trying stdin...]"
          if read -r adt_input < /dev/stdin 2>/dev/null; then
            echo "[DEBUG: stdin read succeeded, got: '${adt_input}']"
          else
            echo "[DEBUG: stdin read failed, setting empty]"
            adt_input=""
          fi
        fi
      else
        echo "[DEBUG: /dev/tty not available, trying stdin...]"
        if read -r adt_input 2>/dev/null; then
          echo "[DEBUG: stdin read succeeded, got: '${adt_input}']"
        else
          echo "[DEBUG: stdin read failed, setting empty]"
          adt_input=""
        fi
      fi
      
      echo "[DEBUG: Final adt_input value: '${adt_input}']"
      echo "[DEBUG: Empty check: $([ -z "$adt_input" ] && echo 'empty' || echo 'not empty')]"
      
      # If empty input, we're done
      if [[ -z "$adt_input" ]]; then
        echo "[DEBUG: Breaking loop due to empty input]"
        break
      fi
      
      # Add to array
      adts_array+=("$adt_input")
      echo "  ✅ Added: $adt_input"
      echo "[DEBUG: Array now has ${#adts_array[@]} items]"
    done
    
    # Re-enable exit on error after the loop
    echo "[DEBUG: Re-enabling exit on error]"
    set -e
    
    # Join array into space-separated string and quote it
    value=$(printf "%s " "${adts_array[@]}")
    value=${value% }  # Remove trailing space
    value="\"$value\""  # Quote the entire value
    
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
    # Prompt and read input
    safe_read input "$(printf -- "- Enter value for %s [%s]: " "$key" "$show")"

    # Required key enforcement (for mandatory keys) - only OPENAI_API_KEY is truly required
    if [[ "$key" == "OPENAI_API_KEY" ]]; then
      while [[ -z "$input" && -z "$current" ]]; do
        safe_read input "$(printf -- "  (Required) Enter value for %s: " "$key")"
      done
    fi

    # If input is empty, use the default value (for fields with defaults) or empty (for truly optional fields)
    if [[ -z "$input" ]]; then
      value="$show"  # Use the default/current value
      break
    fi
    
    value="$input"
    
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
