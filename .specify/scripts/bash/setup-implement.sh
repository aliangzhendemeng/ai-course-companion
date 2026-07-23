#!/usr/bin/env bash
# Setup script for /speckit-implement command
# Returns JSON with implementation metadata

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
if [[ ! -f "$TASKS" ]]; then
    echo "ERROR: tasks.md not found in $FEATURE_DIR" >&2
    echo "Run /speckit-tasks first to create the task list." >&2
    exit 1
fi

if [[ ! -f "$IMPL_PLAN" ]]; then
    echo "ERROR: plan.md not found in $FEATURE_DIR" >&2
    echo "Run /speckit-plan first to create the implementation plan." >&2
    exit 1
fi

# Output results
if $JSON_MODE; then
    if has_jq; then
        jq -cn \
            --arg feature_dir "$FEATURE_DIR" \
            --arg tasks "$TASKS" \
            --arg impl_plan "$IMPL_PLAN" \
            '{FEATURE_DIR:$feature_dir,TASKS:$tasks,IMPL_PLAN:$impl_plan}'
    else
        printf '{"FEATURE_DIR":"%s","TASKS":"%s","IMPL_PLAN":"%s"}\n' \
            "$(json_escape "$FEATURE_DIR")" "$(json_escape "$TASKS")" "$(json_escape "$IMPL_PLAN")"
    fi
else
    echo "FEATURE_DIR: $FEATURE_DIR"
    echo "TASKS: $TASKS"
    echo "IMPL_PLAN: $IMPL_PLAN"
fi
