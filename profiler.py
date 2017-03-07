#! /usr/bin/python3

# myprofile.py
# Takes in a user's name and searches the top results on Google related to the user
# Then opens the relevant tabs

import requests, sys, os, webbrowser, bs4, itertools, re, textwrap
import argparse

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

def indent(text, **kwargs):
	return textwrap.fill(text, subsequent_indent='\t', **kwargs)

def write_to_file():
	with open('search_results.html', 'wb') as results_html:
		for chunk in search_resp.iter_content(100000):
			results_html.write(chunk)

def all_combinations(name_list):
	name_combinations = []
	for i in range(0, len(name_list)+1):
		for subset in itertools.combinations(name_list, i):
			#name_combinations.append(' '.join(subset))
			name_combinations.append(subset)

	start = len(name_list)+1
	forward_list = [result for result in name_combinations[start:] if len(result) == 2]
	backward_list = [(item[1], item[0]) for item in forward_list[::-1]]
	return forward_list + backward_list

def find_links(valid_links, links_list):
	for count, item in enumerate(links_list):
		if count not in valid_links:
			for names in name_combs:
				#print('Names: ',names[0], names[1])
				name_regex = r'.*' + str(names[0]) + r'[\s\-\.]{0,1}' + str(names[1]) + r'.*'
				if re.match(name_regex, str(item.get_text()), re.I) is not None:
					valid_links[count] = [item.get_text(),  item.get('href')]

	return valid_links

def get_lists(*args):
	valid_links = {}
	#print("Printing lists")
	for links_list in args:
		find_links(valid_links, links_list)

	return valid_links

def valid_response(resp):
	try:
		resp.raise_for_status()
	except Exception as excptn:
		print(indent('There was a problem with ' + color.RED + resp.url + color.END + ' %s' % excptn))
		return False
	else:
		print(indent('Link ' + color.DARKCYAN + resp.url + color.END + ' works'))
		return True

def set_browser(path):
	if os.path.isfile(path):
		return webbrowser.get(path).open
	else:
		print('Failed to locate: %s' % path)
		return webbrowser.open

def set_action(browser_choice):
	firefox_path = '/usr/bin/firefox'
	chrome_path = '/usr/bin/google-chrome'
	chromium_path = '/usr/bin/chromium'
	opera_path = '/usr/bin/opera'

	if browser_choice == 'chrome':
		action = set_browser(chrome_path)
	elif browser_choice == 'firefox':
		action = set_browser(firefox_path)
	elif browser_choice == 'chromium':
		action = set_browser(chromium_path)
	elif browser_choice == 'default':
		action = webbrowser.open
	else:
		action = webbrowser.open

	return action

# Supported browsers
browsers = ['chrome', 'chromium', 'firefox', 'default']

# Parse terminal arguments
parser = argparse.ArgumentParser()
parser.add_argument('-o', '--open', help='Open links in browser', nargs='?', choices=browsers)
parser.add_argument('name', help='User name(s) to use in search', nargs='+')


if len(sys.argv) > 1:
	options = vars(parser.parse_args())
	# TODO: Specify behaviour if no arguments passed

	print()
	#print(options['open'])
	#print(options['name'])
	#action = webbrowser.open

	if options['open']:
		action = set_action(options['open'])
	else:
		print('Browser not specified. Using default')
		action = webbrowser.open

	name_list = options['name']
	names = ' '.join(name_list)
	name_combs = all_combinations(name_list) # Get all name combinations
	#print(name_combs)
	print()
	#print(names)
	search_engine = 'http://google.com'
	search_query = 'http://google.com/search?q=' + names
	print('Search query: ', search_query)
	print()

	search_resp = requests.get(search_query)
	if valid_response(search_resp):
		search_text = search_resp.text
		#print(search_text.prettify())
		souped_text = bs4.BeautifulSoup(search_text, 'html.parser')

		top_links = souped_text.select('.r a')
		cited_links = souped_text.select('cite')
		gl_links = souped_text.select('.gl')

		valid_links = get_lists(top_links, cited_links, gl_links)

		if not valid_links:
			print(color.BLUE + 'No results found.' + color.END)
		else:
			print('Showing valid links')
			for i in valid_links:
				print(valid_links[i][0])
				print(valid_links[i][1])
				print()

			#print(bool(options['open']))
			if options['open'] is not None:
				print('Opening links')
				for i in valid_links:
					try:
						action(search_engine + valid_links[i][1])
					except TypeError:
						print(color.RED + 'Link skipped: %s' % valid_links[i][0] + color.END)
						pass
else:
	print('\n' + color.RED + 'Command incomplete. No arguments found' + color.END + '\n')
	parser.print_help()	