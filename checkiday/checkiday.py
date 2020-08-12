"""
Post daily event on checkiday.com to a subreddit(r/WhatToCelebrateToday)
"""

import random
import time

import requests
import praw
import bs4

class CheckIDay():
    url = "https://www.checkiday.com/"

    def __init__(self):
        self._post_text = ""    # Content to post to reddit
        self._post_title = ""   # Title of post
        self._post_text_from_sidebar = ""   # Will be merged with self._post_text

    def get_url(self):
        r = requests.get(CheckIDay.url)
        soup = bs4.BeautifulSoup(r.text, features="html.parser")
        holidays_section = soup.select(".holiday .mdl-card__media") # Direct link to individual holiday
        for key, value in enumerate(holidays_section):
            if "timeanddate.com" not in value.get("href"):  # Check against event articles that aren't hosted on checkiday.com(like timeanddate.com)
                req = requests.get(value.get("href"))
                sub_soup = bs4.BeautifulSoup(req.text, features="html.parser")
                post_content_without_p = sub_soup.select_one(".mdl-cell--8-col") # To navigate elements one by one(each tags)
                self._post_title = sub_soup.select_one(".card-image__filename").getText().replace("\n", "").replace("   ", "")
                self._post_text += self._post_title + "\n"
                side_bar_contents = sub_soup.select_one(".mdl-cell--8-col-tablet .mdl-card__supporting-text")
                self.get_sidebar_contents(side_bar_contents)
                for element in post_content_without_p.next_elements:
                    if element.name == "p" or element.name == "h2":
                        if element.name == "h2" and element.getText() == "Something Wrong or Missing?":  # We've reached where to stop gather articles for the page
                            break
                        else:
                            if element.name == "h2" and element.getText() == "How to Observe":
                                self._post_text += "# How to Celebrate \n" # Replace the word 'How to Observe' with 'How to Celebrate'
                                continue
                            self._post_text += self.format_paragraphs(element, "p")
                            #print(element.encode('utf-8'))
                self._post_text += "\n"
                self._post_text += "# [Other Events Your Might Like](https://www.reddit.com/r/WhatToCelebrateToday/?f=flair_name%3A%22Event%20of%20the%20day%20%22)"
                self._post_text = self._post_text_from_sidebar + self._post_text # Join both
                self.post_to_reddit()
                #print(self._post_title)
                #print(self._post_text)
                # Reset
                self._post_title = ""
                self._post_text_from_sidebar = ""
                self._post_text = ""
                time.sleep(1800)    # Wait 30 min before posting another

    def get_sidebar_contents(self, node):
        """
        Extract contents(text) from page side bar

        node: object - beautiful soup elements
        """
        dates_index = -1    #   To tell the position on "Dates" text
        temp = ""
        keep_headers =[]
        keep_bullets = []
        head_two = node.find_all("h2")
        ul = node.find_all("ul")
        for key, tags in enumerate(head_two):
            if tags.getText() == "Dates":
                dates_index = key
            if tags.getText() != "Dates":    # Dates - since we are not interested in dates header and its items
                keep_headers.append(f"# {tags.getText()}")
        for key, tags in enumerate(ul):
            if key != dates_index:    # Dates - since we are not interested in dates header and its items
                li = tags.find_all("li")
                tem = []
                for sub_tag in li:
                    h3 = sub_tag.find("h3")
                    tem.append(self.format_paragraphs(h3, "h3"))
                keep_bullets.append(tem)
        for i in range(len(keep_headers)):
            self._post_text_from_sidebar += keep_headers[i] + "\n"
            for j in range(len(keep_bullets[i])):
                self._post_text_from_sidebar += f"* {keep_bullets[i][j]}\n"
            self._post_text_from_sidebar += "\n"

        
    
    def format_paragraphs(self, paragraph, tag):
        """
        format paragraph(p) to match reddit format by fromatting <a> tags 
        e.g <a href="https://en.wikipedia.org/wiki/Tartan">tartan</a> becomes [tartan](https://en.wikipedia.org/wiki/Tartan)

        paragrapg: str - paragraph of text
        tag: str - the tag to remove

        return: str - new formatted string
        """
        innertext_of_link = []
        try:    # no link inside the paragraph
            links = paragraph.select("a")
            for key, value in enumerate(links):
                innertext_of_link.append(value.getText())
            if tag == "p":
                trim_p_from_text = str(paragraph).replace("<p>", "").replace("</p>", "")
            else:
                trim_p_from_text = str(paragraph).replace("<h3>", "").replace("</h3>", "")
            forward_pointer = 1
            current_pointer = 0
            total_text = len(trim_p_from_text)

            all_links = []  # links extracted and formatted
            while forward_pointer != total_text - 1:
                tem_text = ""
                if trim_p_from_text[current_pointer] == "<" and trim_p_from_text[forward_pointer] == "a":   # Start extracting link
                    tem_current_pointer = forward_pointer + 8   #  To go further to link from <a href="
                    while True: # Continue grabbing characters of link until reached " character
                        if trim_p_from_text[tem_current_pointer] == '"':
                            tem_text += ""
                            all_links.append(tem_text)
                            break
                        tem_text += trim_p_from_text[tem_current_pointer]
                        tem_current_pointer += 1
                current_pointer += 1
                forward_pointer += 1

            dynamic_names = {}  # Store each level of replacement from node string

            for i in range(len(all_links)):
                """
                NOTE: This uses more space

                Each replacement will be stored so that next replacement will be done on the previous one because
                each changes to the string needs to be stored.
                """
                txt = f'<a href="{all_links[i]}">{innertext_of_link[i]}</a>'
                txt_em = f'<a href="{all_links[i]}"><em>{innertext_of_link[i]}</em></a>'    # If their is <em> tag in
                if i == 0:
                    if txt in trim_p_from_text:
                        dynamic_names[i] = trim_p_from_text.replace(txt, f"[{innertext_of_link[i]}]({all_links[i]})")
                    elif txt_em in trim_p_from_text:
                        dynamic_names[i] = trim_p_from_text.replace(txt_em, f"[{innertext_of_link[i]}]({all_links[i]})")
                else:
                    if txt in trim_p_from_text:
                        dynamic_names[i] = dynamic_names[i - 1].replace(txt, f"[{innertext_of_link[i]}]({all_links[i]})")
                    elif txt_em in trim_p_from_text:
                        dynamic_names[i] = dynamic_names[i - 1].replace(txt_em, f"[{innertext_of_link[i]}]({all_links[i]})")
            return dynamic_names[len(dynamic_names) - 1] + "\n"
        except: # No link inide tage or if it's an <h2> tag or <h3> tag
            return paragraph.getText() + "\n"

    def post_to_reddit(self):
        """
        Post content to reddit
        """
        mod_user = praw.Reddit("bot1") # Will approve new post
        user_index = [0, 1]
        praw_index = random.choice(user_index)
        reddit = praw.Reddit(f"bot{praw_index}") # Select a reddit account to use for posting randomly
        flair_id = "d472d224-de5c-11e9-8dac-0ec8e76b2c5a"
        submited = reddit.subreddit("WhatToCelebrateToday").submit(title=self._post_title, selftext=self._post_text, flair_id=flair_id, resubmit=False, send_replies=False)
        #Approve the post
        try:
            submission = mod_user.submission(id=submited.id)
            submission.mod.approve()            
        except:
            pass
        
        
def main():
    checkiday = CheckIDay()
    checkiday.get_url()

if __name__ == "__main__":
    main()
