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

movie_exts = ['.avi', '.mkv', '.mp4', '.mov', '.mpg', '.wmv']
subs_exts = ['.srt', '.sub']

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

def get_movie_files(rootdir, with_subs=False):
    filelist = []
    for root, subfolders, files in os.walk(rootdir):
        for file in files:
            name, ext = os.path.splitext(file)
            if ext in movie_exts:
                if with_subs == has_subs(root, name):
                    filelist.append(os.path.join(root, file))
    return filelist

def has_subs(root, name):
    for ext in subs_exts:
        filename = os.path.join(root, name + ext)
        if os.path.isfile(filename):
            return True
    return False

#search for subtitles to download
def download_subtitles(rootdir, languages):
    filelist = get_movie_files(rootdir, with_subs=False)
    for file in filelist:
        if os.path.isfile(file):
            for language in languages:
                result = download(language, get_hash(file), file)
                if result == 200:
                    uploaded[file] = result
                    print "download subtitle", file
                    break
                elif result == 404:
                    print language, "subtitle not found", file
                time.sleep(random.uniform(1,5))

#search for subtitles to upload
def upload_subtitles(rootdir):
    filelist = get_movie_files(rootdir, with_subs=True)
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

def parse_options():
    global DIRECTORIES, base_url
    def parse_list(option, opt, value, parser):
        setattr(parser.values, option.dest, value.split(','))
    from optparse import OptionParser
    parser = OptionParser()
    parser.add_option('-d', '--dirs', type='string', action='callback', callback=parse_list, help='Folders to scan for movies: DIR1[,DIR2]')
    parser.add_option('-j', '--host', help='SubDB HOST in http://[HOST]:[PORT]/subdb?query')
    parser.add_option('-p', '--port', help='SubDB PORT in http://[HOST]:[PORT]/subdb?query')
    parser.add_option('-u', '--url', help='SubDB URL [URL]?query. Overrides --host and --port')
    (options, args) = parser.parse_args()
    if options.url:
        base_url = options.url + '?{0}'
    elif options.host:
        netloc = options.host
        if options.port:
            netloc += ':' + options.port
        base_url = list(urllib2.urlparse.urlsplit(base_url))
        base_url[1] = netloc
        base_url = urllib2.urlparse.urlunsplit(base_url)
    if options.dirs:
        DIRECTORIES = options.dirs

if __name__ == '__main__':
    parse_options()
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
