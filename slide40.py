# COMP 593 Week 4 regex example slides 38-41
# Extract names and phone numbers from a text file
import re
with open(r'muppets.txt', 'r') as file:
    pattern = r'NAME=(.*?)\s.*?PHONE=(.*?)\s'
    # Iterate through file line by line
    for line in file:
        # Check line for regex match
        match = re.search(pattern, line)
        if match:
            # Extract and print capturing group info
            name = match.group(1)
            phone = match.group(2)
            print(f"{name}'s phone number is {phone}.")
