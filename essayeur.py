#!/usr/bin/env python3

from bisect import bisect
from os import fsync
import pickle
import random
import itertools
import re
import sys

from lingtools import stem as stem_word, is_stop_word

class _Node:
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
			self.nodes[source] = _Node(source, "", text)
		self.clarify(source, text)
		self.define(source, text)
		dot = self.to_dot()

	def add(self, source, question):
		if question in self.questions:
			qid = self.questions[question]
			if qid != source:
				self.nodes[qid].sources.add(source)
		else:
			node = _Node(self.qid, question)
			node.sources.add(source)
			self.nodes[self.qid] = node
			self.questions[question] = self.qid
			self.qid += 1

	def to_dot(self):
		result = ["digraph {",]
		result.append("    layout=neato")
		result.append("    start=Q0")
		result.append("    overlap=scalexy")
		for qid, node in self.nodes.items():
			result.extend(node.to_dot_list())
		result.append("}")
		return "\n".join(result)

	def clarify(self, source, text):
		for word in text.lower().split():
			if word in ("we", "us", "our", "ours", "ourselves", "we'd", "we'll", "we're", "we've"):
				self.add(source, "clarify \"{}\"".format(re.sub("'.*", "", word)))
			elif word in ("he", "him", "his", "himself", "he'd", "he'll", "he's", "she", "her", "hers", "herself", "she'd", "she'll", "she's"):
				self.add(source, "clarify \"{}\"".format(re.sub("'.*", "", word)))
			elif word in ("it", "its", "itself", "it's"):
				self.add(source, "clarify \"{}\"".format(re.sub("'.*", "", word)))
			elif word in ("they", "them", "their", "theirs", "themselves", "they'd", "they'll", "they're", "they've"):
				self.add(source, "clarify \"{}\"".format(re.sub("'.*", "", word)))

	def define(self, source, text):
		for word, stem in ((word, stem_word(word)) for word in text.split()):
			if not is_stop_word(word):
				self.add(source, "define \"{}\"".format(word))

	def justify(self, source, text):
		if "the fact that" in text:
			self.add(source, "justify \"{}\"".format(re.search("the fact that (.*)", text).group(1)))
		if "despite" in text:
			self.add(source, "justify \"{}\"".format(re.search("despite (.*)", text).group(1)))

def cli(carto, file=None):
	text = ""
	while not text[:4] in ("exit", "quit"):
		print_state = False
		if text:
			text = re.sub(" +", " ", text.strip())
			text = re.sub("[^[^'0-9A-Za-z]$", "", text)
			text = re.sub("^[^'0-9A-Za-z]*", "", text)
			cmd, args = text.split(" ", 1)
			if cmd.isdigit():
				carto.expand(int(cmd), args)
				print_state = True
			elif cmd == "save":
				with open(args, "wb") as fd:
					pickle.dump(carto, fd)
				print("Cartographer saved to {}".format(args))
			elif cmd == "load":
				with open(args, "rb") as fd:
					carto = pickle.load(fd)
				print("Cartographer loaded from {}".format(args))
				print_state = True
			elif cmd == "import":
				with open(args, "rb") as fd:
					other = pickle.load(fd)
				for node in other.nodes.values():
					if node.question in carto.questions:
						carto.expand(carto.questions[node.question], node.answer)
				print("Map imported from Cartographer {}".format(args))
				print_state = True
			else:
				print("Command unknown")
			if print_state:
				if file:
					with open(file, "w") as fd:
						fd.write(carto.to_dot())
						fd.flush()
						fsync(fd.fileno())
				else:
					print("\n".join("{}\t{}".format(qid, node.question) for qid, node in carto.nodes.items() if not node.answer))
		print("")
		text = input("> ")

if __name__ == "__main__":
	file = sys.argv[1] if len(sys.argv) == 2 else None
	try:
		cli(Cartographer(), file=file)
	except KeyboardInterrupt:
		print("")
