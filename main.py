from datetime import datetime

import bs4
import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns
from selenium import webdriver
from selenium.webdriver.common.by import By
import time
from tqdm import tqdm

class ClimateScraper:
    def __init__(self):
        self.base_url = "https://klimaraadet.dk"
        self.url = "https://klimaraadet.dk/da/udforsk-vores-virkemiddelkatalog"
        self.links = []
        self.setup()

        self.num_pages = len(self.soup.find('ul', class_='pager__items js-pager__items').find_all('li')) - 2 # -2 because of the "previous" and "next" buttons
        self.data = {}
        self.df = pd.DataFrame()

        self.cvs_file_path = f'climate_data_{datetime.now().strftime("%Y-%m-%d")}.csv'

        self.run()

    def setup(self):
        self.driver = webdriver.Chrome()
        self.driver.get(self.url)
        self.update_soup()

    def update_soup(self):
        time.sleep(1) # Allow the page to load
        self.soup = bs4.BeautifulSoup(self.driver.page_source, 'html.parser')

    def read_links_from_table(self):
        table = self.soup.find_all('td', class_='views-field views-field-rendered-entity')
        for td in table:
            a = td.find('a')
            if a:
                self.links.append(a['href'])
        
    def next_page(self):
        next_page = self.driver.find_element(By.XPATH, "//*[contains(@class, 'pager__item pager__item--next')]")
        next_page.click()
        self.update_soup()

    def read_links_from_pages(self):
        for _ in tqdm(range(self.num_pages), desc='Reading links from pages', total=self.num_pages):
            self.read_links_from_table()
            self.next_page()

    def read_data_from_subpage(self):
        title = self.soup.find('h1').text.strip()
        sector = self.soup.find('div', class_='sector-element--name').text.strip()
        year = self.soup.find('div', class_='field field--name-field-year field--type-yearonly field--label-above').find('div', class_='field__item').text
        status = self.soup.find('div', class_='field field--name-field-status field--type-entity-reference field--label-above').find('div', class_='field__item').text
        adopted = self.soup.find('div', class_='field field--name-field-adopted field--type-entity-reference field--label-above').find('div', class_='field__item').text
        tags = [el.text for el in self.soup.find('div', class_='field field--name-field-tags field--type-entity-reference field--label-above').find_all('div', class_='field__item')]
        impact = self.soup.find('div', class_='field field--name-field-impact field--type-entity-reference field--label-above')
        if impact: impact = impact.find('div', class_='field__item').text
        datetime = self.soup.find('div', class_='field field--name-field-latest-status-update field--type-datetime field--label-above').find('div', class_='field__item').find('time').text
        return title, sector, year, status, adopted, tags, impact, datetime

    def add_data(self, index, title, sector, year, status, adopted, tags, impact, datetime, link):
        data = {
            'title': title,
            'sector': sector,
            'year': year,
            'status': status,
            'adopted': adopted,
            'tags': tags,
            'impact': impact,
            'datetime': datetime,
            'link': link
        }
        self.data[index] = data

    def save_data(self):
        self.df = pd.DataFrame.from_dict(self.data, orient='index')
        print(self.df)
        self.df.to_csv(self.cvs_file_path, index=False)
        print(f'Data saved to {self.cvs_file_path}')

    def visit_links(self):
        for i, link in tqdm(enumerate(self.links), desc='Visiting links', total=len(self.links)):
            full_link = self.base_url + link
            self.driver.get(full_link)
            self.update_soup()
            title, sector, year, status, adopted, tags, impact, datetime = self.read_data_from_subpage()
            print(title, sector, year, status, adopted, tags, impact, datetime)
            self.add_data(i, title, sector, year, status, adopted, tags, impact, datetime, full_link)

    def run(self):
        self.read_links_from_pages()
        self.visit_links()
        self.save_data()

class ClimateAnalyser:
    def __init__(self, csv_file_path):
        self.cvs_file_path = csv_file_path
        self.df = pd.read_csv(self.cvs_file_path)

    def show_adoption_piechart(self, save=False):
        adopted = self.df['adopted'].value_counts()
        print(adopted)

        # Create a pie chart
        plt.figure(figsize=(9, 6), dpi=300, facecolor='#eee')
        sns.set_style('whitegrid')
        sns.set_context('talk')
        plt.title('Følger regeringen anbefalingerne fra Klimarådet?')
        plt.pie(adopted, labels=adopted.index, autopct='%1.1f%%', colors=['#dd8452', '#c44e52', '#55a868'], startangle=90+10/69*360)

        if save:
            plt.savefig('adoption_piechart.png')
        plt.show()

if __name__ == '__main__':
    cs = ClimateScraper()
    ca = ClimateAnalyser('climate_data_2024-05-06.csv')
    ca.show_adoption_piechart(save=True)

