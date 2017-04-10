#!/usr/bin/env python2

# Copyright (C) 2013 Cybojenix <anthonydking@gmail.com>
# Copyright (C) 2013 The OmniROM Project
# Copyright (C) 2014/2015 crDroid Android
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

from __future__ import print_function
import json
import sys
import os
import re
from xml.etree import ElementTree as ES
# Use the urllib importer from the Cyanogenmod roomservice
try:
    # For python3
    import urllib.request
except ImportError:
    # For python2
    import imp
    import urllib2
    urllib = imp.new_module('urllib')
    urllib.request = urllib2

# Config
# set this to the default remote to use in repo
default_rem = "github"
# set this to the default revision to use (branch/tag name)
default_rev = "android-7.1"
# set this to the remote that you use for projects from your team repos
# example fetch="https://github.com/omnirom"
default_team_rem = "github"
# this shouldn't change unless google makes changes
local_manifest_dir = ".repo/local_manifests"
# change this to your name on github (or equivalent hosting)
android_team = "purity-devices"


def check_repo_exists(git_data):
    if not int(git_data.get('total_count', 0)):
        raise Exception("{} not found in {} Github, exiting "
                        "roomservice".format(device, android_team))


# Note that this can only be done 5 times per minute
def search_github_for_device(device):
    git_device = '+'.join(re.findall('[a-z]+|[\d]+',  device))
    git_search_url = "https://api.github.com/search/repositories" \
                     "?q=%40{}+android_device+{}+fork:true".format(android_team, git_device)
    git_req = urllib.request.Request(git_search_url)
    try:
        response = urllib.request.urlopen(git_req)
    except urllib.request.HTTPError:
        raise Exception("There was an issue connecting to github."
                        " Please try again in a minute")
    git_data = json.load(response)
    check_repo_exists(git_data)
    print("found the {} device repo".format(device))
    return git_data


def get_device_url(git_data):
    device_url = ""
    for item in git_data['items']:
        temp_url = item.get('html_url')
        if "{}/android_device".format(android_team) in temp_url:
            try:
                temp_url = temp_url[temp_url.index("android_device"):]
            except ValueError:
                pass
            else:
                if temp_url.endswith(device):
                    device_url = temp_url
                    break

    if device_url:
        return device_url
    raise Exception("{} not found in {} Github, exiting "
                    "roomservice".format(device, android_team))


def parse_device_directory(device_url,device):
    to_strip = "android_device"
    repo_name = device_url[device_url.index(to_strip) + len(to_strip):]
    repo_name = repo_name[:repo_name.index(device)]
    repo_dir = repo_name.replace("_", "/")
    repo_dir = repo_dir + device
    return "device{}".format(repo_dir)


# Thank you RaYmAn
def iterate_manifests(check_all):
    files = []
    if check_all:
        for file in os.listdir(local_manifest_dir):
            files.append(os.path.join(local_manifest_dir, file))
    files.append('.repo/manifest.xml')
    for file in files:
        try:
            man = ES.parse(file)
            man = man.getroot()
        except IOError, ES.ParseError:
            print("WARNING: error while parsing %s" % file)
        else:
            for project in man.findall("project"):
                yield project


def check_project_exists(url):
    for project in iterate_manifests(True):
        if project.get("name") == url:
            return True
    return False


def check_dup_path(directory):
    for project in iterate_manifests(False):
        if project.get("path") == directory:
            print ("Duplicate path %s found! Removing" % directory)
            return project.get("name")
    return None


# Use the indent function from http://stackoverflow.com/a/
