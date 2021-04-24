import requests
from bs4 import BeautifulSoup

from apps.simulators.models import Sentence


class SentenceCrawler:

    def __init__(self):
        page = requests.get(
            'https://setare.com/fa/news/32447/%D9%85%D8%B9%D8%B1%D9%88%D9%81%E2%80%8C-%D8%AA%D8%B1%DB%8C%D9%86-%D8%AC%D9%85%D9%84%D8%A7%D8%AA-%D8%A7%D9%86%DA%AF%DB%8C%D8%B2%D8%B4%DB%8C-%DB%B9%DB%B1-%D8%AC%D9%85%D9%84%D9%87-%D9%85%D8%B9%D8%B1%D9%88%D9%81-%D8%AF%D8%B1-%D8%AF%D9%86%DB%8C%D8%A7-%D8%A8%D8%B1%D8%A7%DB%8C-%D8%AD%D9%81%D8%B8-%D8%A7%D9%86%DA%AF%DB%8C%D8%B2%D9%87/')
        self.soup = BeautifulSoup(page.text, "html.parser")

    def collect_sentences(self):
        to_be_inserted = []
        main_div_all_p = self.soup.find(class_='main-side single clearfix').find_all('p')
        for p in main_div_all_p:
            text = p.get_text().strip()
            if '✰★' in text or text == '':
                continue
            to_be_inserted.append(Sentence(sentence=text))
        Sentence.objects.bulk_create(to_be_inserted)
