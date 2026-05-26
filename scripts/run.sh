#!/bin/bash
"""
SMS Receiver Skill Launcher
"""

# Get the directory of this script
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
SKILL_DIR="$(dirname "$SCRIPT_DIR")"

# Check if Python is available
if ! command -v python3 &> /dev/null; then
    echo "Error: Python 3 is required"
    exit 1
fi

# Check if the skill script exists
SKILL_SCRIPT="$SCRIPT_DIR/sms_receiver.py"
if [ ! -f "$SKILL_SCRIPT" ]; then
    echo "Error: SMS receiver script not found"
    exit 1
fi

# Run the skill with provided arguments
python3 "$SKILL_SCRIPT" "$@"
