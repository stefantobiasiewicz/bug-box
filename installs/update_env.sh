#!/bin/bash

if [ $# -ne 2 ]; then
    echo "Usage: $0 <environment_variable_name> <new_value>"
    exit 1
fi

variable_name="$1"
new_value="$2"

config_file="/opt/bug-box/set-env.sh"

if ! grep -q "^export $variable_name=" "$config_file"; then
    echo "Environment variable '$variable_name' does not exist in the configuration file."
    exit 1
fi

sed -i "s/^export $variable_name=.*/export $variable_name=\"$new_value\"/" "$config_file"

echo "Updated environment variable '$variable_name' to '$new_value' in the configuration file."
