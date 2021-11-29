# encoding: utf-8

import re
from contextlib import closing
from urllib.parse import urljoin
from urllib.request import urlopen

from bs4 import BeautifulSoup


class OpenGraph:
    scrape = False

    def __init__(
        self,
        url="http://example.com",
        html=None,
        scrape=False,
        required_attrs=set(("title", "type", "image", "url")),
        **kwargs,
    ):
        # If scrape == True, then will try to fetch missing attribtues
        # from the page's body
        self.scrape = scrape
        self.url = url
        self.items = {}
        self.required_attrs = set(required_attrs)

        if not html:
            with closing(urlopen(url, **kwargs)) as raw:
                html = raw.read()

        self.parser(html)

    def absolute(self, url):
        return urljoin(self.url, url)

    def parser(self, html):
        if not isinstance(html, BeautifulSoup):
            doc = BeautifulSoup(html, features="html.parser")
        else:
            doc = html
        ogs = doc.html.head.findAll(property=re.compile(r"^og"))
        for og in ogs:
            if og.has_attr("content"):
                self.items[og["property"][3:]] = og["content"]

        # Couldn't fetch all attrs from og tags, try scraping body
        if self.scrape:
            remaining_keys = self.required_attrs - set(self.items.keys())
            for key in remaining_keys:
                self.items[key] = getattr(self, "scrape_{key}".format(key=key))(doc)

        image = self.items.get("image", False)
        if image:
            self.items["image"] = self.absolute(self.items["image"])

    def is_valid(self):
        return self.required_attrs <= set(self.items.keys())

    def to_html(self):
        if not self.is_valid():
            return '<meta property="og:error" content="og metadata is not valid" />'

        meta = ""
        for key, value in self.items.items():
            meta += '\n<meta property="og:%s" content="%s" />' % (key, value)
        meta += "\n"

        return meta

    def scrape_image(self, doc):
        images = [dict(img.attrs)["src"] for img in doc.html.body.findAll("img")]

        if images:
            return images[0]

        return ""

    def scrape_title(self, doc):
        return doc.html.head.title.text

    def scrape_type(self, doc):
        return "other"

    def scrape_url(self, doc):
        return self.url

    def scrape_description(self, doc):
        ogs = doc.html.head.findAll(
            name="meta",
            attrs={"name": ("description", "DC.description", "eprints.abstract")},
        )
        for og in ogs:
            content = og.get("content", False)
            if content:
                return content
        else:
            heading = doc.html.find(re.compile("h[1-6]"))
            if heading:
                return heading.text
            else:
                return doc.html.find("p").text
