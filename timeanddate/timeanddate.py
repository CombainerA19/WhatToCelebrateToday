"""
Post daily event on timeanddate.com to a subreddit(r/WhatToCelebrateToday)
"""

import random

import requests
import praw
import bs4

class TimeAndDate():
    url = "https://www.timeanddate.com/on-this-day/"

    def __init__(self):
        self._post_text = ""
        self._post_title = ""

    def get_url(self):
        r = requests.get(TimeAndDate.url)
        soup = bs4.BeautifulSoup(r.text, features="html.parser")
        self._post_title = f"{soup.select_one('.bn-header__title').getText()}\n"
        head_titles_raw = soup.select(".otd-row")
        for key, value in enumerate(head_titles_raw):
            head_titles = value.select(".columns .otd-cat")
            self.extract_headings(head_titles)
            bulletin_text = value.select(".otd-row .columns ul li")
            self.extract_subheading_and_text(bulletin_text)
        self.post_to_reddit()


    def extract_headings(self, head_nodes):
        """
        Extract Event headings

        head_nodes: list - list of titles
        """
        for key, value in enumerate(head_nodes):
            self._post_text += f"#  {value.getText()}\n"

    def extract_subheading_and_text(self, sub_node):
        """
        Extract Bullet heading and sub heading

        sub_node: list - list of tags where to get text
        """
        for key, value in enumerate(sub_node):
            bulletin_head = value.select("li h3")
            sub_heading = value.select("li p")
            for i in range(len(bulletin_head)): # Both bulletin_head and sub_heading have same length
                self._post_text += f"* **{bulletin_head[i].getText()}** {sub_heading[i].getText()} \n"
        self._post_text += "\n\n"

    def post_to_reddit(self):
        """
        Post content to reddit
        """
        mod_user = praw.Reddit("bot1") # Will pin new post and unpin old post and also approve new post
        last_post_id = self.read_pinned_id()
        try:
            if len(last_post_id) != 0:  # Remove old pinned post
                submission = mod_user.submission(id=f'{last_post_id[0]}')
                submission.mod.sticky(state=False)  # Remove post as pinned
        except:
            pass
        user_index = [0, 1]
        praw_index = random.choice(user_index)
        reddit = praw.Reddit(f"bot{praw_index}") # Select a reddit account to use for posting randomly
        flair_id = "cd73016a-de5c-11e9-be2e-0ec36a59db5e"
        submited = reddit.subreddit("WhatToCelebrateToday").submit(title=self._post_title, selftext=self._post_text, flair_id=flair_id, resubmit=False, send_replies=False)
        #Approve the post
        try:
            submission = mod_user.submission(id=submited.id)
            submission.mod.approve()
            # Pin the new post
            submission = mod_user.submission(id=submited.id)
            submission.mod.sticky(bottom=False)
        except:
            pass
        # Save id of the new post for later unpinning
        self.write_pinned_id(submited.id)


    def read_pinned_id(self):
        """
        Read ID or last post(pinned)
        """
        with open("post_id.txt", "r") as file:
            f = file.readlines()
        return f

    def write_pinned_id(self, id):
        """
        Write ID of post(pinned)
        
        id: Submission(post) id
        """
        with open("post_id.txt", "w") as file:
            file.write(id)
        


def main():
    timeanddate = TimeAndDate()
    timeanddate.get_url()

if __name__ == "__main__":
    main()
