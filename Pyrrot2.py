'''
Created on 02/04/2010

@author: Jr. Hames
'''

#edit the following options according to your needs
PYRROT_DIR = ""
DIRECTORIES = ["/path/to/your/video/files", "/path/to/your/video/files2"]
LANGUAGES = ["pt","en"]
HASHES_FILE = 'pyrrot-uploaded.prt'
LOG_FILE = 'pyrrot-log.txt'
MOVIE_EXTS = ['.avi', '.mkv', '.mp4', '.m4v', '.mov', '.mpg', '.wmv']
SUBS_EXTS = ['.srt', '.sub']
#end of configurations


import logging
import cPickle
import io
import hashlib
import os
import random
import re
import time
import urllib
import urllib2
import urllib2_file

base_url = 'http://api.thesubdb.com/?{0}'
user_agent = 'SubDB/1.0 (Pyrrot/0.1; http://github.com/jrhames/pyrrot-cli)'
logger = None
uploaded = {}
retry = 0

def get_hash(name):
    readsize = 64 * 1024
    with open(name, 'rb') as f:
        size = os.path.getsize(name)
        data = f.read(readsize)
        f.seek(-readsize, os.SEEK_END)
        data += f.read(readsize)
    return hashlib.md5(data).hexdigest()

def download(language, hash, filename):
    global retry
    params = {'action': 'download', 'language': language, 'hash': hash}
    url = base_url.format(urllib.urlencode(params))
    req = urllib2.Request(url)
    req.add_header('User-Agent', user_agent)
    try:
        response = urllib2.urlopen(req)
        ext = response.info()['Content-Disposition'].split(".")[1]
        file = os.path.splitext(filename)[0] + "." + ext
        with open(file, "wb") as fout:
            fout.write(response.read())
        retry = 0
        return 200
    except urllib2.HTTPError, e:
        retry = 0
        return e.code
    except urllib2.URLError as e:
        if retry < 1800:
            retry += 60
        else:
            return -1
        logger.debug("service did not respond, waiting %ds before retry" % retry)
        time.sleep(retry)
        download(language, hash, filename)

def upload(hash, filename):
    global retry
    for ext in SUBS_EXTS:
        file = os.path.splitext(filename)[0] + ext
        if os.path.isfile(file):
            fd_file = open(file, 'rb')
            fd = io.BytesIO()
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
                retry = 0
                return e.code
            except urllib2.URLError as e:
                if retry < 1800:
                    retry += 60
                else:
                    return -1
                logger.debug("service did not respond, waiting %ds before retry" % retry)
                time.sleep(retry)
                upload(hash, filename)

def get_movie_files(rootdir, with_subs=False):
    filelist = []
    for root, subfolders, files in os.walk(rootdir):
        for file in files:
            name, ext = os.path.splitext(file)
            if ext in MOVIE_EXTS:
                if with_subs == has_subs(root, name):
                    filelist.append(os.path.join(root, file))
    return filelist

def has_subs(root, name):
    for ext in SUBS_EXTS:
        filename = os.path.join(root, name + ext)
        if os.path.isfile(filename):
            return True
    return False

#search for subtitles to download
def download_subtitles(rootdir, languages):
    filelist = get_movie_files(rootdir, with_subs=False)
    for file in filelist:
        if os.path.isfile(file):
            result = download(','.join(languages), get_hash(file), file)
            if result == 200:
                uploaded[file] = result
                logger.info("download subtitle " + file)
            elif result == 404:
                logger.debug("subtitle not found " + file)
            save()
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
                logger.info("uploaded subtitle " + file)
            elif result == 403:
                uploaded[file] = result
                logger.debug("subtitle already exists " + file)
            elif result == 415:
                uploaded[file] = result
                logger.warning("unsupported media type or the file is bigger than 200k " + file)
            else:
                logger.error("cannot upload subtitle %s - result: %s" % (file, result))
            save()
            time.sleep(random.uniform(1,10))

def save():
    with open(HASHES_FILE, 'wb') as hashes_file:
        cPickle.dump(uploaded, hashes_file)

def parse_options():
    global DIRECTORIES, HASHES_FILE, LOG_FILE, base_url
    def parse_list(option, opt, value, parser):
        setattr(parser.values, option.dest, value.split(','))
    from optparse import OptionParser
    parser = OptionParser()
    parser.add_option('-a', '--hashes', help='File where to store database of uploaded hashes')
    parser.add_option('-b', '--base', type='string', help='Set the basedir (application directory) of Pyrrot')
    parser.add_option('-d', '--dirs', type='string', action='callback', callback=parse_list, help='Folders to scan for movies: DIR1[,DIR2]')
    parser.add_option('-l', '--log', help='File where to write logging output')
    parser.add_option('-j', '--host', help='SubDB HOST in http://[HOST]:[PORT]/subdb?query')
    parser.add_option('-p', '--port', help='SubDB PORT in http://[HOST]:[PORT]/subdb?query')
    parser.add_option('-u', '--url', help='SubDB URL [URL]?query. Overrides --host and --port')
    (options, args) = parser.parse_args()
    if options.base:
        PYRROT_DIR = options.base
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
    if options.hashes:
        HASHES_FILE = options.hashes
    if options.log:
        LOG_FILE = options.log.strip()

def load_hashes_db():
    global uploaded
    if not os.path.isfile(HASHES_FILE):
        logger.info("hash file does not exist yet")
        return
    try:
        with open(HASHES_FILE, 'rb') as hashes_file:
            uploaded = cPickle.load(hashes_file)
    except EOFError:
        logger.info("hash file corrupted, will create new one")

def init_logger():
    global logger
    format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    if not LOG_FILE:
        logging.basicConfig(format=format)
    else:
        logging.basicConfig(filename=LOG_FILE, format=format)
    logger = logging.getLogger("Pyrrot2")
    logger.setLevel(logging.INFO)


if __name__ == '__main__':
    parse_options()
    if PYRROT_DIR != "":
        os.chdir(PYRROT_DIR)
    init_logger()
    if LOG_FILE:
        print "running... see the log in", LOG_FILE
    load_hashes_db()
    for folder in DIRECTORIES:
        download_subtitles(folder, LANGUAGES)
        upload_subtitles(folder)
    save()
    logger.info("-------------------------------------------")
    print "done"
