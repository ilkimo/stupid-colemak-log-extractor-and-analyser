#!/bin/bash

# Set default number of commands to 100 if no argument is provided
num_commands=${1:-100}

# Check if the argument is a positive integer
if ! [[ $num_commands =~ ^[1-9][0-9]*$ ]]; then
    echo "Error: Argument must be a positive integer."
    exit 1
fi

# Check if the .bash_history file exists and is readable
if [[ -r ~/.bash_history ]]; then
    # Process the .bash_history file to find the top used commands
    awk '{print $1}' ~/.bash_history | sort | uniq -c | sort -nr | head -n "$num_commands" | awk '{print $2}' > "bash-commands-$num_commands.txt"
    echo "The top $num_commands commands have been saved to bash-commands-$num_commands.txt"
else
    echo "Error: The .bash_history file does not exist or is not readable."
fi

