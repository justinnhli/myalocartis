#!/usr/bin/env python3

from bisect import bisect
import pickle
import random
import itertools
import re
import sys

from lingtools import stem, is_stop_word

class Cartographer:
	def __init__(self, text):
		self.qid = 0
		self.nodes = {}
		self.qid_map = {}
		self.nodes[text] = set()
		self.qid_map[self.qid] = text
		self.qid += 1
	def explore(self, source, text):
		text = re.sub(" +", " ", text.strip())
		text = re.sub("[^[^'0-9A-Za-z]$", "", text)
		text = re.sub("^[^'0-9A-Za-z]*", "", text)
		for word, stem in ((word, stem(word)) for word in text.split()):
			if not is_stop_word(word):
				self.add(source, "define \"{}\"".format(word))
	def add(self, source, question):
		if question in self.nodes:
			self.nodes[question].add(source)
		else:
			self.nodes.setdefault(question, set()).add(source)
			self.qid_map[self.qid] = question
			self.qid += 1
	def print_dot(self):
		print("digraph {")
		print("    overlap=false")
		for qid, question in self.qid_map.items():
			print("    Q{qid} [label=\"Q{qid}\\n{question}\"]".format(qid=qid, question=question.replace('"', r'\"')))
			for source in self.nodes[question]:
				print("    Q{source} -> Q{qid}".format(source=source, qid=qid))
		print("}")

class Essayeur:
	MAX_NGRAM = 4
	GENERIC_RESPONSES = set((
			"I don't understand what you're saying.",
			))

	def __init__(self):
		# settings
		self.debug = False
		# history
		self.transcript = []
		self.responses = []
		# statistics
		self.ngrams = {}
		# decision state
		self.clear_decision_state()
		# future state
		self.next_type = ""
		# initialization
		for i in range(0, Essayeur.MAX_NGRAM):
			self.ngrams[i+1] = {}

	def process_input(self, text):
		text = text.strip()
		if text.startswith("\\"):
			self.process_command(text)
		elif text:
			return self.decide_response(text)
		return None

	def process_command(self, statement):
		# TODO turn this into an Essayeur argparse object
		statement = statement[1:]
		tokens = statement.split()
		command = tokens[0]
		if command == "choices":
			num_choices = len(self.acceptable_responses)
			for index, response in enumerate(self.acceptable_responses.keys()):
				print("{:{width}}: {}".format(index, response, width=num_choices))
		elif command == "force":
			choice = int(tokens[1])
			response = list(self.acceptable_responses.keys())[int(tokens[1])]
			self.responses = self.responses[:-1]
			self.responses.append(response)
			print(response)
		elif command == "help":
			print(re.sub("^\t*", "    ", r"""
					\choices    Show all considered repsonses
					\exit       Quit this program
					\force N    Forace the selected response instead
					\help       Print this help message
					\history    Print a transcript of the current session
					\quit       Quit this program
					\save FILE  Save the state of Essayeur to FILE
					""".strip(), flags=re.MULTILINE))
		elif command == "history":
			for back, forth in zip(essayeur.transcript, essayeur.responses):
				print(back)
				print(forth)
		elif command == "save":
			with open(tokens[1], "wb") as fd:
				pickle.dump(essayeur, fd)
			print("Essayeur saved to {}".format(tokens[1]))

	def decide_response(self, text):
		self.clear_decision_state()
		text = re.sub(" +", " ", text.strip())
		text = re.sub("[^[^'0-9A-Za-z]$", "", text)
		text = re.sub("^[^'0-9A-Za-z]*", "", text)
		self.original_text = text
		self.split_text = text.split()
		self.update_statistics(text)
		for word, stem in zip(self.split_text, self.stemmed_text):
			if not is_stop_word(word):
				self.propose_response("What do you mean by \"{}\"?".format(word), "definition")
		response = self.select_response()
		self.apply_response(response)
		return response

	def select_response(self):
		original_responses = dict((key, value) for key, value in self.acceptable_responses.items() if key not in self.responses)
		# TODO do next_type (symbolic) selection
		if len(original_responses):
			return Essayeur.softmax(*((key, value[1]) for key, value in original_responses.items()))
		return random.choice(Essayeur.GENERIC_RESPONSES)

	def apply_response(self, response):
		self.next_type = self.acceptable_responses[response][0]
		self.update_history(self.original_text, response)

	def update_statistics(self, text):
		self.stemmed_text = [stem(word) for word in text.split()]
		for n in range(1, Essayeur.MAX_NGRAM+1):
			for i in range(0, len(self.stemmed_text)-n+1):
				ngram = tuple(self.stemmed_text[i:i+n])
				self.ngrams[n][ngram] = self.ngrams[n].get(ngram, 0) + 1

	def update_history(self, text, response):
		self.transcript.append(text)
		self.responses.append(response)

	def propose_response(self, response, next_type, utility=1):
		self.acceptable_responses[response] = (next_type, utility)

	def clear_decision_state(self):
		self.original_text = ""
		self.split_text = []
		self.stemmed_split_text = []
		self.acceptable_responses = {} # {response: (next_type, utility)
		self.sentence_type = set()

	@staticmethod
	def softmax(*weighted_choices):
		choices, weights = zip(*weighted_choices)
		cumdist = list(itertools.accumulate(weights))
		return choices[bisect(cumdist, random.random() * cumdist[-1])]

def cli(essayeur):
	print("type \"\\help\" to see a list of commands")
	text = ""
	while not text[:5] in ("\\exit", "\\quit"):
		response = essayeur.process_input(text.strip())
		if response:
			print(response)
		print("")
		text = input("{}> ".format(len(essayeur.transcript)))

if __name__ == "__main__":
	carto = Cartographer("I am uncomfortable with the fact that we're all alone together.")
	carto.add(0, "clarify \"we\"")
	carto.add(0, "define \"alone together\"")
	carto.add(0, "define \"uncomfortable\"")
	carto.add(0, "justify \"we're all alone together\"")
	carto.print_dot()
	exit()
	if len(sys.argv) == 2:
		with open(sys.argv[1], "rb") as fd:
			essayeur = pickle.load(fd)
	else:
		essayeur = Essayeur()
	try:
		cli(essayeur)
	except KeyboardInterrupt:
		print("")
