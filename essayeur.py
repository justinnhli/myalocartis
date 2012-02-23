#!/usr/bin/env python3

from bisect import bisect
from os import fsync
import pickle
import random
import itertools
import re
import sys

from lingtools import stem as stem_word, is_stop_word

class Cartographer:

	class Node:
		def __init__(self, qid, question=None, answer=None):
			self.qid = qid
			self.question = (question if question else "")
			self.answer = (answer if answer else "")
			self.sources = set()
		def to_dot_list(self):
			format_map = {
					"qid":self.qid,
					"question":self.question.replace('"', r'\"'),
					"answer":self.answer.replace('"', r'\"'),
					}
			result = []
			if self.answer:
				result.append("    Q{qid} [label=\"Q{qid}\\n{question}\\n{answer}\"]".format(**format_map))
			else:
				result.append("    Q{qid} [label=\"Q{qid}\\n{question}\"]".format(**format_map))
			for source in self.sources:
				result.append("    Q{source} -> Q{qid}".format(source=source, qid=self.qid))
			return result

	def __init__(self, file=None):
		self.qid = 1
		self.nodes = {}
		self.questions = {}
		self.file = file

	def expand(self, source, text):
		text = re.sub(" +", " ", text.strip())
		text = re.sub("[^[^'0-9A-Za-z]$", "", text)
		text = re.sub("^[^'0-9A-Za-z]*", "", text)
		if source in self.nodes:
			self.nodes[source].answer = text
		else:
			self.nodes[source] = Cartographer.Node(source, "", text)
		for word, stem in ((word, stem_word(word)) for word in text.split()):
			if not is_stop_word(word):
				self.add(source, "define \"{}\"".format(word))
		dot = self.to_dot()
		if self.file:
			with open(self.file, "w") as fd:
				fd.write(dot)
				fd.flush()
				fsync(fd.fileno())
		else:
			print(dot)

	def add(self, source, question):
		print(len(self.nodes))
		if question in self.questions:
			self.nodes[self.questions[question]].sources.add(source)
		else:
			self.nodes[self.qid] = Cartographer.Node(self.qid, question)
			self.questions[question] = self.qid
			self.qid += 1

	def to_dot(self):
		result = ["digraph {",]
		result.append("    overlap=false")
		for qid, node in self.nodes.items():
			result.extend(node.to_dot_list())
		result.append("}")
		return "\n".join(result)

def cli(carto):
	text = ""
	while not text[:5] in ("\\exit", "\\quit"):
		if text:
			source, text = text.split(" ", 1)
			carto.expand(int(source), text)
		print("")
		text = input("{}> ".format(""))

if __name__ == "__main__":
	if len(sys.argv) == 2:
		with open(sys.argv[1], "rb") as fd:
			carto = pickle.load(fd)
	else:
		carto = Cartographer()
	try:
		cli(carto)
	except KeyboardInterrupt:
		print("")
