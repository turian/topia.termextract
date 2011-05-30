#!/usr/bin/python

from topia.termextract import extract
extractor = extract.TermExtractor()

extractor.filter = extract.permissiveFilter

print extractor("The fox can't jump over the fox's tail.")
