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
        'status': <one of success, no_repo, no_html, github, cloned, problem, others TBD>
    }

ToDo: guard against broken URLs like *.git.git
    implemented but not tested

'''
from sys import argv, stderr
import re  # Regular expressions to dig through folder names
import pathlib  # file & folder path objects
import os
from datetime import datetime  # The strptime() method to convert strings to date-time
import subprocess  # for the git clone task

# Constants
# OpenSSH, to use different entry in .ssh/config
server_name = "git@github-fleming"  # Different from my usual GitHub ID for SSH key reasons
# Windows: the git command uses a built-in OpenSSH client so it does not use
# the PuTTY installation or Pageant. Configure the usual .ssh/config file
# the same way as you would under Linux/BSD.
    # Host github-fleming
    #     Hostname github.com
    #     IdentityFile C:/Users/Louis/.ssh/id_ed25519-win11-fleming


def get_folder(argv):
    '''Get the command line argv for the folder path.
    Raise OSError if path cannot be resolved.'''
    if len(argv) > 1:
        folder = pathlib.Path(argv[1])
    else:
        print("multi-clone: Expected folder name on command line, using CWD.", file=stderr)
        folder = pathlib.Path.cwd()
    return folder.resolve(strict=True)

def list_folders(folder):
    '''Return a list of folders as pathlib.Path objects.
    Parameter folder is a Path containing the target folders.
    '''
    folders = []
    for entry in folder.iterdir():
        path = pathlib.Path(entry)
        if path.is_dir():
            folders.append(path)
    return folders

def get_datetime(grps):
    '''The groups returned by the regex are:
        MON DD YYYY HHMM AM
        HHMM could also be HMM, hence the divide by 100 and modulo 100,
        AM could be PM; this is where strptime() very convenient
        (so D2L doesn't know about 24-hour time?).
    return a datetime instance.
    '''
    hh = int(grps[5])//100
    mm = int(grps[5])%100
    timestamp = datetime.strptime(f'{grps[2]} {grps[3]} {grps[4]} {hh} {mm} {grps[6]}', r'%b %d %Y %I %M %p')
    return timestamp

def extract_student_info(path):
    '''Using a regex, break up the folder name produced by the D2L downloader into groups.
        NNNNN-MMMMMM - First Last - MON DD, 2025 HHMM PM
    return a dictionary of student information, or None if the regex did not match anything.
    '''
    # Extract the last component of the path, the actual folder name.
    folder_name = path.name
    pattern = r'\d+-\d+\s-\s(\w+) (\.|\w+|\w+-\w+)\s-\s(\w+)\s(\d+),\s(\d{4})\s(\d{3,4})\s(AM|PM)$'
    mat = re.search(pattern, folder_name)
    if mat:
        grps = mat.groups()
        timestamp = get_datetime(grps)
        student = {
            'folder': path,
            'datetime': timestamp,
            'first': grps[0],
            'last': grps[1],
        # the next two will be added later, from the HTML file in the folder.
        #     'userid': <github user ID>,
        #     'repo': <reponame>,
            'status': 'folder'  # Progress indicator, means "have folder"
        }
        return student
    else:
        return None  # regex did not match

def get_github_info(students):
    '''Add GitHub info to each dictionary.
    Look for the .html file created by the D2L downloader. This file contains
    the comment that should give the URL to the repo on GitHub.
    Adds user ID and repo name to the student's dictionary,
    then forms the proper URL to clone using ssh (instead of https).
    returns None
    '''
    for student in students.values():
        if not student['status'] == "folder":
            continue
        folder = student['folder']
        # print(f"folder={folder}")  # Debug only
        # Get the .html file(s)
        for name in folder.glob('*.html'):
            get_student_url(student, name)
    return

def get_student_url(student, name):
    # Pattern to match <a> tag hyperlink or <p> tag plain text paste.
    #  https://regex101.com/r/8Z43u4/1
    PATTERN = r'href=(?:\")(https\://github\.com/.+/.+)(?:\")|(?:<p>)(https://github.com/.+/.+)(?:</p>)'
    with open(name, 'r', encoding='utf-8') as html:
        for line in html:
            mat = re.search(PATTERN, line)
            if mat:
                # The URL could be in one of the groups, which one?
                for grp in mat.groups():
                    if 0 == str(grp).find(r"https://github.com"):
                        url = str(grp)
                        break
                # print(url, file=stderr)  # Debug only
                components = url.split('/')  # split along / separator
                # print(f"Components = {components}", file=stderr)   # Debug only
                student['userid'] = components[3]
                # remove any extraneous ".git" name extensions
                repo = components[4]
                # print(f"repo = {repo}", file=stderr)  # Debug only
                while re.search(r"\.git$", repo):
                    repo = re.sub(r"\.git$", "", repo)
                    # print(f"trimmed = {repo}", file=stderr)  # Debug only
                student['repo'] = repo
                # print(f"student.repo = {student['repo']}", file=stderr)  # Debug only

                # Form the SSH URL
                # Example: git clone git@github-fleming:CSIkid/COMP593-lab2.git
                student['ssh_url'] = f"{server_name}:{components[3]}/{repo}.git"
                # print(f"student.ssh_url = {student['ssh_url']}", file=stderr)  # Debug only
                student['status'] = 'github'  # Means that we have the GitHub info.
                return
            else:
                student['ssh_url'] = ""
                student['status'] = 'no_url'

def clone_repos(students):
    '''Spawn a new task for each to git clone the student repo.'''
    for k in students.keys():
        student = students[k]
        if student['status'] != 'github':
            print(f"multi-clone: error: No GitHub URL found for student {k}.")
            continue
        command = ("git", "clone", student['ssh_url'])
        # print(command, file=stderr)  # Debug only
        try:
            completed = subprocess.run( command,
                               stdin=None,
                               input=None,
                               stdout=None,
                               stderr=None,
                               capture_output=True,
                               shell=False,
                               cwd=student['folder'],
                               timeout=None,
                               check=False,
                               encoding=None,
                               errors=None,
                               text=True,
                               env=None,
                               universal_newlines=None
                            )
            # print(f'{k}: return={completed.returncode}')
            if completed.returncode == 0:
                student['status'] = 'cloned'
            else:
                student['status'] = 'problem'
                print(f'  stderr="{completed.stderr}"', file=stderr)
        except subprocess.CalledProcessError as err:
            student['status'] = 'problem'
            print(f"Subprocess failed for student {student['first']} {student['last']}\n"
                  f"{err.cmd}: {err.output}", file=stderr)
    return  # return nothing, everything is in the dictionary

def main():
    try:
        main_folder = get_folder(argv)
    except OSError as err:
        print(f'multi_clone: Cannot resolve directory name from command line\n    {err}')
        exit(0)
    print(f'[{datetime.now().isoformat()}] multi-clone.py: Processing {main_folder}')
    folders = list_folders(main_folder)
    students = {}
    for f in folders:
        student = extract_student_info(f)
        # Add the student dictionary to the dictionary of students,
        # using first+last as the key.
        # Check datetime to make sure that we are using the most recent submission
        if student:
            student_key = student['first'].lower() + student['last'].lower()
            # If student already in students, check datetime to keep latest
            if student_key in students:
                prev_datetime = students[student_key]['datetime']
                if student['datetime'] > prev_datetime:
                    del students[student_key]
            students[student_key] = student

    # print(f'students=\n{students}\n', file=stderr)
    get_github_info(students)  # Add GitHub info to each dictionary
    # spawn a new task for each, recording the outcome in the dictionary.
    clone_repos(students)
    # Report the outcome
    for k in students.keys():
        student = students[k]
        print(f"{k}: {student['status']}")
    return 0


if __name__ == '__main__':
    main()
