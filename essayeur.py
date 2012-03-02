#!/usr/bin/env python3

from bisect import bisect
from os import fsync
from os.path import exists as file_exists
import random
import itertools
import re
import sys

from lingtools import stem as stem_word, is_stop_word

CUSTOM_STOP_LIST = ("something", "someone")

class _Node:
	def __init__(self, qid, question=None, answer=None):
		self.qid = qid
		self.question = (question if question else "")
		self.answer = (answer if answer else "")
		self.sources = set()
		self.hide = False
	def to_dot_list(self):
		format_map = {
				"qid":self.qid,
				"question":self.question.replace('"', r'\"'),
				"answer":self.answer.replace('"', r'\"'),
				}
		attrs = []
		if not self.question:
			attrs.append(("style", "bold"))
		if self.answer:
			attrs.append(("color", "#4E9A06"))
		else:
			attrs.append(("color", "#A40000"))
		attrs.append(("label", "Q{qid}\\n{question}\\n{answer}".format(**format_map)))
		result = ["    Q{} [{}]".format(self.qid, ", ".join("{}=\"{}\"".format(key, value) for key, value in attrs)),]
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
		self.ask(source, text)

	def ask(self, source, text):
		self.clarify(source, text)
		self.define(source, text)
		self.justify(source, text)

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

	def hide(self, qid):
		self.nodes[qid].hide = True

	def to_dot(self):
		result = ["digraph {",]
		result.append("    layout=neato")
		result.append("    overlap=scalexy")
		if self.nodes:
			result.append("    start=Q{}".format(self.questions[""]))
			for qid, node in self.nodes.items():
				result.extend(node.to_dot_list())
		result.append("}")
		return "\n".join(result)

	def from_dot(self, text):
		edges = {}
		mapping = {}
		for line in text.split("\n"):
			line = line.strip()
			if line.startswith("Q"):
				if re.match("^Q[0-9]+ -> Q[0-9]+$", line):
					edge = re.match("^Q([0-9]+) -> Q([0-9]+)$", line)
					srcs = edges.setdefault(int(edge.group(2)), set())
					srcs.add(int(edge.group(1)))
				else:
					qid = int(re.match("Q[0-9]+", line).group(0)[1:])
					label = re.search(r'label="Q{}\\n(.*)\\n(.*)"'.format(qid), line)
					question = re.sub(r'\\"', '"', label.group(1))
					answer = label.group(2)
					if question in self.questions:
						mapping[qid] = self.questions[question]
						qid = mapping[qid]
						if not self.nodes[qid].answer:
							self.nodes[qid].answer = answer
					else:
						mapping[qid] = self.qid
						qid = self.qid
						self.nodes[qid] = _Node(self.qid, question, answer)
						self.questions[question] = qid
						self.qid += 1
					self.ask(qid, answer)
		for dest, srcs in edges.items():
			dest = mapping[dest]
			for src in srcs:
				self.nodes[dest].sources.add(mapping[src])

	def clarify(self, source, text):
		for word in text.lower().split():
			word = re.sub("[^[^'0-9A-Za-z]$", "", word.lower())
			word = re.sub("^[^'0-9A-Za-z]*", "", word)
			if word:
				if word in ("we", "us", "our", "ours", "ourselves", "we'd", "we'll", "we're", "we've"):
					self.add(source, "clarify \"{}\"".format(re.sub("'.*", "", word)))
				elif word in ("he", "him", "his", "himself", "he'd", "he'll", "he's", "she", "her", "hers", "herself", "she'd", "she'll", "she's"):
					self.add(source, "clarify \"{}\"".format(re.sub("'.*", "", word)))
				elif word in ("it", "its", "itself", "it's"):
					self.add(source, "clarify \"{}\"".format(re.sub("'.*", "", word)))
				elif word in ("they", "them", "their", "theirs", "themselves", "they'd", "they'll", "they're", "they've"):
					self.add(source, "clarify \"{}\"".format(re.sub("'.*", "", word)))
				elif word in ("something", "someone"):
					self.add(source, "clarify \"{}\"".format(word))

	def define(self, source, text):
		for word, stem in ((word, stem_word(word)) for word in text.split()):
			word = re.sub("[^[^'0-9A-Za-z]$", "", word.lower())
			word = re.sub("^[^'0-9A-Za-z]*", "", word)
			if word:
				word = re.sub("[^[^'0-9A-Za-z]$", "", word)
				word = re.sub("^[^'0-9A-Za-z]*", "", word)
				if not is_stop_word(word, CUSTOM_STOP_LIST):
					self.add(source, "define \"{}\"".format(word.lower()))

	def justify(self, source, text):
		if "the fact that" in text:
			self.add(source, "justify \"{}\"".format(re.search("the fact that (.*)", text).group(1)))
		if "despite" in text:
			self.add(source, "justify \"{}\"".format(re.search("despite (.*)", text).group(1)))

def cli(carto, file=None):
	if file:
		text = "load {}".format(file)
	else:
		text = ""
	while not text[:4] in ("exit", "quit"):
		print_state = True
		if text and " " in text:
			cmd, args = text.split(" ", 1)
			if cmd.isdigit():
				if args == '""':
					args = ''
				carto.expand(int(cmd), args)
			else:
				if cmd == "load":
					if file_exists(args):
						with open(args, "r") as fd:
							carto.from_dot(fd.read())
						print("Cartographer loaded from {}".format(args))
				elif cmd == "new":
					qid = carto.qid
					carto.qid += 1
					carto.expand(qid, args)
					carto.questions[""] = qid
				elif cmd == "save":
					with open(args, "w") as fd:
						fd.write(carto.to_dot())
					print("Cartographer saved to {}".format(args))
					print_state = False
				else:
					print("Command unknown")
					print_state = False
		else:
			print("Command unknown")
			print_state = False
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
