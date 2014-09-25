# coding: iso-8859-15 

import re
import urllib2
import socket
import HTMLParser

from datetime import datetime

URL_REGEX = re.compile(r"(?:^|\s)((?:https?://)?(?:[a-z0-9.\-]+[.][a-z]{2,4}/?)(?:[^\s()<>]*|\((?:[^\s()<>]+|(?:\([^\s()<>]+\)))*\))+(?:\((?:[^\s()<>]+|(?:\([^\s()<>]+\)))*\)|[^\s`!()\[\]{};:\'\".,<>?]))", flags=re.IGNORECASE|re.DOTALL)
TITLE_REGEX = re.compile(r'<title(\s+.*?)?>(.*?)</title>', flags=re.IGNORECASE|re.DOTALL)

class URLsPlugin(object):
    last_url = None
    last_url_at = None

    def get_title(self, cardinal, user, channel, msg):
        # Find every URL within the message
        urls = re.findall(URL_REGEX, msg)

        # Loop through the URLs, and make them valid
        for url in urls:
            if url[:7].lower() != "http://" and url[:8].lower() != "https://":
                url = "http://" + url

            if (url == self.last_url and self.last_url_at and
                (datetime.now() - self.last_url_at).seconds < cardinal.config['urls'].LOOKUP_COOLOFF):
                return

            self.last_url = url
            self.last_url_at = datetime.now()

            # Attempt to load the page, timing out after a default of ten seconds
            try:
                try:
                    timeout = cardinal.config['urls'].TIMEOUT
                except:
                    timeout = 10
                    print "Warning: TIMEOUT not set in urls/config.py."

                o = urllib2.build_opener()
                o.addheaders = [('User-agent', 'Mozilla/5.0 (Windows NT 6.2; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/32.0.1667.0 Safari/537.36')]
                f = o.open(url, timeout=timeout)
            except urllib2.URLError, e:
                print "Unable to load URL (%s): %s" % (url, e.reason)
                return
            except socket.timeout, e:
                print "Unable to load URL (%s): %s" % (url, e.reason)
                return

            # Attempt to find the title, giving up after a default of 512KB
            # (512 * 1024).
            try:
                read_bytes = cardinal.config['urls'].READ_BYTES
            except:
                read_bytes = 512 * 1024
                print "Warning: READ_BYTES not set in urls/config.py."
            
            content_type = f.info()['content-type']
            if not (('text/html' in content_type) or ('text/xhtml' in content_type)):
                save_url(cardinal.config['urls'].LINKS_FILE, url, user.group(1))
                return
            content = f.read(read_bytes)
            f.close()
            
            title = re.search(TITLE_REGEX, content)
            if title:
                if len(title.group(2).strip()) > 0:
                    title = re.sub('\s+', ' ', title.group(2)).strip()
                    
                    h = HTMLParser.HTMLParser()
                    title = str(h.unescape(title))

                    # Truncate long titles to the first 200 characters.
                    title_to_send = title[:200] if len(title) >= 200 else title
                    
                    cardinal.sendMsg(channel, "URL Found: %s" % title_to_send)
                    save_url(cardinal.config['urls'].LINKS_FILE, url, user.group(1), title_to_send)
                    continue

            save_url(cardinal.config['urls'].LINKS_FILE, url, user.group(1))

    get_title.regex = URL_REGEX

def setup():
    return URLsPlugin()

def save_url(url_file, url, user=None, title=None):
    f = open(url_file, 'a')

    line_to_write = "{} | {}".format(
            datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC"),
            url,
        )
    if title:
        line_to_write += " | {}".format(title)
    if user:
        line_to_write += " | Mentioned by: {}".format(user)

    f.write("{}\n".format(line_to_write))
    f.close()
