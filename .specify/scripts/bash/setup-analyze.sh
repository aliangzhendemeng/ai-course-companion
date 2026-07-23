#!/usr/bin/env bash
# Setup script for /speckit-analyze command
# Returns JSON with analysis metadata

set -e

# Parse command line arguments
JSON_MODE=false

for arg in "$@"; do
    case "$arg" in
        --json) JSON_MODE=true ;;
        --help|-h)
            echo "Usage: $0 [--json]"
            echo "  --json    Output results in JSON format"
            echo "  --help    Show this help message"
            exit 0
            ;;
        *) echo "ERROR: Unknown option '$arg'" >&2; exit 1 ;;
    esac
done

# Source common functions
SCRIPT_DIR="$(CDPATH="" cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/common.sh"

# Get feature paths
_paths_output=$(get_feature_paths) || { echo "ERROR: Failed to resolve feature paths" >&2; exit 1; }
eval "$_paths_output"
unset _paths_output

# Validate required files exist
for file in "$FEATURE_SPEC" "$IMPL_PLAN" "$TASKS"; do
    if [[ ! -f "$file" ]]; then
        echo "ERROR: Required file not found: $file" >&2
        exit 1
    fi
done

# Output results
if $JSON_MODE; then
    if has_jq; then
        jq -cn \
            --arg feature_dir "$FEATURE_DIR" \
            --arg spec "$FEATURE_SPEC" \
            --arg plan "$IMPL_PLAN" \
            --arg tasks "$TASKS" \
            '{FEATURE_DIR:$feature_dir,SPEC:$spec,PLAN:$plan,TASKS:$tasks}'
    else
        printf '{"FEATURE_DIR":"%s","SPEC":"%s","PLAN":"%s","TASKS":"%s"}\n' \
            "$(json_escape "$FEATURE_DIR")" \
            "$(json_escape "$FEATURE_SPEC")" \
            "$(json_escape "$IMPL_PLAN")" \
            "$(json_escape "$TASKS")"
    fi
else
    echo "FEATURE_DIR: $FEATURE_DIR"
    echo "SPEC: $FEATURE_SPEC"
    echo "PLAN: $IMPL_PLAN"
    echo "TASKS: $TASKS"
fi
