#VERSION: 2.04
#AUTHORS: Christophe Dumez (chris@qbittorrent.org)
#CONTRIBUTORS: Diego de las Heras (ngosang@hotmail.es)

# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
#    * Redistributions of source code must retain the above copyright notice,
#      this list of conditions and the following disclaimer.
#    * Redistributions in binary form must reproduce the above copyright
#      notice, this list of conditions and the following disclaimer in the
#      documentation and/or other materials provided with the distribution.
#    * Neither the name of the author nor the names of its contributors may be
#      used to endorse or promote products derived from this software without
#      specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
# ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE
# LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
# CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
# SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
# INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
# CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
# ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.

from html.parser import HTMLParser
#qBt
from novaprinter import prettyPrinter
from helpers import download_file, retrieve_url

class extratorrent(object):
    """ Search engine class """
    url = 'https://extratorrent.cc'
    name = 'ExtraTorrent'
    supported_categories = {'all'       : '0',
                            'movies'    : '4',
                            'tv'        : '8',
                            'music'     : '5',
                            'games'     : '3',
                            'anime'     : '1',
                            'software'  : '7',
                            'books'     : '2',
                            'pictures'  : '6'}

    def download_torrent(self, info):
        """ Downloader """
        print(download_file(info))

    class MyHtmlParseWithBlackJack(HTMLParser):
        """ Parser class """
        def __init__(self, list_searches, url):
            HTMLParser.__init__(self)
            self.url = url
            self.list_searches = list_searches
            self.current_item = None
            self.cur_item_name = None
            self.pending_size = False
            self.next_queries = True
            self.pending_next_queries = False
            self.next_queries_set = set()

        def handle_starttag(self, tag, attrs):
            if self.current_item:
                if tag == "a":
                    params = dict(attrs)
                    link = params['href']

                    if not link.startswith("/torrent"):
                        return

                    if link[8] == "/":
                        #description
                        self.current_item["desc_link"] = "".join((self.url, link))
                        #remove view at the beginning
                        self.current_item["name"] = params["title"][5:-8].replace("&amp;", "&")
                        self.pending_size = True
                    elif link[8] == "_":
                        #download link
                        link = link.replace("torrent_", "", 1)
                        self.current_item["link"] = "".join((self.url, link))

                elif tag == "td":
                    if self.pending_size:
                        self.cur_item_name = "size"
                        self.current_item["size"] = ""
                        self.pending_size = False

                    for attr in attrs:
                        if attr[0] == "class":
                            if attr[1][0] == "s":
                                self.cur_item_name = "seeds"
                                self.current_item["seeds"] = ""
                            elif attr[1][0] == "l":
                                self.cur_item_name = "leech"
                                self.current_item["leech"] = ""
                        break


            elif tag == "tr":
                for attr in attrs:
                    if attr[0] == "class" and attr[1].startswith("tl"):
                        self.current_item = dict()
                        self.current_item["engine_url"] = self.url
                        break

            elif self.pending_next_queries:
                if tag == "a":
                    params = dict(attrs)
                    if params["title"] in self.next_queries_set:
                        return
                    self.list_searches.append(params['href'])
                    self.next_queries_set.add(params["title"])
                    if params["title"] == "10":
                        self.pending_next_queries = False
                else:
                    self.pending_next_queries = False

            elif self.next_queries:
                if tag == "b" and ("class", "pager_no_link") in attrs:
                    self.next_queries = False
                    self.pending_next_queries = True

        def handle_data(self, data):
            if self.cur_item_name:
                temp = self.current_item[self.cur_item_name]
                self.current_item[self.cur_item_name] = " ".join((temp, data))
                #Due to utf-8 we need to handle data two times if there is space
                if not self.cur_item_name == "size":
                    self.cur_item_name = None

        def handle_endtag(self, tag):
            if self.current_item:
                if tag == "tr":
                    prettyPrinter(self.current_item)
                    self.current_item = None

    def search(self, what, cat="all"):
        """ Performs search """
        query = "".join((self.url, "/advanced_search/?with=", what, "&s_cat=", self.supported_categories[cat]))

        response = retrieve_url(query)

        list_searches = []
        parser = self.MyHtmlParseWithBlackJack(list_searches, self.url)
        parser.feed(response)
        parser.close()

        for search_query in list_searches:
            response = retrieve_url(self.url + search_query)
            parser.feed(response)
            parser.close()

        return
