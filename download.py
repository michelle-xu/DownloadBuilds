# Created by Michelle xu at 2018-04-18
# This function is used to download builds with multiple threads.

from __future__ import division
from optparse import OptionParser
from bs4 import BeautifulSoup
import urllib2
import datetime,sys
import threading
import traceback

def downloader(url, username='test', password='test', num_thread = 20):
    try:
        # create password manager
        password_mgr = urllib2.HTTPPasswordMgrWithDefaultRealm()
        # add username and password
        password_mgr.add_password(None, url, username, password)
        # create new handler
        handler = urllib2.HTTPBasicAuthHandler(password_mgr)
        # create opener
        opener = urllib2.build_opener(handler)
        # using opener to get URL
        #opener.open(bigurl)
        # install opener
        urllib2.install_opener(opener)
        # build request
        request = urllib2.Request(url)
        # urllib2.urlopen to send request
        page = urllib2.urlopen(request)
        # get response data to get access RMS build location
        data = page.read()
        # get HTML element and get the latest build
        soup = BeautifulSoup(data, 'html.parser')

        # builds_href to get all builds
        builds_href = soup.select('a[href*="/"]')
        builds_href.pop(0)
        # builds is used to store build version
        builds = []
        # get all href that end with character '/'
        for build in builds_href:
            digital_build = build.string.strip('/')
            # check the build number is all digital, then add to builds
            if digital_build.isdigit():
                version = int(digital_build)
                builds.append(version)
        # Compare and get latest build
        latest_build = max(builds)
        url = url + str(latest_build) + '/'

        # get all files from latest build
        print ("Now latest build url is: %s" % url)
        request = urllib2.Request(url)
        page = urllib2.urlopen(request)
        data = page.read()
        soup = BeautifulSoup(data, 'html.parser')

        # get all installers from latest build version, it supports to download for different products.
        installers = soup.select('a[href*="."]')
        # remove href with 'parent directory' element, it is index 0
        installers.pop(0)
        print "Installer count is: %s" % (len(installers))
        for installer in installers:
            downloadThread(installer, url, num_thread)

    except (Exception,urllib2.HTTPError) as e:
        print 'Exception:\t', str(e)
        print 'traceback.format_exec():\n%s' % traceback.format_exc()
        raise e


# read with range size to reduce memory usage
def read_write_in_range(filePath, url, start, end):
    headers = {'Range': 'bytes=%d-%d' % (start, end)}
    try:
        request = urllib2.Request(url,headers=headers)
        page = urllib2.urlopen(request)

        with open(filePath, 'r+b') as f:
            f.seek(start)
            var = f.tell()
            f.write(page.read())
    except (IOError,urllib2.HTTPError) as e:
        print 'Exception:\t', Exception
        print 'traceback.format_exec():\n%s' % traceback.format_exc()
        raise e


# Using multiple threads
def mulithread(total_size, num_thread, filename, fileurl):
    # start multiple threads to write file
    # get parts with same size for each thread
    part = total_size // num_thread

    for i in range(num_thread):
        start = part * i
        # if last part, then end range is total size
        if i == num_thread - 1:
            end = total_size
        else:
            end = start + part
        # call read_write_in_range to download file
        thread = threading.Thread(target=read_write_in_range, args=(filename, fileurl, start, end))
        thread.setDaemon(True)
        thread.start()

    # waiting all threads finish and join all threads
    main_thread = threading.current_thread()
    for t in threading.enumerate():
        if t is main_thread:
            continue
        t.join()

# Access url then start to do download
def downloadThread(file, url, num_thread):
    try:
        filename = file.string
        fileurl = url + filename
        print ("The fileurl is: %s" % (fileurl))
        request = urllib2.Request(fileurl)
        page = urllib2.urlopen(request)

        # get file size
        total_size = int(dict(page.headers).get('content-length', 0))
        if total_size> 0 and total_size < 1024:
            print "[+] File: %s, Size: %dBytes" % (filename, total_size)
            num_thread = 1
        elif total_size > 1024 * 1024 * 1024:
            print "[+] File: %s, Size: %.1fGB" % (filename, total_size / 1024 / 1024 / 1024)
        elif total_size > 1024 * 1024:
            print "[+] File: %s, Size: %.1fMB" % (filename, total_size / 1024 / 1024)
        elif total_size > 1024:
            print "[+] File: %s, Size: %.1fKB" % (filename, total_size / 1024)
            num_thread = 1
        else:
            print "[+] File: %s, Size: None" % (filename)

        # create one file with same file size locally
        fp = open(filename, "wb")
        # fp.truncate(total_size)
        fp.close()

        # get start_time of one file before start to download
        start_time = datetime.datetime.now().replace(microsecond=0)
        # start multiple threads to write file
        mulithread(total_size, num_thread, filename, fileurl)
        # get end time for a file after complete
        end_time = datetime.datetime.now().replace(microsecond=0)
        print ("Time used: %s, complete download file %s successfully!\n" % (str(end_time - start_time), filename))
    except (IOError,urllib2.HTTPError) as e:
        print 'Exception:\t', Exception
        print 'traceback.format_exec():\n%s' % traceback.format_exc()
        raise e



if  __name__ == '__main__':
    usage = "usage: %prog [options] arg"
    parser = OptionParser()
    parser.add_option("-s", "--url", dest="url", help="need provide download url")
    parser.add_option("-u", "--user", dest="username", help="username to login server")
    parser.add_option("-w", "--password", dest="password", help="password for login user")
    # parser.add_option("-o", "--output", dest="filename", help="download file to save")
    # parser.add_option("-a", "--user-agent", dest="useragent", help="request user agent",
    #                   default='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 \
    #                   (KHTML, like Gecko) Chrome/64.0.3282.140 Safari/537.36')
    # parser.add_option("-r", "--referer", dest="referer", help="request referer")
    # parser.add_option("-c", "--cookie", dest="cookie", help="request cookie", default='_ga=GA1.2.725424807.1491454584;')
    (options, args) = parser.parse_args()
    if not options.url:
        print "Missing url"
        sys.exit()
    if options.username and options.password:
        print "Start to download with given username and password!"
        start_time = datetime.datetime.now().replace(microsecond=0)
        downloader(options.url, options.username, options.password)
        end_time = datetime.datetime.now().replace(microsecond=0)
        print ("Total Time used: %s" % (str(end_time - start_time)))
    else:
        print "Start to download with default login username and password!"
        start_time = datetime.datetime.now().replace(microsecond=0)
        downloader(options.url)
        end_time = datetime.datetime.now().replace(microsecond=0)
        print ("Total Time used: %s" % (str(end_time - start_time)))

    # if not options.filename:
    #     options.filename = options.url.split('/')[-1]
    # headers = {
    #     'User-Agent': options.useragent,
    #     'Referer': options.referer if options.referer else options.url,
    #     'Cookie': options.cookie
    # }
