from collections import defaultdict
from datetime import datetime
from bs4 import BeautifulSoup
import feedparser
import requests
import asyncio
import time
import json
import re

with open('config.json') as f: config = json.load(f)

async def main():

    class Webhook:
        def __init__(self, url, **kwargs):

            """
            Initialise a Webhook Embed Object
            """

            self.url = url
            self.msg = kwargs.get('msg')
            self.username = kwargs.get('username')
            self.avatar_url = kwargs.get('avatar_url')
            self.color = kwargs.get('color')
            self.title = kwargs.get('title')
            self.title_url = kwargs.get('title_url')
            self.author = kwargs.get('author')
            self.author_icon = kwargs.get('author_icon')
            self.author_url = kwargs.get('author_url')
            self.description = kwargs.get('description')
            self.fields = kwargs.get('fields', [])
            self.image = kwargs.get('image')
            self.thumbnail = kwargs.get('thumbnail')
            self.footer = kwargs.get('footer')
            self.footer_icon = kwargs.get('footer_icon')
            self.ts = kwargs.get('ts')

        def add_field(self, **kwargs):
            '''Adds a field to `self.fields`'''
            name = kwargs.get('name')
            value = kwargs.get('value')
            inline = kwargs.get('inline', True)

            field = {

                'name': name,
                'value': value,
                'inline': inline

            }

            self.fields.append(field)

        def set_description(self, description):
            self.description = description

        def set_author(self, **kwargs):
            self.author = kwargs.get('name')
            self.author_icon = kwargs.get('icon')
            self.author_url = kwargs.get('url')

        def set_title(self, **kwargs):
            self.title = kwargs.get('title')
            self.title_url = kwargs.get('url')

        def set_thumbnail(self, url):
            self.thumbnail = url

        def set_image(self, url):
            self.image = url

        def set_footer(self, **kwargs):
            self.footer = kwargs.get('text')
            self.footer_icon = kwargs.get('icon')
            ts = kwargs.get('ts')
            if ts:
                self.ts = str(datetime.utcfromtimestamp(time.time()))
            else:
                self.ts = str(datetime.utcfromtimestamp(ts))

        def del_field(self, index):
            self.fields.pop(index)

        @property
        def json(self, *arg):
            '''
            Formats the data into a payload
            '''

            data = {}

            data["embeds"] = []
            embed = defaultdict(dict)
            if self.username: data['username'] = self.username
            if self.avatar_url: data['avatar_url'] = self.avatar_url
            if self.msg: data["content"] = self.msg
            if self.author: embed["author"]["name"] = self.author
            if self.author_icon: embed["author"]["icon_url"] = self.author_icon
            if self.author_url: embed["author"]["url"] = self.author_url
            if self.color: embed["color"] = self.color
            if self.description: embed["description"] = self.description
            if self.title: embed["title"] = self.title
            if self.title_url: embed["url"] = self.title_url
            if self.image: embed["image"]['url'] = self.image
            if self.thumbnail: embed["thumbnail"]['url'] = self.thumbnail
            if self.footer: embed["footer"]['text'] = self.footer
            if self.footer_icon: embed['footer']['icon_url'] = self.footer_icon
            if self.ts: embed["timestamp"] = self.ts

            if self.fields:
                embed["fields"] = []
                for field in self.fields:
                    f = {}
                    f["name"] = field['name']
                    f["value"] = field['value']
                    f["inline"] = field['inline']
                    embed["fields"].append(f)

            data["embeds"].append(dict(embed))

            empty = all(not d for d in data["embeds"])

            if empty and 'content' not in data:
                print('You cant post an empty payload.')
            if empty: data['embeds'] = []

            return json.dumps(data, indent=4)

        def post(self):
            """
            Send the JSON formated object to the specified `self.url`.
            """

            headers = {'Content-Type': 'application/json'}

            result = requests.post(self.url, data=self.json, headers=headers)

    def escape(text: str):
        text = text.replace("@everyone", "@\u200beveryone")
        text = text.replace("@here", "@\u200bhere")
        text = (text.replace("`", "\\`")
                .replace("*", "\\*")
                .replace("_", "\\_")
                .replace("~", "\\~"))
        return text

    ID = ''
    comments = 0
    while True:
        try:
            d = feedparser.parse('https://hypixel.net/forums/-/index.rss')
            entry = d['entries'][0]
            try: replies = int(d['entries'][0]['slash_comments'])
            except: replies = 0
            threadID = entry['id']
            r = requests.get(f"{threadID}page-99999")
            soup = BeautifulSoup(r.content, 'lxml')
            found = soup.findAll("li", {"class": re.compile("sectionMain message.*")})[-1]
            postID=found.get('id')
            if ID != threadID and replies != comments:
                avatar = f"https://hypixel.net/{found.find('img').get('src')}".split('?')[0]
                username = found.find('img').get('alt')
                text = found.find("div", {"class": "messageContent"})
                try: text.find('div', {"class": "bbCodeBlock bbCodeQuote"}).decompose()
                except: pass
                try: text.find('div', {"class": "attachedFiles"}).decompose()
                except: pass
                text = escape(text.text.strip())
                if any(x in text for x in config["words"]):
                    await asyncio.sleep(2)
                    continue
                wh = Webhook(url=config['webhook'],
                             username='Hypixel RSS', color=10181046)
                wh.description = f"[{entry['title']}]({entry['links'][0]['href']}page-9999#{postID})\n\n{text}"
                wh.set_author(name=username, icon=avatar)
                wh.set_footer(text=f"Thread by {entry['authors'][0]['name']}", ts=datetime.now().strptime(entry['published'], '%a, %d %b %Y %H:%M:%S %z'))
                wh.post()
                ID = threadID
                comments = replies
            await asyncio.sleep(4)
        except Exception as error:
            print('\n'.join(__import__('traceback').format_exception(type(error), error, error.__traceback__)))
            await asyncio.sleep(10)

if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.create_task(main())
    loop.run_forever()