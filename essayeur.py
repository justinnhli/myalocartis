#!/usr/bin/env python3

from bisect import bisect
from os import fsync
import pickle
import random
import itertools
import re
import sys

from lingtools import stem as stem_word, is_stop_word

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

class Cartographer:

	def __init__(self):
		self.qid = 1
		self.nodes = {}
		self.questions = {}

	def expand(self, source, text):
		if source in self.nodes:
			self.nodes[source].answer = text
		else:
			self.nodes[source] = Node(source, "", text)
		for word, stem in ((word, stem_word(word)) for word in text.split()):
			if not is_stop_word(word):
				self.add(source, "define \"{}\"".format(word))
		dot = self.to_dot()

	def add(self, source, question):
		if question in self.questions:
			self.nodes[self.questions[question]].sources.add(source)
		else:
			node = Node(self.qid, question)
			node.sources.add(source)
			self.nodes[self.qid] = node
			self.questions[question] = self.qid
			self.qid += 1

	def to_dot(self):
		result = ["digraph {",]
		result.append("    overlap=false")
		for qid, node in self.nodes.items():
			result.extend(node.to_dot_list())
		result.append("}")
		return "\n".join(result)

def cli(carto, file=None):
	text = ""
	while not text[:4] in ("exit", "quit"):
		if text:
			text = re.sub(" +", " ", text.strip())
			text = re.sub("[^[^'0-9A-Za-z]$", "", text)
			text = re.sub("^[^'0-9A-Za-z]*", "", text)
			cmd, args = text.split(" ", 1)
			if cmd.isdigit():
				carto.expand(int(cmd), args)
				dot = carto.to_dot()
				if file:
					with open(file, "w") as fd:
						fd.write(dot)
						fd.flush()
						fsync(fd.fileno())
				else:
					print(dot)
			elif cmd == "save":
				with open(args, "wb") as fd:
					pickle.dump(carto, fd)
				print("Cartographer saved to {}".format(args))
			elif cmd == "load":
				with open(args, "rb") as fd:
					carto = pickle.load(fd)
				print("Cartographer loaded from {}".format(args))
			else:
				print("Command unknown")
		print("")
		text = input("> ")

if __name__ == "__main__":
	file = sys.argv[1] if len(sys.argv) == 2 else None
	try:
		cli(Cartographer(), file=file)
	except KeyboardInterrupt:
		print("")
