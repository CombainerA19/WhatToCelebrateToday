import datetime
import urllib3
import random
import time

from html.parser import HTMLParser
from html.entities import name2codepoint
from datetime import date

import praw
import requests
import bs4

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class MyHTMLParser(HTMLParser):
    """
    Reformat html element(text and link from wikipedia) to follow reddit pattern
    """
    def __init__(self):
        HTMLParser.__init__(self)
        self._data = ""
        self._all_data = []
        self._title = []    # Reddit post title(3 random text from list)
        self._href = ""
        self._start_tag_is_a = False

    def handle_starttag(self, tag, attrs):
        if tag == "a":
            self._start_tag_is_a = True
        #print("Start tag:", tag)
        for attr in attrs:
            if attr[0] == 'href':
                self._href = f"(https://en.wikipedia.org{attr[1]})"
            #print("     attr:", attr)

    def handle_endtag(self, tag):
        self._start_tag_is_a = False
        if tag == "li":
            self._all_data.append(self._data)
            self._data = ""
        #print("End tag  :", tag)

    def handle_data(self, data):
        if self._start_tag_is_a:
            data = data.replace("'", "--")
            self._data += "[" + data + "]" + self._href
        else:
            self._data += data
        #print("Data     :", data)

    def handle_comment(self, data):
        #print("Comment  :", data)
        pass

    def handle_entityref(self, name):
        c = chr(name2codepoint[name])
        #print("Named ent:", c)

    def handle_charref(self, name):
        if name.startswith('x'):
            c = chr(int(name[1:], 16))
        else:
            c = chr(int(name))
        #print("Num ent  :", c)

    def handle_decl(self, data):
        #print("Decl     :", data)
        pass

    def get_all_data(self):
        return self._all_data

    def generate_title_index(self):
        """
        3 Indices of where to pick title from randomly
        among the list
        """
        index = []
        data = []
        _len = len(self._all_data)
        for i in range(_len):
            data.append(i)
        while len(index) != 3:
            temp = random.choices(data)
            if temp not in index:
                index.append(temp[0])
        return index

try:
    parser = MyHTMLParser()

    today = date.today()
    date_for_title =  str(datetime.datetime(today.year, today.month, today.day).strftime('%B %d')) + ":"

    url = f"https://en.wikipedia.org/wiki/October_{today.day}"

    req = requests.get(url)

    content = f"**Events**\n\n"

    soup = bs4.BeautifulSoup(req.text, features="html.parser")
    event = soup.select("ul")[1].select("li")
    #parser.feed(str(event))
    #print(parser.get_data())
    for key, value in enumerate(event):
        # Break down HTML structure and extract data
        parser.feed(str(value))
    # print(parser.get_all_data())
    for _, value in enumerate(parser.get_all_data()):
        content += f"* {value}\n"
        if len(content) > 270:  # Praw only allow 300 max char
            break

    # print(content)
    title_index = parser.generate_title_index()

    title = date_for_title
    for i in title_index:
        title += soup.select("ul")[1].select("li")[i].getText() + ";"

    f_id = "cd73016a-de5c-11e9-be2e-0ec36a59db5e"
    reddit = praw.Reddit("bot1")
    #submited = reddit.subreddit("WhatToCelebrateToday").submit(title, selftext=content[:269], flair_id=f_id, resubmit=False, send_replies=False)
    reddit.subreddit("WhatToCelebrateToday").submit(title[:300], url=url, flair_id=f_id, resubmit=False, send_replies=False)
except Exception as e:
    print(e)
    time.sleep(6)