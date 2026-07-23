#!/usr/bin/env bash
# Setup script for /speckit-specify command
# Returns JSON with feature spec metadata

set -e

# Parse command line arguments
JSON_MODE=false
ARGS=()

for arg in "$@"; do
    case "$arg" in
        --json)
            JSON_MODE=true
            ;;
        --help|-h)
            echo "Usage: $0 [--json]"
            echo "  --json    Output results in JSON format"
            echo "  --help    Show this help message"
            exit 0
            ;;
        *)
            ARGS+=("$arg")
            ;;
    esac
done

# Source common functions
SCRIPT_DIR="$(CDPATH="" cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/common.sh"

# Get feature paths
_paths_output=$(get_feature_paths) || { echo "ERROR: Failed to resolve feature paths" &>2; exit 1; }
eval "$_paths_output"
unset _paths_output

# Ensure the feature directory exists
mkdir -p "$FEATURE_DIR"

# Copy spec template if spec doesn't already exist
if [[ -f "$FEATURE_SPEC" ]]; then
    if $JSON_MODE; then
        echo "Spec already exists at $FEATURE_SPEC, skipping template copy" &>2
    else
        echo "Spec already exists at $FEATURE_SPEC, skipping template copy"
    fi
else
    TEMPLATE=$(resolve_template "spec-template" "$REPO_ROOT") || true
    if [[ -n "$TEMPLATE" ]] && [[ -f "$TEMPLATE" ]]; then
        cp "$TEMPLATE" "$FEATURE_SPEC"
        if $JSON_MODE; then
            echo "Copied spec template to $FEATURE_SPEC" &>2
        else
            echo "Copied spec template to $FEATURE_SPEC"
        fi
    else
        if $JSON_MODE; then
            echo "Warning: Spec template not found" &>2
        else
            echo "Warning: Spec template not found"
        fi
        touch "$FEATURE_SPEC"
    fi
fi

# Output results
if $JSON_MODE; then
    if has_jq; then
        jq -cn \
            --arg feature_spec "$FEATURE_SPEC" \
            --arg feature_dir "$FEATURE_DIR" \
            '{FEATURE_SPEC:$feature_spec,FEATURE_DIR:$feature_dir}'
    else
        printf '{"FEATURE_SPEC":"%s","FEATURE_DIR":"%s"}\n' \
            "$(json_escape "$FEATURE_SPEC")" "$(json_escape "$FEATURE_DIR")"
    fi
else
    echo "FEATURE_SPEC: $FEATURE_SPEC"
    echo "FEATURE_DIR: $FEATURE_DIR"
fi
