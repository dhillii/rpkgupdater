"""
@file rpkgupdate.py
@author David Hill, Jr.
@brief This script will scan all repos that use the R programming language
       in the cooper center organization, collect all r packages used and and install them locally on your machine.
"""

from github import Github
import sys
import getpass
import stdiomask
import re
import rpy2.robjects.packages as rpackages
from rpy2.robjects.vectors import StrVector
from subprocess import check_call, CalledProcessError
import os
from progress.spinner import Spinner


"""
@brief this method gets all the repos from the cooper center organization
"""
def setup():
    # login
    user = input("Github Username: ")
    password = stdiomask.getpass("Github Password: ")

    try:
        g = Github(user, password)
    except:
        print("Username or Password incorrect.")
        return

    # get cooper center organization
    try:
        org = g.get_organization("coopercenter")
    except:
        print("Could not get organization or it does not exist.")
        return

    # get all repos of organization
    org_repos = org.get_repos('all')

    return org_repos

"""
@param set r_packages - the set of r packages that we find
@param FileContents file - the R or Rmd file
@brief gets all substrings between library() and require() token parentheses and
adds those dependency strings to the set of r packages
"""
def GetDeps(r_packages, file):
    contents = str(file.decoded_content)
    pattern1 = r"library\((.*?)\)"
    pattern2 = r"require\((.*?)\)"
    result = re.findall(pattern1, contents)
    result2 = re.findall(pattern2, contents)
    results = result + result2
    for dep in results:
        r_packages.add(dep)

def main():
    r_repos = []
    r_pkgs = set()
    content_files = []
    r_files = []

    # this is needed for something R related
    utils = rpackages.importr('utils')


    # get all repos from setup
    repos = setup()

    spinner1 = Spinner('Scanning Github...')
    spinner1.next()


    if repos:
        # gets all R repos
        for repo in repos:
            spinner1.next()
            if repo.language == 'R':
                r_repos.append(repo)

        # get all files from all R repos recursively
        for repo in r_repos:
            spinner1.next()
            contents = repo.get_contents("")
            while contents:
                spinner1.next()
                file_content = contents.pop(0)
                if file_content.type == "dir":
                    contents.extend(repo.get_contents(file_content.path))
                else:
                    content_files.append(file_content)

        # get all r and rmd files
        for file in content_files:
            spinner1.next()
            if file.name.endswith('.R') or file.name.endswith('.Rmd'):
                r_files.append(file)
        spinner1.finish()

        spinner2 = Spinner('Finding Dependencies...')

        # Get deps from files
        for file in r_files:
            spinner2.next()
            GetDeps(r_pkgs, file)

        spinner2.finish()
        print("\nDependencies Collected. Installing!")

        # getting a little jank here but it works. Might improve later...
        pkgs_to_install = []
        """pkgs_to_install.append('devtools')
        pkgs_to_install.append('pkgconfig')
        pkgs_to_install.append('latticeExtra')
        pkgs_to_install.append('cowplot')
        pkgs_to_install.append('rstatix')
        pkgs_to_install.append('car')
        pkgs_to_install.append('XML')
        pkgs_to_install.append('scholar')
        pkgs_to_install.append('dependencies = TRUE')"""

        pkgs_to_install += [x for x in r_pkgs if not rpackages.isinstalled(x)]

        # remove any double quotes
        pkgs_to_install = [i.replace('"', '') for i in pkgs_to_install]

        print("\nNeed to install " + str(pkgs_to_install) + " packages...\n")

        if len(pkgs_to_install) > 0:
            utils.install_packages(StrVector(pkgs_to_install))
        else:
            print("All packages up to date!")


    else:
        exit()



if __name__ == "__main__":
    main()
