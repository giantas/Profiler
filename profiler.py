#! /usr/bin/python3

# myprofile.py
# Takes in a user's name and searches the top results on Google related to the user
# Then opens the relevant tabs

import requests, sys, os, webbrowser, bs4, itertools, re, textwrap
import argparse
from urllib.parse import urlparse

class color:
   PURPLE = '\033[95m'
   CYAN = '\033[96m'
   DARKCYAN = '\033[36m'
   BLUE = '\033[94m'
   GREEN = '\033[92m'
   YELLOW = '\033[93m'
   RED = '\033[91m'
   BOLD = '\033[1m'
   UNDERLINE = '\033[4m'
   END = '\033[0m'

class BrowseMe(object):
	"""Find all instances of user name(s) online."""

	browsers = ['chrome', 'chromium', 'firefox', 'default']
	firefox_path = '/usr/bin/firefox'
	chrome_path = '/usr/bin/google-chrome'
	chromium_path = '/usr/bin/chromium'
	opera_path = '/usr/bin/opera'
	search_engine = 'http://google.com'

	def __init__(self, name_list, name_count, view, common_term, browser=None):
		"""Initialise the browser, user name(s) and valid_links."""

		if browser is not None:
			self.browser = browser[0]
		else:
			self.browser = browser

		if common_term is not None:
			self.common_term = common_term[0]
		else:
			self.common_term = common_term

		if name_count is not None:
			self.name_count = name_count[0]
		else:
			self.name_count = 2

		self.names_list = name_list
		self.names = ' '.join(self.names_list)
		self.view = view
		self.valid_links = {}
		self.netlocs = []
		#self.name_combinations = self.all_combinations()
		
	def indent(self, text, **kwargs):
		"""Use textwrap to indent output by one tab key."""

		return textwrap.fill(text, subsequent_indent='\t', **kwargs)

	def all_combinations(self, name_list=None):
		"""Find all possible combinations of names specified.

		Defaults to two-names results.

		"""
		
		if name_list is None:
			name_list = self.names_list

		if len(name_list) == 1:
			return [(name_list[0],)]

		return list(itertools.permutations(name_list, self.name_count))

	def find_links(self, valid_links, links_list):
		"""Find links that match user name provided."""

		# TODO: Add support for third name search in regex
		name_combs = self.all_combinations()
		for count, item in enumerate(links_list):
			if count not in valid_links:
				for names in name_combs:
					try:
						name_regex = r'.*' + str(names[0]) + r'[\s\-\.]{0,1}' + str(names[1]) + r'.*'
					except IndexError:
						name_regex = r'.*' + str(names[0]) + r'[\s\-\.]{0,1}' + r'.*'
					if re.match(name_regex, str(item.get_text()), re.I) is not None:
						valid_links[count] = [item.get_text(),  item.get('href')]

		return valid_links

	def get_lists(self, *args):
		valid_links = {}
		#print("Printing lists")
		for links_list in args:
			self.find_links(valid_links, links_list)

		return valid_links

	def valid_response(self, resp):
		try:
			resp.raise_for_status()
		except Exception as excptn:
			print(self.indent('There was a problem with ' + color.RED + resp.url + color.END + ' %s' % excptn))
			return False
		else:
			print(self.indent('Link ' + color.DARKCYAN + resp.url + color.END + ' works'))
			return True

	def set_browser(self, path):
		if os.path.isfile(path):
			return webbrowser.get(path).open
		else:
			print('Failed to locate: %s' % path)
			return webbrowser.open

	def set_action(self):
		browser_choice = self.browser

		if browser_choice == 'chrome':
			self.action = self.set_browser(self.chrome_path)
		elif browser_choice == 'firefox':
			self.action = self.set_browser(self.firefox_path)
		elif browser_choice == 'chromium':
			self.action = self.set_browser(self.chromium_path)
		elif browser_choice == 'default':
			self.action = webbrowser.open
		else:
			self.action = webbrowser.open

		return self.action

	def do_search(self, name_combs=None):
		"""Initialise search."""
		if name_combs is None:
			name_combs = self.all_combinations(self.names_list)

		for two_names in name_combs:
			comb_result = self.search_names(' '.join(two_names))
			if comb_result: self.valid_links.update(comb_result)

		if not self.valid_links:
			print(color.BLUE + 'No results found.' + color.END)
		else:
			print(color.BLUE + '%s result(s) found. Add "-v" to view.' % len(self.valid_links) + color.END)
			if self.browser is not None:
				self.open_links()
			else:
				self.print_links()

	def search_names(self, two_names):
		common_term = self.common_term or ''
		names = two_names
		search_query = 'http://google.com/search?q=' + names + ' ' + ' '.join(common_term.split('_'))
		print('Search query: ', search_query)
		print()
		valid_comb_links ={}

		search_resp = requests.get(search_query)
		if self.valid_response(search_resp):
			souped_text = bs4.BeautifulSoup(search_resp.text, 'html.parser')

			top_links = souped_text.select('.r a')
			cited_links = souped_text.select('cite')
			gl_links = souped_text.select('.gl')

			valid_comb_links = self.get_lists(top_links, cited_links, gl_links)

		return self.deduplify_domain(valid_comb_links)

	def search_names_from_files(self, two_names):
		names = two_names
		print()
		valid_comb_links ={}

		file_name = names + '.html'
		open_file = open(file_name, 'r', encoding='ISO-8859-1').read()
		souped_text = bs4.BeautifulSoup(open_file, 'html.parser')

		top_links = souped_text.select('.r a')
		cited_links = souped_text.select('cite')
		gl_links = souped_text.select('.gl')

		valid_comb_links = self.get_lists(top_links, cited_links, gl_links)

		return self.deduplify_domain(valid_comb_links)

	def open_links(self, links_list=None):
		"""Open links in browser."""

		action = self.set_action()
		if links_list is None:
			links_list = self.valid_links

		print('Opening links...')
		for i in links_list:
			try:
				action(self.search_engine + links_list[i][1])
			except TypeError:
				action(links_list[i][0])
		return 

	def deduplify(self, links_dict):
		"""Remove duplicate links."""

		deduplified = {}
		for i,v in links_dict.items():
			if v not in deduplified.values():
				deduplified[i] = v
		return deduplified

	def print_links(self):
		if self.view:
			for key, value in self.valid_links.items():
				print(int(key)+1, '-', self.indent(value[0]))
				if value[1] is None:
					print('\t' + value[0])
				else:
					print('\t' + self.search_engine + str(value[1]))
				print()

		return

	def clear_path(self, string):
		"""Get domain.

		Clear search path, get query fragment and split result to get domain.

		"""

		new_string = string.replace('/url?q=', '')
		parsed_url = urlparse(new_string)
		try:
			domain = '.'.join(parsed_url.hostname.split('.')[1:])
		except AttributeError:
			domain = new_string # For Google image search
		return domain


	def deduplify_domain(self, links_dict):
		"""Remove duplicate domain links."""

		deduplified = {}
		for i,v in links_dict.items():

			if v[1] is not None:
				clear_item = self.clear_path(v[1])

				if clear_item not in self.netlocs:
					self.netlocs.append(clear_item)
					if v not in deduplified.values(): deduplified[i] = v

				else:
					pass
			else:
				if v not in deduplified.values(): deduplified[i] = v
			
		return deduplified


if __name__ == '__main__':
	# Supported browsers
	browsers = ['chrome', 'chromium', 'firefox', 'default']

	class CountAction(argparse.Action):

		def __call__(self, parser, namespace, values, option_string):
			if values[0] < 1:
				parser.error('Count cannot be less than 1.')

			setattr(namespace, self.dest, values)

	# Parse terminal arguments
	parser = argparse.ArgumentParser()
	parser.add_argument('name', help='User name(s) to use in search', nargs='+')
	parser.add_argument('-c', '--count', help='The number of names to include in search. Default is 2.', action=CountAction, nargs=1, type=int)
	parser.add_argument('-v', '--view', help='View links in terminal', action='store_true')
	parser.add_argument('-t', '--term', help='Common term(s) to use in search. Joined by underscore', nargs=1)
	parser.add_argument('-o', '--open', help='Open links in specified browser', nargs=1, choices=browsers)

	if len(sys.argv) > 1:
		options = vars(parser.parse_args())

		names_num = len(options['name'])
		if options['count'] and options['count'][0] > names_num:
			raise parser.error('Count cannot be greater than the number of names, %s here.' % names_num)

		me = BrowseMe(options['name'], options['count'], options['view'], options['term'], options['open'])

		# TODO: Add support for Google's "No result found for ... Showing for ...". 
		me.do_search()

	else:
		print('\n' + color.RED + 'Command incomplete. No arguments found' + color.END + '\n')
		parser.print_help()