#-*- coding:utf-8 -*-

from selenium import webdriver
from bs4 import BeautifulSoup as bs
import re
import urllib.parse
# import os
# from multiprocessing import Pool

class Crawler:

	# It will be added more.
	target_list = ['aladin', 'kyobo']

	# Initialize options, driver and pool
	def __init__(self):
		# driver configurations
		self.options = webdriver.ChromeOptions()
		self.options.add_argument('headless')
		self.options.add_argument('window-size=1920x1080')
		self.options.add_argument("disable-gpu")	

		# self.driver = webdriver.Chrome('/Users/sewon/Downloads/chromedriver', chrome_options=self.options)
		# self.pool = Pool(processes=8)
		# multi processing is implemented later.

	# open the chrome driver
	def openDriver(self):
		self.driver = webdriver.Chrome('/usr/bin/chromedriver', chrome_options=self.options)

	# close the chrome driver
	def closeDriver(self):
		self.driver.quit()

	# extract isbn from url using regular expression.
	def getIsbn(self, url):
		isbn_match = re.search(r'barcode=([0-9X]{10,13})', url)
		if not isbn_match:
			return None
		return isbn_match.group(1)

	# parse the title to format of kyobo
	def parseTitle(self, title):
		return '%20'.join(title.split())

	# parse the price string to number format
	def parsePrice(self, price):
		return ''.join(price.split('원')[0].split(','))

	# get candidate list using book's title.
	def getCandidateList(self, title):
		# get the kyobo site and search the book using title.

		encodedTitle = urllib.parse.quote(title)
		parsedTitle = self.parseTitle(title)

		# if parsedTitle is equal to encodedTitle,
		# the title is english, otherwise korean.
		if parsedTitle == encodedTitle:
			search_url = 'http://www.kyobobook.co.kr/search/SearchCommonMain.jsp?vPstrCategory=TOT&vPstrKeyWord=' + parsedTitle + '&vPplace=top'
			self.driver.get(search_url)
		else:
			search_url = 'http://www.kyobobook.co.kr/search/SearchCommonMain.jsp'
			self.driver.get(search_url)
			self.driver.find_element_by_name('searchKeyword').send_keys(title)
			self.driver.find_element_by_xpath('//*[@id="searchTop"]/div[1]/div/input').click()

		# get the page's html.
		html = self.driver.page_source

		# get the beautiful soup object and parse the html
		soup = bs(html, 'html.parser')

		# get the soup objects that contain the data
		images = soup.select('#container > div > form > table > tbody > tr > td.image > div.cover > a > img')
		isbns = soup.select('#container > div > form > table > tbody > tr > td.detail > div.title > a')
		titles = soup.select('#container > div > form > table > tbody > tr > td.detail > div.title > a > strong')
		infos = soup.select('#container > div > form > table > tbody > tr > td.detail > div.author')
		prices = soup.select('#container > div > form > table > tbody > tr > td.price > div.org_price > del')

		# make dictionary list
		data = []
		for index in range(len(isbns)):
			# empty dictionary
			datum = {}

			# get the image link
			if images[index]['src'] == 'http://image.kyobobook.co.kr/newimages/apps/b2c/product/Noimage_l.gif':
				datum['imageLink'] = 'https://books.google.co.kr/googlebooks/images/no_cover_thumb.gif'
			else:
				datum['imageLink'] = images[index]['src']

			# get the book's isbn
			isbn = self.getIsbn(isbns[index]['href'])
			if isbn is None:
				break
			datum['ISBN'] = isbn

			# get the book's title
			datum['title'] = titles[index].text.strip()

			# split the info that contains author, publisher and publishedYear.
			info = infos[index].text.strip().split('\n')

			# if length of info is less than 5, ignore it because this is gift.
			if len(info) < 5: 
				continue

			# get the book's author, publisher and publishedYear
			datum['author'] = info[0].strip()
			datum['publisher'] = info[-2].split('|')[-1].strip()
			datum['publishedYear'] = info[-1].split('|')[-1].strip()
			
			# get the book's market price
			datum['marketPrice'] = self.parsePrice(prices[index].text.strip())

			# append the dictionary to list
			data.append(datum)

		return data

	# crawl data from some sites using isbn
	def getUsedbookData(self, isbn):

		data = []

		# kyobo case
		search_url = 'http://www.kyobobook.co.kr/search/SearchUsedBookMain.jsp?vPstrCategory=USE&vPstrKeyWord=' + str(isbn) + '&vPplace=top'
		self.driver.get(search_url)
		html = self.driver.page_source

		soup = bs(html, 'html.parser')
		details = soup.select('#container > div.list_search_result > form > table > tbody > tr')

		for detail in details:
			datum = {}
			datum['site'] = 'kyobo'
			datum['price'] = self.parsePrice(detail.select('td.price > div.sell_price > strong')[0].text.strip())
			datum['link'] = detail.select('div.title > a')[0]['href'].strip()
			data.append(datum)

		# aladin case
		try:
			search_url = 'https://www.aladin.co.kr/search/wsearchresult.aspx?SearchTarget=Used&KeyWord=' + str(isbn) + '&KeyRecentPublish=0&OutStock=0&ViewType=Detail&CustReviewCount=0&CustReviewRank=0&KeyFullWord=' + str(isbn) + '&KeyLastWord=' + str(isbn) + '&CategorySearch=&chkKeyTitle=&chkKeyAuthor=&chkKeyPublisher='
			self.driver.get(search_url)
			self.driver.find_element_by_xpath('//*[@id="Search3_Result"]/div/table/tbody/tr/td[3]/table/tbody/tr[1]/td[2]/div/div[1]/a').click()
			html = self.driver.page_source

			soup = bs(html, 'html.parser')
			details = soup.select('#Myform > div > table > tbody > tr > td:nth-of-type(2) > div:nth-of-type(1)')

			for detail in details:
				datum = {}
				datum['site'] = 'aladin'
				datum['price'] = self.parsePrice(detail.select('ul > li:nth-of-type(2) > span > b')[0].text.strip())
				datum['link'] = detail.select('ul > li:nth-of-type(1) > a.bo')[0]['href'].strip()
				data.append(datum)
		except:
			None
			
		return data
