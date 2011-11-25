#!/usr/bin/python
# -*- coding: utf8 -*-
############################################################################## #
# Copyright (c) 2009 Zope Foundation and Contributors.
# All Rights Reserved.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.1 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE.
#
##############################################################################
"""POS Tagger

$Id: tag.py 100555 2009-05-30 15:26:12Z srichter $
"""
import sys
import os
import re
import re2              # Use re2 if we get killed by exponential regex evaluation.
                        # This used to happen with an old TERM_SPEC regex,
                        # and now will generally timeout if there are 300 dots in a row.
                        # DOWNLOAD AT: https://github.com/axiak/pyre2
                        # (see Python bug http://bugs.python.org/issue1662581)
re2.set_fallback_notification(re2.FALLBACK_WARNING)

# Timeout re requests
from timeout import timeout, TimeoutError

import zope.interface

from topia.termextract import interfaces

ORIG_TERM_SPEC = re.compile('([^a-zA-Z]*)([a-zA-Z-\.]*[a-zA-Z])([^a-zA-Z]*[a-zA-Z]*)')
# Modified by jpt
# regex [^\W\d_] = [a-zA-Z] with Unicode alphabetic character.
# See: http://stackoverflow.com/questions/2039140/python-re-how-do-i-match-an-alpha-character/2039476#2039476
TERM_SPEC = re.compile('([\W\d_]*)(([^\W\d_]?[-\.]?)*[^\W\d_])([\W\d_]*[^\W\d_]*)', re.UNICODE)
# TERM_SPEC2 is faster (because it uses re2) but it DOESN'T handle Unicode
# correctly (https://github.com/axiak/pyre2/issues/5). So only use re2 if
# re times out.
TERM_SPEC2 = re2.compile('([\W\d_]*)(([^\W\d_]?[-\.]?)*[^\W\d_])([\W\d_]*[^\W\d_]*)', re2.UNICODE)
DATA_DIRECTORY = os.path.join(os.path.dirname(__file__), 'data')


def correctDefaultNounTag(idx, tagged_term, tagged_terms, lexicon):
    """Determine whether a default noun is plural or singular."""
    term, tag, norm = tagged_term
    if tag == 'NND':
        if term.endswith('s'):
            tagged_term[1] = 'NNS'
            tagged_term[2] = term[:-1]
        else:
            tagged_term[1] = 'NN'

def verifyProperNounAtSentenceStart(idx, tagged_term, tagged_terms, lexicon):
    """Verify that noun at sentence start is truly proper."""
    term, tag, norm = tagged_term
    if (tag in ('NNP', 'NNPS') and
        (idx == 0 or tagged_terms[idx-1][1] == '.')):
        lower_term = term.lower()
        lower_tag = lexicon.get(lower_term)
        if lower_tag in ('NN', 'NNS'):
            tagged_term[0] = tagged_term[2] = lower_term
            tagged_term[1] = lower_tag

def determineVerbAfterModal(idx, tagged_term, tagged_terms, lexicon):
    "Determine the verb after a modal verb to avoid accidental noun detection."
    term, tag, norm = tagged_term
    if tag != 'MD':
        return
    len_terms = len(tagged_terms)
    idx += 1
    while idx < len_terms:
        if tagged_terms[idx][1] == 'RB':
            idx += 1
            continue
        if tagged_terms[idx][1] == 'NN':
            tagged_terms[idx][1] = 'VB'
        break

def normalizePluralForms(idx, tagged_term, tagged_terms, lexicon):
    term, tag, norm = tagged_term
    if tag in ('NNS', 'NNPS') and term == norm:
        # Plural form ends in "s"
        singular = term[:-1]
        if (term.endswith('s') and
            singular in lexicon):
            tagged_term[2] = singular
            return
        # Plural form ends in "es"
        singular = term[:-2]
        if (term.endswith('es') and
            singular in lexicon):
            tagged_term[2] = singular
            return
        # Plural form ends in "ies" (from "y")
        singular = term[:-3]+'y'
        if (term.endswith('ies') and
            singular in lexicon):
            tagged_term[2] = singular
            return


class Tagger(object):
    zope.interface.implements(interfaces.ITagger)

    rules = (
        correctDefaultNounTag,
        verifyProperNounAtSentenceStart,
        determineVerbAfterModal,
        normalizePluralForms,
        )

    def __init__(self, language='english'):
        self.language = language

    def initialize(self):
        """See interfaces.ITagger"""
        filename = os.path.join(DATA_DIRECTORY, '%s-lexicon.txt' %self.language)
        file = open(filename, 'r')
        self.tags_by_term = dict([line[:-1].split(' ')[:2] for line in file])
        file.close()

    def tokenize(self, text):
        """See interfaces.ITagger.
        Split is true if this token originally had a space after it."""
        split = []
        terms = []
        for term in re.split('\s', text):
            # If the term is empty, skip it, since we probably just have
            # multiple whitespace cahracters.
            if term == '':
                continue
            # Now, a word can be preceded or succeeded by symbols, so let's
            # split those out
            @timeout(1)
            def slow_match(term):
                return TERM_SPEC.search(term)
            try:
                match = slow_match(term)
            except TimeoutError:
                import sys
                print >> sys.stderr, "TIMEOUT when running regex on %s (%s).\nRe-running with re2 (sorry if you have Unicode, this will tokenize it wrong)" % (term.encode("utf-8"), repr(term))
                match = TERM_SPEC2.search(term)
            if match is None:
                terms.append(term)
                split.append(True)
                continue

            # In the new TERM_SPEC, skip the third regex group
            # -jpt
#            import sys
#            print >> sys.stderr, "match groups =", repr(match.groups()), term.encode("utf-8")
            match_groups = match.groups()[0], match.groups()[1], match.groups()[3]
            for subTerm in match_groups:
                if subTerm != '':
                    terms.append(subTerm)
                    split.append(False)
            split[-1] = True
        return split, terms

    def tag(self, terms):
        """See interfaces.ITagger"""
        tagged_terms = []
        # Phase 1: Assign the tag from the lexicon. If the term is not found,
        # it is assumed to be a default noun (NND).
        for term in terms:
            tagged_terms.append(
                [term, self.tags_by_term.get(term, 'NND'), term])
        # Phase 2: Run through some rules to improve the term tagging and
        # normalized form.
        for idx, tagged_term in enumerate(tagged_terms):
            for rule in self.rules:
                rule(idx, tagged_term, tagged_terms, self.tags_by_term)
        return tagged_terms

    def __call__(self, text):
        """See interfaces.ITagger"""
        split, terms = self.tokenize(text)
        return split, self.tag(terms)

    def __repr__(self):
        return '<%s for %s>' %(self.__class__.__name__, self.language)

if __name__ == "__main__":
    t = u"Geçerlilik....................................................................."
#    t = "CEDAR RAPIDS, Iowa, Jul 16, 2010 (BUSINESS WIRE) -- --Overall full year guidance updated with EPS of about $3.50 and operating cash flow increased to about $700 million \n Rockwell Collins, Inc. /quotes/comstock/13*!col/quotes/nls/col (COL 56.06, -0.07, -0.12%)  today reported net income of $142 million for its fiscal year 2010 third quarter ended June 30, 2010, a decrease of $3 million, or 2%, from fiscal year 2009 third quarter net income of $145 million. Earnings per share was $0.89, a decrease of $0.02 from earnings per share of $0.91 for the same period in 2009. \n Third quarter 2010 sales increased $130 million, or 12%, to $1.214 billion compared to sales of $1.084 billion for the same period a year ago. Organic revenue growth was 8%, while incremental sales from the acquisitions of DataPath and Air Routing contributed $43 million, or 4%, to total revenues. Total segment operating margins were 18.8% for the third quarter of 2010 compared to 21.5% for the third quarter of 2009. \n Cash provided by operating activities for the first nine months of 2010 totaled $440 million compared to the $381 million reported for the same period last year. The increase resulted primarily from lower payments for employee incentive compensation. \n \"Despite continued uncertainty in the global economic recovery our business continued to perform very well relative to the expectations we communicated in September, 2009,\" said Rockwell Collins Chairman, President and Chief Executive Officer Clay Jones. \"Both business segments posted year-over-year increases in revenue for the first time since the fourth quarter of fiscal year 2008 as the commercial markets show solid improvement and our defense business continues its steady progress.\" \n Mr. Jones went on to state, \"Given the benefits of the balance and diversification of our businesses and the strength of our shared services operating model, we are updating several pieces of our overall guidance. Despite higher accruals now expected for employee incentive compensation and the absence of the Federal R&D Tax Credit, we are confident enough in our overall performance to tighten our EPS and increase our operating cash flow guidance.\" \n Following is a discussion of fiscal year 2010 third quarter sales and earnings for each business segment. \n Government Systems \n Government Systems, which provides communication and electronic systems, products and services for airborne and surface applications to the U.S. Department of Defense, other government agencies, civil agencies, defense contractors and foreign ministries of defense, achieved third quarter sales of $754 million, an increase of $103 million, or 16%, compared to the $651 million reported for the same period last year. Incremental sales from the May 29, 2009 acquisition of DataPath contributed $34 million of revenue growth. \n Airborne solutions sales increased $8 million, or 2%, to $460 million as higher revenues related to tanker and transport aircraft programs were partially offset by lower revenues on fighter jet programs. Surface solutions sales increased $95 million, or 48%, to $294 million. DataPath sales contributed $34 million to acquisition-related revenue growth, while organic sales increased $61 million primarily due to revenues related to a vehicle electronics integration program with the California Highway Patrol and higher sales from a number of international programs. \n Government Systems third quarter operating earnings decreased 3% to $153 million, resulting in an operating margin of 20.3%, compared to operating earnings of $158 million, or an operating margin of 24.3%, for the same period last year. The decrease in operating earnings was primarily the result of higher employee compensation and pension expenses, transition costs related to the San Jose, California facility shut-down and higher research and development expenditures, which were partially offset by the benefit of a favorable contract adjustment, reduction in warranty expenses and incremental earnings on higher revenues. Operating margin was also negatively impacted by lower margins on DataPath revenues. \n Commercial Systems \n Commercial Systems, which provides aviation electronics systems, products and services to air transport, business and regional aircraft manufacturers and airlines worldwide, achieved third quarter sales of $460 million, an increase of $27 million, or 6%, compared to sales of $433 million reported for the same period last year. Incremental sales from the acquisition of Air Routing contributed $9 million of revenue growth. \n Sales related to aircraft original equipment manufacturers increased $29 million, or 14%, to $240 million primarily due to higher sales to Boeing resulting from the absence of last year's post-labor strike inventory rationalization and an increase in 787 revenues, and higher equipment sales for Chinese turbo-prop aircraft. Aftermarket sales increased $11 million, or 6%, to $210 million. Air Routing sales cont"
#    t = u'Enter your email address:\n\nDelivered by FeedBurner\nLock On Flaming Cliffs 2 PC -SKIDROW is available on a new fast direct download service with over 2,210,000 Files to choose from.Download anything with more then 1000+ Kb/s downloading speed.Signup process takes just 10 sec to go.Signup today and enjoy the speed !\n-------------------- Similar Software to (Lock On Flaming Cliffs 2 PC -SKIDROW): History Channel Battle For The PacificThe Scourge Project Episode 1 and 2 Update 2-SKIDROWStorm Over the Pacific v1.02 Update-SKIDROWTom Clancys Splinter Cell Conviction v1.03 Update-SKIDROWThe Witcher - Enhanced Edition ISO'
#    t = "------------------------------"
    tok = Tagger()
    print zip(*tok.tokenize(t))

#    import common.mongodb
#    collection = common.mongodb.collection(DATABASE="spiderdmoz", name="docs")
#    for doc in common.mongodb.findall(collection, matchfn=lambda doc: True):
#        tok.tokenize(doc["text"])


#    tok.initialize()
#    print tok.tag(tok.tokenize(t))
