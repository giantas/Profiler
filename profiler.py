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

	# FIX: Name_list should not be none
	def __init__(self, name_list=None, name_count=None, view=None, interactive=None, common_term=None, browser=None, search_engine=None):
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

		if isinstance(search_engine, list):
			self.search_engine = 'http://' + search_engine[0].lower() + '.com'
		else:
			self.search_engine = 'http://google.com'

		self.names_list = name_list
		self.names = ' '.join(self.names_list)
		self.view = view
		self.interactive = interactive
		self.valid_links = {}
		self.netlocs = []
		
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

		name_combinations = []
		for i in range(2, self.name_count +1):
			name_combinations += list(itertools.permutations(name_list, i))

		return name_combinations

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
			self.interactive and print(color.DARKCYAN + '----{0}--- OK'.format(resp.url) + color.END)
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

		print('\n{:-^60}'.format('\nInitiating.\n'))
		print('Searching...\n')
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
			self.view and self.print_links()

	def search_tags(self, search_engine=None):
		tags = []
		if search_engine is None:
			search_engine = self.search_engine

		if search_engine == 'http://bing.com':
			tags.append('cite')
		else: # search_engine == Google
			tags.append('.r a')
			tags.append('cite')
			tags.append('.gl')
		return tags

	def soup_links(self, souped_text, tags):
		souped_links = []
		for tag in tags:
			souped_links.append(souped_text.select(tag))
		return souped_links

	def search_names(self, two_names):
		valid_comb_links ={}
		common_term = self.common_term or ''
		names = two_names
		search_query = self.search_engine + '/search?q=' + names + ' ' + ' '.join(common_term.split('_'))
		self.interactive and print('Search query: ', search_query)

		search_resp = requests.get(search_query)
		if self.valid_response(search_resp):
			souped_text = bs4.BeautifulSoup(search_resp.text, 'html.parser')

			search_tags = self.search_tags()
			souped_links = self.soup_links(souped_text, search_tags)
			valid_comb_links = self.get_lists(*souped_links)

		return self.deduplify_domain(valid_comb_links)

	def open_links(self, links_list=None):
		"""Open links in browser."""

		action = self.set_action()
		if links_list is None:
			links_list = self.valid_links

		print('\nOpening links...\n')
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
			for count, value in enumerate(self.valid_links.items(), 1):
				if value[1][1] is None:
					print('\n{0} - {1}'.format(str(count), value[1][0]))
				else:
					print('\n{0} - {1}\n{2}{3}'.format(str(count), str(value[1][0]), self.search_engine, str(value[1][1])))
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

		def deduplify_item(i, v, v_link, deduplified):
			if v_link is not None:
				clear_item = self.clear_path(v_link)

				if clear_item not in self.netlocs:
					self.netlocs.append(clear_item)
					if v not in deduplified.values():
						deduplified[i] = v

			else:
				if v not in deduplified.values(): deduplified[i] = v

		deduplified = {}
		for i,v in links_dict.items():
			if self.search_engine == 'http://google.com':
				deduplify_item(i, v, v[1], deduplified)
			if self.search_engine == 'http://bing.com':
				deduplify_item(i, v, v[0], deduplified)
				

		return deduplified


if __name__ == '__main__':
	# Supported browsers
	browsers = ['chrome', 'chromium', 'firefox', 'default']
	engines = ['google', 'bing']

	class CountAction(argparse.Action):

		def __call__(self, parser, namespace, values, option_string):
			if values[0] < 2:
				parser.error('Count cannot be less than 2.')

			setattr(namespace, self.dest, values)

	# Parse terminal arguments
	parser = argparse.ArgumentParser()
	parser.add_argument('name', help='User name(s) to use in search.', nargs='+')
	parser.add_argument('-c', '--count', help='The number of names to include in search. Default is 2.', action=CountAction, nargs=1, type=int)
	parser.add_argument('-v', '--view', help='View links in terminal.', action='store_true')
	parser.add_argument('-t', '--term', help='Common term(s) to use in search. Joined by underscore.', nargs=1)
	parser.add_argument('-o', '--open', help='Open links in specified browser.', nargs=1, choices=browsers)
	parser.add_argument('-i', '--interactive', help='Display messages.', action="store_true")
	parser.add_argument('-e', '--engine', help='Search engine to use.', nargs=1, choices=engines)

	if len(sys.argv) > 1:
		options = vars(parser.parse_args())

		names_num = len(options['name'])
		if options['count'] and options['count'][0] > names_num:
			raise parser.error('Count cannot be greater than the number of names, %s here.' % names_num)

		me = BrowseMe(options['name'], options['count'], options['view'], options['interactive'], options['term'], options['open'], options['engine'])

		# TODO: Add support for Google's "No result found for ... Showing for ...". 
		# TODO: Add blacklisting option
		# TODO: Add profile report generation
		# TODO: Add terminal interaction
		me.do_search()
		print('{:-^60}\n'.format('\nDone.\n'))

	else:
		print('\n' + color.RED + 'Command incomplete. No arguments found' + color.END + '\n')
		parser.print_help()