#!/usr/bin/env python3

import pickle
import random
import re
import sys

from porter import stem

class Essayeur:
	MAX_NGRAM = 4

	def __init__(self):
		self.transcript = []
		self.responses = []
		self.ngrams = {}
		self.debug = False
		for i in range(0, Essayeur.MAX_NGRAM):
			self.ngrams[i+1] = {}

	def store_ngrams(self, text):
		stems = tuple(stem(word) for word in text.split())
		for n in range(1, Essayeur.MAX_NGRAM+1):
			for i in range(0, len(stems)-n+1):
				ngram = stems[i:i+n]
				self.ngrams[n][ngram] = self.ngrams[n].get(ngram, 0) + 1

	def respond(self, text):
		text = re.sub("^[^'0-9A-Za-z]*", "", re.sub("[^[^'0-9A-Za-z]$", "", text.strip()))
		self.transcript.append(text)
		self.store_ngrams(text)
		response = "I don't understand what you're saying."
		self.responses.append(response)
		return response

def process_command(statement, essayeur):
	statement = statement[1:]
	tokens = statement.split()
	command = tokens[0]
	if command == "help":
		print(re.sub("^\t*", "    ", """
				\exit       Quit this program
				\help       Print this help message
				\history    Print the history of Essayeur
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

def cli(essayeur):
	print("type \"\\help\" to see a list of commands")
	print("")
	sentence = ""
	while not sentence[:5] in ("\\exit", "\\quit"):
		sentence = sentence.strip()
		if sentence:
			if sentence.startswith("\\") and not sentence[:5] in ("\\exit", "\\quit"):
				process_command(sentence, essayeur)
			else:
				print(essayeur.respond(sentence))
		print("")
		sentence = input("{}> ".format(len(essayeur.transcript)))

if __name__ == "__main__":
	if len(sys.argv) == 2:
		with open(sys.argv[1], "rb") as fd:
			essayeur = pickle.load(fd)
	else:
		essayeur = Essayeur()
	try:
		cli(essayeur)
	except KeyboardInterrupt:
		pass
