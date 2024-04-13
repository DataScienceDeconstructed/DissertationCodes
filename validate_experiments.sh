#!/bin/bash

# Function to search for files with a specific word
search_files() {
    local search_word="$1"
    local directory="$2"

    # Loop through files and directories in the specified directory
    for entry in "$directory"/*; do
        if [ -d "$entry" ]; then
            # If entry is a directory, recursively search it
            search_files "$search_word" "$entry"
        elif [ -f "$entry" ]; then
            # If entry is a file, check if it contains the search word
            if grep -qi "$search_word" "$entry"; then
                echo "Found '$search_word' in: $dictionary/$entry"
            fi
        fi
    done
}

# Check if the user provided a search word
if [ -z "$1" ]; then
    echo "Usage: $0 <search_word>"
    exit 1
fi

# Get the search word from command line argument
search_word="$1"

# Call the search_files function with the current directory
search_files "$search_word" "$(pwd)"
