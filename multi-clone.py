#!/usr/bin/env python3
'''multi-clone.py -- Clone repos identified in D2L downloaded assignments.
COMP 593 Scripting Applications Winter 2025
Louis Bertrand <louis.bertrand@flemingcollege.ca>

Usage:
multi-clone.py <folder-path>

Iterate over every folder in the folder indicated by folder-path
From the folder name in the pattern
    101768-164537 - First Last - Jan 25, 2025 204 PM
extract First, Last, datetime stamp

Search for a .html file in the folder
In that .html file, extract the GitHub user ID and repo name
Form the SSH URL as
    git@github-fleming:userid/repo
Execute git clone with the SSH URL

Throughout, maintain a list of entries with success/fail status
    student = {
        'folder': <path to folder>
        'datetime': <datetime>
        'first': <firstname>,
        'last': <lastname>,
        'userid': <github user ID>,
        'repo': <reponame>,
        'status': <one of success, no_repo, no_html, others TBD>
    }

'''
from sys import argv
import re
import pathlib
import os
from datetime import datetime

# Constants
server_name = "git@github-fleming"  # Different from my usual GitHub ID for SSH key reasons


def get_folder(argv):
    '''Get the command line argv for the folder path.
    Raise OSError if path cannot be resolved.'''
    if len(argv) > 1:
        folder = pathlib.Path(argv[1])
    else:
        print("multi-clone: Expected folder name on command line, using CWD.")
        folder = pathlib.Path.cwd()
    return folder.resolve(strict=True)

def list_folders(folder):
    '''Return a list of folders as Path objects.
    Parameter folder is a Path containing the target folders.
    '''
    folders = []
    for entry in folder.iterdir():
        path = pathlib.Path(entry)
        if path.is_dir():
            folders.append(path)
    return folders

def get_datetime(grps):
   hh = int(grps[5])//100
   mm = int(grps[5])%100
   timestamp = datetime.strptime(f'{grps[2]} {grps[3]} {grps[4]} {hh} {mm} {grps[6]}', r'%b %d %Y %I %M %p')
   return timestamp

def extract_student_info(path):
    folder_name = path.name
    # print(folder_name)
    pattern = r'\d+-\d+\s-\s(\w+) (\.|\w+|\w+-\w+)\s-\s(\w+)\s(\d+),\s(\d{4})\s(\d{3,4})\s(AM|PM)$'

    mat = re.search(pattern, folder_name)
    if mat:
        grps = mat.groups()
        timestamp = get_datetime(grps)
        # print(grp)
        student = {
            'folder': path,
            'datetime': timestamp,
            'first': grps[0],
            'last': grps[1],
        #     'userid': <github user ID>,
        #     'repo': <reponame>,
            'status': 'folder'
        }
        return student
    else:
        return None

def get_github_info(students):
    '''Add GitHub info to each dictionary.'''
    for student in students.values():
        folder = student['folder']
        # Get the .html file 
        for name in folder.glob('*.html'):
            with open(name, 'r') as html:
                for line in html:
                    mat = re.search(r"href=\"(.+)\"", line)
                    if mat:
                        url = mat.group(1)
                        components = url.split('/')
                        student['userid'] = components[3]
                        student['repo'] = components[4]
                        # Form the SSH URL 
                        # Example: git clone git@github-fleming:CSIkid/COMP593-lab2.git
                        student['ssh_url'] = f"{server_name}:{components[3]}/{components[4]}.git"
                        print(student)
    return

def main():
    try:
        main_folder = get_folder(argv)
    except OSError as err:
        print('multi_clone: Cannot resolve directory name from command line')
        print(err)
        exit(0)
    print(main_folder)
    folders = list_folders(main_folder)
    students = {}
    for f in folders:
        student = extract_student_info(f)
        if student:
            students[student['first']+student['last']] = student
    get_github_info(students)  # Add GitHub info to each dictionary

    clone_repos(students)  # spawn a new task for each

    return 0


if __name__ == '__main__':
    main()

