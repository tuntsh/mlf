# -*- coding: utf-8 -*-
import json
import logging
import os
import sys
from pathlib import Path
import requests
import codecs
import time
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from selenium.webdriver.support.ui import WebDriverWait
from scrapy.selector import Selector
from bs4 import BeautifulSoup
import re

logger = logging.getLogger(__name__)

################# Artist ###################
def crawlArtist(driver, doc_id, link):
	logger.info('Downloaded %s', link)

	try:
		wait = WebDriverWait(driver, 10)
		driver.get(link)
		wait.until(EC.presence_of_element_located((By.XPATH, '//ul[@class="artists_index_list"]')))
		driver.execute_script("window.stop();")

		sel = Selector(text=driver.page_source)
		nodes = sel.xpath('//ul[@class="artists_index_list"]/li')
		send_datas = []
		for node in nodes:
			artist_name = node.xpath('.//a/text()').extract_first()
			artist_url = node.xpath('.//a/@href').extract_first()
			if artist_name and artist_url:
				send_datas.append({'artist_name':artist_name,'artist_url':artist_url})

		for send_data in send_datas:
			if not isExitsDocument('genius_artist', 'artist_url', send_data['artist_url']):
				insertDocument('genius_artist',send_data)
				logger.info('Insert %s', send_data['artist_url'])
			else:
				logger.info('Exits %s',send_data['artist_url'])

		update_data = {'crawl_status':1}
		updateDocument('genius_page', doc_id, update_data)
		logger.info('Update Document %s',doc_id)

	except Exception as e:
		logger.error('Failed to do something: ' + str(e))


############## Song #############
def crawlSong(doc_id, artist_name, artist_url):
	logger.info('Scrap %s', artist_url)

	try:
		headers = {'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/68.0.3440.106 Safari/537.36'}
		r = requests.get(artist_url, headers=headers)

		sel = Selector(text=r.content)
		artist_id = sel.xpath('//meta[@name="newrelic-resource-path"]/@content').extract_first().replace('/artists/','')

		if artist_id:
			page = 1
			songs = []
			while 1:
				api_url = 'https://genius.com/api/artists/'+artist_id+'/songs?page='+str(page)+'&sort=popularity'
				r = requests.get(api_url)
				jdatas = r.json()

				logger.info('Loop %s', api_url)
				
				if jdatas['meta']['status'] == 200:
					for sdata in jdatas['response']['songs']:
						song = {
							'song_name': sdata['title'].encode('utf8'),
							'song_full_name': sdata['full_title'].encode('utf8'),
							'song_url': sdata['url'],
							'song_api_url': sdata['api_path'],
							'crawl_status': 0,
							'artist_name': artist_name
						}
						songs.append(song)

				if not jdatas['response']['next_page']:
					break
				page += 1

			return songs
			#print json.dumps(songs, indent=1, sort_keys=True)
		else:
			logger.error('Faild Artist_ID')
			return False

	except Exception as e:
		logger.error('Failed to do something: ' + str(e))
		return False

################# Lyrics ######################
def crawlLyric(driver, doc_id, link):
	driver.get(link)
	time.sleep(1.5)
	try:
		ele = WebDriverWait(driver, 10).until(
        						EC.presence_of_element_located((By.XPATH, '//div[@class="lyrics"]/section/p'))
        					)
		#wait = WebDriverWait(driver, 15)
		#wait.until(EC.presence_of_element_located((By.XPATH, '//div[@class="lyrics"]')))
		#driver.execute_script("window.stop();")
		
		#ele = driver.find_element_by_xpath("//div[@class='lyrics']/section/p")
		content = ele.get_attribute("outerHTML")

		if content:
			content = content.replace("<br>","---breeaakk---")
			soup = BeautifulSoup(content, 'html.parser')
			gettext = soup.get_text().strip()
			gettext = re.sub(r'\n+', '', gettext)

			lyrics = gettext.split("---breeaakk---")
			return lyrics

	except Exception as e:
		logger.error('Failed to do something: ' + str(e))

	