#!/usr/bin/env python
import sys
import os
import re
import vk_api


def extract_strings(directory, pattern, group=(0,)):
	result = list()
	for fileName in os.listdir(directory):
		if fileName.endswith('.html'):
			with open(os.path.join(directory, fileName)) as f:
				data = f.read()
				for match in re.finditer(pattern, data):
					if isinstance(group, int):
						result.append(match.group(group))
					elif isinstance(group, (list, tuple)):
						result.append([match.group(g) for g in group])
	return result


def main(login, password, archive_dir):
	vk_session = vk_api.VkApi(login, password)
	vk_session.auth()
	vk = vk_session.get_api()
	
	comment_links = extract_strings(
		os.path.join(archive_dir, 'comments'),
		r'"https://vk.com/wall(-?[0-9]+)_([0-9]+)\?reply=([0-9]+)"',
		(1, 2, 3)
	)
	wall_comments = {}
	for link in comment_links:
		wall_comments[int(link[0])] = link
	
	wall_ids = list(wall_comments.keys())
	walls = dict(
		[
			(info['id'], '%s %s' % (info['first_name'], info['last_name']))
			for info in vk.users.get(user_ids=list(filter(lambda id: id > 0, wall_ids)))
		] +
		[
			(-info['id'], info['name'])
			for info in vk.groups.getById(group_ids=[-id for id in filter(lambda id: id < 0, wall_ids)])
		]
	)
	
	i = 0
	for wall_id in wall_ids:
		print('[%s] %s #%s#' % (i, walls[wall_id], wall_id))
		i += 1
	preserve_wall_ids_str = input('Enter indexes of wall to preserve comments: ')
	if preserve_wall_ids_str:
		preserve_wall_ids = set(map(lambda j: wall_ids[int(j)], preserve_wall_ids_str.split(' ')))
	else:
		preserve_wall_ids = set()
	comment_ids = list(filter(lambda info: int(info[0]) not in preserve_wall_ids, comment_links))
	for comment in comment_ids:
		try:
			vk.wall.deleteComment(owner_id=int(comment[0]), comment_id=int(comment[2]))
		except vk_api.exceptions.ApiError as e:
			print(str(e))


if __name__ == "__main__":
	if len(sys.argv) != 4:
		print("Usage: %s login password /path/to/extracted/archive")
		sys.exit()
	main(sys.argv[1], sys.argv[2], sys.argv[3])
