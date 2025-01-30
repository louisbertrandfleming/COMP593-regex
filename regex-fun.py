'''regex-fun.py -- Learning about regular expressions.
COMP 593 Scripting Applications Winter 2025
Louis Bertrand <louis.bertrand@flemingcollege.ca>

First pass, recognize only numbers with the area code in parentheses
The output can be described as follows:
    0 (705)555-1212 +1.705.555.1212
    1 1-705-555-1212 no match: area code not in parentheses
    2 (705) 555-1212 +1.705.555.1212  OK, ignore the space after area
    3 (705)555-12123 no match: line does not end after last four digits
    4 (705) 555-12123 no match: line does not end after last four digits
    5 (705)5555-1212 no match: there are four digits before the -
'''
import re

def phone_number_brackets(candidate):
    '''Attempt to recognize a phone number with area code in brackets.
    Example: (705)555-1212
    returns the phone number in canonical form: '+1.705.555.1212'
    or empty string.
    See this regex on Regex101.com:
        https://regex101.com/r/qw559F/1
    '''
    patt = r'(\([\d]*\))\s?([\d]{3})-([\d]{4}$)'
    mat = re.search(patt, candidate)
    if mat:
        area = mat.group(1).strip('()')
        return f'+1.{area}.{mat.group(2)}.{mat.group(3)}'
    else:
        return ''

def main():
    with open("phone-numbers.txt", "r") as infile:
        counter = 0
        for line in infile.readlines():
            line = line.strip()  # Remove trailine newline
            print(counter, line, end=' ')
            counter += 1
            bracketed = phone_number_brackets(line)
            if bracketed:
                print(bracketed)
            else:
                print("no match")
    return

if __name__ == '__main__':
    main()

