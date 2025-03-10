import requests
from datetime import datetime
from dataclasses import dataclass
from typing import List, Dict, Optional

## Readwise will first check title/author/source_type to determine if it is a new book
## then check text to determine if it is a new highlight
## if not new, it will update it (e.g update category/highlighted_at)

# a class for a readwise highlight
@dataclass
class ReadwiseHighlight:
	text: 			str
	title:			Optional[str]	= None
	author:			Optional[str]	= None
	image_url:		Optional[str]	= None
	source_url:		Optional[str]	= None
	source_type:	Optional[str]	= None
	category:		Optional[str]	= None	# books, articles, podcasts, tweets
	note:			Optional[str]	= None	# create tags: '.tag1 .tag2'
	location:		Optional[int]	= None
	location_type:	Optional[str]	= None	# page, order, time_offset
	highlighted_at:	Optional[str]	= None	# ISO 8601 format, e.g. 2020-07-14T20:11:24+00:00
	highlight_url:	Optional[str]	= None

	# get a dict with non-None fields
	def get_dict(self):
		return {k: v for k, v in self.__dict__.items() if v is not None}

class Readwise:
	def __init__(self, access_token, logger):
		self.access_token = access_token
		self.headers = {'Authorization': 'Token ' + access_token}
		self.highlight_create_url = 'https://readwise.io/api/v2/highlights/'
		self.logger = logger

	""" Create highlights in Readwise """

	def create_highlights(self, highlights: List[Dict]):
		response = requests.post(
			f"{self.highlight_create_url}",
			headers=self.headers,
			json={"highlights": highlights}
		)
		
		if response.status_code != 200:
			self.logger.log(f"Failed to create highlights")
			self.logger.log(f"Error code: {response.status_code}")
			self.logger.log(f"Error message: {response.text}")
			raise Exception('Failed to create highlights')
	
	def create_highlights_from_memos(self, memos: List[Dict]):
		highlights = []
		for memo in memos:
			highlight = {
				'title': memo.get('title') or 'Flomo Import',  # 如果没有标题就使用默认标题
				'text': memo.get('content', ''),
				'source_url': memo.get('url', ''),
				'source_type': 'flomo'
			}
			highlights.append(highlight)
		
		if highlights:
			self.create_highlights(highlights)
		else:
			self.logger.log("No highlights to create")

	""" flomo memo -> Readwise highlight """

	def convert_memos_to_highlights(self, memos: List[Dict]) -> List[Dict]:
		highlights = []
		# convert
		for memo in memos:
			highlights.append(self.convert_memo_to_highlight(memo))
		# sort
		highlights = self.sort_highlights_by_time(highlights)
		return highlights

	def convert_memo_to_highlight(self, memo: dict) -> Dict:
		hl = ReadwiseHighlight(text=memo['text'])
		if 'author' in memo:	hl.author = memo['author']
		if 'category' in memo:	hl.category = memo['category']
		if 'title' in memo:		hl.title = memo['title']
		else:
			title = memo['text'].split('\n')[0]
			if len(title) > 20: title = title[:20] + '...'
			hl.title = title
		hl.note = self.convert_tags_to_note(memo['tags'])
		hl.highlight_url = memo['flomo_url']
		hl.highlighted_at = self.convert_memotime_to_iso8601(memo['edit_time'])
		hl.source_type = 'flomo-Notion'
		return hl.get_dict()

	def convert_tags_to_note(self, tags: List[str]) -> str:
		return ' '.join([f'.{tag}' for tag in tags])

	def convert_memotime_to_iso8601(self, memotime: str) -> str:
		# memotime format: '2023-04-17T00:00:00.000Z'
		# iso8601 format: '2023-04-17T00:00:00+00:00'
		return memotime.replace('Z', '+00:00')

	def sort_highlights_by_time(self, highlights: List[Dict]) -> List[Dict]:
		# time format: 'YYYY-MM-DDTHH:MM:SS+00:00'
		highlights.sort(key=lambda x: datetime.fromisoformat(x['highlighted_at']))
		return highlights
