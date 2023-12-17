#!/bin/bash

# Specify the directory containing your .7z files
input_directory="/media/nima/SSD/stackexchange"

# Create a new directory to store the extracted files
output_directory="${input_directory}/extracted"

# Create the output directory if it doesn't exist
mkdir -p "${output_directory}"

# Change into the input directory
cd "${input_directory}" || exit

# Loop through each .7z file and extract it to the corresponding folder
for file in *.7z; do
    # Extract to a folder with the same name as the file (without extension)
    folder_name="${output_directory}/${file%.7z}"
    mkdir -p "${folder_name}"
    7z x -o"${folder_name}" "${file}"
done
