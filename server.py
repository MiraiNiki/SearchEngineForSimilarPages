#!/bin/env python
# -*- coding: utf-8 -*-
from __future__ import print_function
import os
import tornado.ioloop
import tornado.web
from bs4 import BeautifulSoup
import requests
from gensim.models import word2vec
from urllib.parse import urljoin
import MeCab
import urllib

class MainHandler(tornado.web.RequestHandler):
    def get(self):
        original_url = ""
        self.render("index.html", original_url=original_url)

class GetURLHandler(tornado.web.RequestHandler):
    def get(self):
        original_url = self.get_argument("original_url")
        # original_url works if it includes "http://~"
        if "https://ja.wikipedia.org/wiki/" not in original_url:
            original_url = urljoin("https://ja.wikipedia.org/wiki/", original_url)
        related_urls = getPages(original_url)

        # Related_url cannot be found
        if len(related_urls) == 0:
            related_urls = {"見つかりませんでした😵"}

        self.render("index.html", original_url=original_url, related_urls=related_urls)

# Get candidate page by crawling
def getCandidatePages(original_url, title):
    soup = BeautifulSoup(requests.get(original_url).text, 'lxml')
    pages = {}
    mecab = MeCab.Tagger("-Owakati")
    title = mecab.parse(title).split(' ')[0]
    print("original url ////")
    print(title)
    for a in soup.find_all('a'):
        if len(pages) < 20:
            url_str = a.get('href')
            url = urljoin(original_url, url_str)
            url = urllib.parse.unquote(url)
            pageTitle = (url.rsplit('/',1))[1].replace("_", " ")
            if title != pageTitle and'#' not in pageTitle and '?' not in pageTitle and ':' not in pageTitle \
                    and '(' not in pageTitle and len(pageTitle) > 1 and 'ja' in url:
                pages[pageTitle] = url
    return pages

# Get final result
def getResult(sim, candidatePages):
    result = {}
    while len(result) < 5 or len(sim) == 0:
        max_k = max(sim, key=sim.get)
        result[max_k] = candidatePages[max_k]
        del sim[max_k]
    return result

# calclate similarity between original page's title and crawled page's title
def calcSimilarity(candidatePages, model, title):
    mecab = MeCab.Tagger("-Owakati")
    sim = {}
    for page in candidatePages:
        pageKey = mecab.parse(page).split(' ')[0]
        if title in model.wv and pageKey in model.wv:
            sim[page] = model.wv.similarity(title, pageKey)
            print("sim")
            print(sim[page])
    print(sim)
    return sim

# Get similar pages
def getPages(original_url):
    title = (original_url.rsplit('/',1))[1].replace("_", " ")
    print(title)

    # リンクを辿り、候補ページを探索する
    # Search similar page by crawling
    candidatePages = getCandidatePages(original_url, title)
    print(candidatePages)

    # word2vecでtitleの関連度が高いものを出力
    # Calculate similarity using word2vec
    model = word2vec.Word2Vec.load("wiki.model")
    sim = calcSimilarity(candidatePages, model, title)
    if len(sim) != 0:
        result = getResult(sim, candidatePages)
        return result.values()
    else:
        return {}

application = tornado.web.Application([
        (r'/', MainHandler),
        (r'/urls', GetURLHandler),
    ],
    template_path=os.path.join(os.getcwd(), "View"),
    static_path=os.path.join(os.getcwd(), "static")
)

if __name__ == "__main__":
    application.listen(8888)
    print("Server is up ...")
    tornado.ioloop.IOLoop.instance().start()
