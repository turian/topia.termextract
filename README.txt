This package determines important terms within a given piece of content. It
uses linguistic tools such as Parts-Of-Speech (POS) and some simple
statistical analysis to determine the terms and their strength.

NOTE: This is a fork by Joseph Turian of topia.termextract 1.1.0
CONTRIBUTIONS:
    * Unicode alphabetic characters are tokenized correctly.
    I changed TERM_SPEC in topic.termextract.tag:
        Old = [u'S', u'\xe3o', u'Paulo', u'was', u'home', u'to']
        New = [u'S\xe3o', u'Paulo', u'was', u'home', u'to']
    * extractor.extract() now has a parameter KEEP_ORIGINAL_SPACING=True,
    which allows you to keep the original spacing of the term:
        Old = [u'Mr . Smith']
        New = [u'Mr. Smith']
    * Fixed a bug where a term wouldn't be found if it was literally
    the last token of the sentence.
    * Fixed a bug (?) where unigram terms were included even if their
    tokens were part of a multiterm.
