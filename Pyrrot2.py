'''
Created on 02/04/2010

@author: Jr. Hames
'''

#edit the following options according to your needs
DIRECTORIES = ["/path/to/your/video/files", "/path/to/your/video/files2"]
LANGUAGES = ["pt","en"]
#end of configurations


import cPickle
import StringIO
import hashlib
import os
import random
import re
import time
import urllib
import urllib2
import urllib2_file

base_url = 'http://url.to.subdb:port/subdb/?{0}'
user_agent = 'Parrot/2.0 (Compatible; Pyrrot)'

def get_hash(name):
    readsize = 64 * 1024
    with open(name, 'rb') as f:
        size = os.path.getsize(name)
        data = f.read(readsize)
        f.seek(-readsize, os.SEEK_END)
        data += f.read(readsize)
    return hashlib.md5(data).hexdigest()

def download(language, hash, filename):
    params = {'action': 'download', 'language': language, 'hash': hash}
    url = base_url.format(urllib.urlencode(params))
    req = urllib2.Request(url)
    req.add_header('User-Agent', user_agent)
    try:
        response = urllib2.urlopen(req)
        filename = os.path.splitext(filename)[0] + ".srt"
        with open(filename, "wb") as fout:
            fout.write(response.read())
        return 200
    except urllib2.HTTPError, e:
        return e.code

def upload(hash, filename):
    filename = os.path.splitext(filename)[0] + ".srt"
    fd_file = open(filename)
    fd = StringIO.StringIO()
    fd.name = hash + ".srt"
    fd.write(fd_file.read())
    data = { 'hash': hash, 'file': fd }
    params = {'action': 'upload', 'hash': hash}
    url = base_url.format(urllib.urlencode(params))
    req = urllib2.Request(url)
    req.add_header('User-Agent', user_agent)
    try:
        urllib2.urlopen(req, data)
    except urllib2.HTTPError as e:
        return e.code

def get_files_without_subs(rootdir):
    filelist = []
    for root, subfolders, files in os.walk(rootdir):
        for file in files:
            if not re.search("\.(srt|sub|db)$", file):
                filename = os.path.join(root, file)
                if not os.path.isfile(os.path.splitext(filename)[0] + ".srt"):
                    filelist.append(filename)
    return filelist

def get_files_with_subs(rootdir):
    filelist = []
    for root, subfolders, files in os.walk(rootdir):
        for file in files:
            if not re.search("\.(srt|sub|db)$", file):
                filename = os.path.join(root, file)
                if os.path.isfile(os.path.splitext(filename)[0] + ".srt"):
                    filelist.append(filename)
    return filelist

#search for subtitles to download
def download_subtitles(rootdir, languages):
    filelist = get_files_without_subs(rootdir)
    for file in filelist:
        if os.path.isfile(file):
            for language in languages:
                result = download(language, get_hash(file), file)
                if result == 200:
                    print "download subtitle", file
                    break
                elif result == 404:
                    print language, "subtitle not found", file
                time.sleep(random.uniform(1,5))

#search for subtitles to upload
def upload_subtitles(rootdir):
    filelist = get_files_with_subs(rootdir)
    for file in filelist:
        if os.path.isfile(file):
            if file in uploaded:
                continue
            hash = get_hash(file)
            result = upload(hash, file)
            if result == 201:
                uploaded[file] = result
                print "uploaded subtitle", file
            elif result == 403:
                uploaded[file] = result
                print "subtitle already exists", file
            elif result == 415:
                uploaded[file] = result
                print "unsupported media type or the file is bigger than 200k"
            else:
                print "---------------------------------"
                print "error code", result
                print "hash", get_hash(file)
                print "subtitle not uploaded", file
                print "---------------------------------"
            time.sleep(random.uniform(1,10))

if __name__ == '__main__':
    try:
        hashes_file = open('pyrrot-uploaded.prt', 'rb')
        uploaded = cPickle.load(hashes_file)
        hashes_file.close()
    except IOError:
        uploaded = {}
        print "hash file does not exist yet"
    for folder in DIRECTORIES:
        download_subtitles(folder, LANGUAGES)
        upload_subtitles(folder)

    with open('pyrrot-uploaded.prt', 'wb') as hashes_file:
        cPickle.dump(uploaded, hashes_file)
    print "done"
