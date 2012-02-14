#!/usr/bin/env python3

from os import environ as env
from random import choice
import re
import sys

class myalocartis:

	def __init__(self):
		pass

	def respond(self, text):
		return "I don't understand what you're saying"

if __name__ == "__main__":
	mc = myalocartis()
	sentence = input("Enter a statement to begin: ")
	while sentence not in ("exit", "quit"):
		if sentence:
			print(mc.respond(sentence))
		print("")
		sentence = input("myalocartis> ")
