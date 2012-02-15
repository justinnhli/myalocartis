#!/usr/bin/env python3

import pickle
import random
import re
import sys

from porter import stem

class myalocartis:
	MAX_NGRAM = 4

	def __init__(self):
		self.ngrams = {}
		self.debug = False
		for i in range(0, myalocartis.MAX_NGRAM):
			self.ngrams[i+1] = {}

	def store_ngrams(self, text):
		stems = tuple(stem(word) for word in text.split())
		print(stems)
		for n in range(1, myalocartis.MAX_NGRAM+1):
			for i in range(0, len(stems)-n+1):
				ngram = stems[i:i+n]
				self.ngrams[n][ngram] = self.ngrams[n].get(ngram, 0) + 1

	def respond(self, text):
		text = re.sub("^[^'0-9A-Za-z]*", "", re.sub("[^[^'0-9A-Za-z]$", "", text.strip()))
		self.store_ngrams(text)
		print(self.ngrams)
		return "I don't understand what you're saying."

if __name__ == "__main__":
	mc = myalocartis()
	sentence = input("Enter a statement to begin: ")
	try:
		while sentence not in ("exit", "quit"):
			if sentence:
				print(mc.respond(sentence))
			print("")
			sentence = input("myalocartis> ")
	finally:
		print(pickle.dumps(mc, pickle.HIGHEST_PROTOCOL))
