#!/usr/bin/env python3
# -*- coding: utf-8, vim: expandtab:ts=4 -*-

"""
The program recognizes both Hungarian quantitative and qualitative meters.
It categorizes poems as dactylic, anapestic, trochaic, or iambic, and provides
a regularity score between 0 and 1, indicating how consistently the rhythm of
the poem follows the recognized abstract quantitative meter. In addition, the
program identifies qualitative meters that have an "aaaa..." or "abab..."
structure.

Using the program, it is possible to retrieve poems that have both quantitative
and qualitative meters simultaneously.

The input to the program is the level3_without_meter XML files from the ELTE
Poetry Corpus, which contain syllable length annotations for each line. In these
annotations, character "0" indicates short syllables, and "1" indicates
long syllables. The program converts these to "1" (short syllables) and "2" (long
syllables), and uses the converted values to compute the number of moras of the
feet.

Using the program:
Place the level3_without_meter folder containing the TEI XML files in the same
directory as the program code (poetry_corpus_level3_meter.py). The contents of
the level3_without_meter folder should follow this structure: level3_without_meter/author/file,
e.g., level3_without_meter/Kosztolanyi_00753/Kosztolanyi_00753_0001.xml
In the level3_without_meter folder inside the hunpoem_meter_analyzer directory, the
files are already organized in this structure. If you want to test the program, you do
not need to change anything. Naturally, the poems can also be grouped into folders based
on other criteria besides authors.

The program has two main functions, each designed for different purposes (at the end of
the script, uncomment the function call you want to use):

annotate_level3(0, 0.75, 6) function:
The program annotates the TEI XML files in the level3_without_meter folder with features
of both quantitative and qualitative meters. These TEI XML files are located in the
hun_poem_meter_analyzer directory. The program copies the newly annotated files with meter
into the newly created 'level3' folder. The annotations are placed in the @met attribute
of the <div> element in the TEI XML files.
In the case of poems with qualitative meter, the numbers in the annotation indicate the
syllable count of the bars. If the odd and even lines have different bar structures, the
'_' character separates the bar structures of the odd and even lines.

get_tsv() function:
The program analyzes the metrical features of the TEI XML files in the level3_without_meter
folder and outputs the results to the screen in TSV format.

When running the get_tsv() function, you can choose from the four functions below:
1. meter_quantitative() : For each author, it outputs the frequencies of poems with
different types of quantitative meters in TSV format.
2. meter_qualitative() : For each author, it outputs the frequencies of poems with
qualitative meter in TSV format.
3 meter_qualitative_frequency() : It outputs frequency lists of the different types of
qualitative meters for each author.
4. meter_simultan() : For each author, it outputs the frequencies of poems having
quantitative and qualitative meters at the same time in TSV format.
5. annotate_level3(0, 0.75, 6) : From the get_tsv() function, it is possible to call the
function annotating the TEI XML files in the level3_without_meter folder with features of
both quantitative and qualitative meters.
"""


from statistics import mean, median
import os
import xml.etree.ElementTree as ET
from xml.dom import minidom
from datetime import date

ET.register_namespace("", "http://www.tei-c.org/ns/1.0")

TEI_NAMESPACE = {"ns": "http://www.tei-c.org/ns/1.0"}


# Quantitative meter:


def pentameter(rhythm, words):
	"""
	It tries to analyze a line as a pentameter.
	:param rhythm: string representing the rhythm of the line, consisting of
	"1" and "2" characters ("1" = short syllable, "2" = long syllable).
	:param words: list containing the words of the line.
	:return: list whose elements are metrical feet consisting of 1 and 2 characters.
	If the line could not be analyzed as a pentameter, the output is [0].
	"""
	vowels = "aáeéiíoóöőuúüűAÁEÉIÍOÓÖŐUÚÜŰ"
	words_num_syllable = []
	for word in words:
		num_syllable = 0
		for char in word:
			if char in vowels:
				num_syllable += 1
		words_num_syllable.append(num_syllable)
	words_first_syllable = []
	sum = 0
	for num_syllable in words_num_syllable:
		sum += num_syllable
		words_first_syllable.append(sum)

	pentameter_caesura = {"21121122112112": 7,
						  "21121122112111": 7,
						  "2112222112112": 6,
						  "2112222112111": 6,
						  "2221122112112": 6,
						  "2221122112111": 6,
						  "222222112112": 5,
						  "222222112111": 5}
	pentameter_feet = {"21121122112112": ["211", "211", "211", "211"],
					   "21121122112111": ["211", "211", "211", "211"],
					   "2112222112112": ["211", "22", "211", "211"],
					   "2112222112111": ["211", "22", "211", "211"],
					   "2221122112112": ["22", "211", "211", "211"],
					   "2221122112111": ["22", "211", "211", "211"],
					   "222222112112": ["22", "22", "211", "211"],
					   "222222112111": ["22", "22", "211", "211"]}
	feet = [0]
	if rhythm in pentameter_caesura:
		if pentameter_caesura[rhythm] in words_first_syllable:
			feet = pentameter_feet[rhythm]
	return feet


def split_line_mora4_feet(rhythm):
	"""
	It tries to split a string consisting of "1" and "2" characters, representing
	the rhythm of a line, into a list containing four-mora metrical feet.
	:param rhythm: string representing the rhythm of the line, consisting of
	"1" and "2" characters ("1" = short syllable, "2" = long syllable).
	:return:  list containing the metrical feet of the line split into four-mora feet.
	(e.g., ["211", "211", "22"]). If the line cannot be split into four-mora metrical
	feet, the output will be: [0].
	"""
	feet = []
	foot = []
	for serial, syll in enumerate(rhythm):
		foot.append(int(syll))
		sum_foot = sum(foot)
		if sum_foot == 4:
			foot = "".join([str(i) for i in foot])
			feet.append(foot)
			foot = []
		elif sum_foot > 4:
			break

	# The last short syllable can also be interpreted as a long syllable, and the last
	# long syllable can be interpreted as a short syllable.
	if len(rhythm) > 1 and serial == len(rhythm)-1:
		if foot == [1, 1, 1]:
			feet.append("112")
		elif foot == [2, 1, 2]:
			feet.append("211")
		elif foot == [2, 1]:
			feet.append("22")
		elif foot == [1, 1, 1, 2]:
			feet.append("1111")
		elif foot in [[1, 1],[1, 2], [1, 2, 2]]:
			feet = [0]
		else:
			pass
	else:
			feet = [0]
	return feet


def score_anapestic_and_dactylic(feet, checked_meter4):
	"""
	It tests the line, divided into four-mora metrical feet, for anapestic or dactylic
	meter, resulting in a score between 0 and 1, which represents the regularity score
	for the tested meter.
	:param feet: list whose elements are four-mora metrical feet consisting of "1" and "2"
	characters.
	:param checked_meter4: string indicating the tested meter ("anapestic" or "dactylic").
	:return: float between 0 and 1, representing the regularity score for the tested meter.
	"""
	score = 0
	if feet != [0]:
		num_feet = len(feet)
		dactyl = feet.count("211")
		anapest = feet.count("112")
		spondee = feet.count("22")
		proceleusmatic = feet.count("1111")
		amphibrach = feet.count("121")
		if amphibrach == 0:
			if checked_meter4 == "dactylic":
				score = ((dactyl * 4) + (spondee * 2) + (proceleusmatic * 1)) / (num_feet * 4)
			elif checked_meter4 == "anapestic":
				score = ((anapest * 4) + (spondee * 2) + (proceleusmatic * 1)) / (num_feet * 4)
	return score


def split_line_syll2_feet(rhythm):
	"""
	It splits a string representing the rhythm of a line, consisting of "1" and
	"2" characters, into two syllable metrical feet.
	:param rhythm: string representing the rhythm of the line, consisting of "1" and "2"
	characters ("1" = short syllable, "2" = long syllable).
	:return: list whose elements are the metrical feet of the line split into two syllables
	(e.g., ["11", "12", "22", "12"]).
	"""
	feet = []
	foot = ""
	for syll in rhythm:
		foot += syll
		if len(foot) == 2:
			feet.append(foot)
			foot = ""
	if len(rhythm) % 2 == 0 and len(feet) != 0:
		if feet[-1] == "11":
			feet = feet[:-1] + ["12"]
		elif feet[-1] == "22":
			feet = feet[:-1] + ["21"]
		else:
			pass
	return feet


def score_iambic_and_trochaic(feet, checked_meter2):
	"""
	It tests the line, split into metrical feet of two syllables, for iambic or trochaic
	meter, resulting in a score between 0 and 1, which represents the regularity score for
	the tested meter.
	:param feet: list whose elements are the metrical feet of the line split into two
	syllables (e.g., ["11", "12", "22", "12"]).
	:param checked_meter2: string indicating the tested meter ("iambic" or "trochaic")
	:return: float between 0 and 1, representing the regularity score for the tested meter.
	"""
	score = 0
	num_feet = len(feet)
	iamb = feet.count("12")
	trochee = feet.count("21")
	spondee = feet.count("22")
	pyrrhic = feet.count("11")
	if checked_meter2 == "iambic":
		if len(feet) > 0 and feet[-1] == "12":
			score = ((iamb * 4) + (spondee * 2) + (pyrrhic * 1)) / (num_feet * 4)
	elif checked_meter2 == "trochaic":
		if len(feet) > 0 and feet[-1] == "21":
			score = ((trochee * 4) + (spondee * 2) + (pyrrhic * 1)) / (num_feet * 4)
	return score


def check_meter_line(rhythm, words, checked_meter):
	"""
	Main function that tests a meter (anapestic, dactylic, iambic, or trochaic) on
	a line and outputs a regularity score between 0 and 1.
	:param rhythm: string representing the rhythm of the line, consisting of "1" and "2"
	characters ("1" = short syllable, "2" = long syllable).
	:param words: list containing the words of the line.
	:param checked_meter: string indicating the tested meter ("anapestic", "dactylic",
	"iambic" or "trochaic").
	:return: float between 0 and 1, representing the regularity score for the tested meter.
	"""
	score = 0
	if checked_meter == "anapestic":
		feet = split_line_mora4_feet(rhythm)
		score = score_anapestic_and_dactylic(feet, checked_meter)
	elif checked_meter == "dactylic":
		feet = pentameter(rhythm, words)
		if feet == [0]:
			feet = split_line_mora4_feet(rhythm)
		score = score_anapestic_and_dactylic(feet, checked_meter)
	elif checked_meter in ["iambic", "trochaic"]:
		feet = split_line_syll2_feet(rhythm)
		score = score_iambic_and_trochaic(feet, checked_meter)
	else:
		print("The input meter is wrong. Only anapestic, dactylic, iambic or trochaic meter can be given.")
	return score


def test_meter_poem(poem_rhythms, poem_words, checked_meter, threshold_score):
	"""
	Main function that tests a given meter (anapestic, dactylic, iambic, or trochaic) on
	the poem and outputs a regularity score between 0 and 1.
	:param poem_rhythms: list containing the rhythm of the poem's lines as list elements
	consisting of "1" and "2" characters. (e.g., ["121112", "2212", "11112222", "22221"]
	- "1" = short syllable, "2" = long syllable)
	:param poem_words: list containing the words of lines as lists.
	:param checked_meter: string indicating the tested meter ("anapestic", "dactylic",
	"iambic" or "trochaic").
	:param threshold_score: float between 0 and 1, indicating the threshold for the poem's
	regularity score.
	:return: list, whose first element is the tested meter ("anapestic", "dactylic", "iambic",
	"trochaic" or "under_threshold"), and its second element is the regularity score for
	the tested meter (float). If the poem's regularity score for the tested meter does
	not exceed the threshold, the output will be "under_threshold."
	"""
	score_sum = 0
	if checked_meter == "anapestic":
		for rhythm in poem_rhythms:
			feet = split_line_mora4_feet(rhythm)
			score_line = score_anapestic_and_dactylic(feet, checked_meter)
			score_sum += score_line
	elif checked_meter == "dactylic":
		for serial_num, rhythm in enumerate(poem_rhythms):
			feet = pentameter(rhythm, poem_words[serial_num])
			if feet == [0]:
				feet = split_line_mora4_feet(rhythm)
			score_line = score_anapestic_and_dactylic(feet, checked_meter)
			score_sum += score_line
	elif checked_meter in ["iambic", "trochaic"]:
		for rhythm in poem_rhythms:
			feet = split_line_syll2_feet(rhythm)
			score_line = score_iambic_and_trochaic(feet, checked_meter)
			score_sum += score_line
	else:
		print("The input meter is wrong. Only anapestic, dactylic, iambic "
				  "or trochaic meter can be given.")
	score_poem = score_sum / len(poem_rhythms)
	if score_poem <= threshold_score:
		checked_meter = "under_threshold"
	return [checked_meter, score_poem]


def test_all_meters(poem_rhythms, poem_words, threshold_score):
	"""
	Main function that tests all four meters (anapestic, dactylic, iambic, trochaic) on
	a poem and outputs the one with the highest regularity score, along with the score.
	:param poem_rhythms: list containing the rhythm of the poem's lines as list elements
	consisting of "1" and "2" characters. (e.g., ["121112", "2212", "11112222", "22221"]
	- "1" = short syllable, "2" = long syllable)
	:param poem_words: list containing the words of lines as lists.
	:param threshold_score: float between 0 and 1, indicating the threshold for the poem's
	regularity score.
	:return: list, whose first element is the tested meter ("anapestic", "dactylic", "iambic",
	"trochaic" or "under_threshold"), and its second element is the regularity score for
	the tested meter (float). If the poem's regularity score for the tested meter does
	not exceed the threshold, the output will be "under_threshold." If two or more meters result
	in the same highest score, the output will be "equal."
	"""
	meters = ["anapestic", "dactylic", "iambic", "trochaic"]
	meter = ""
	score = 0
	equal = False
	for checked_meter in meters:
		meter_and_score = test_meter_poem(poem_rhythms, poem_words, checked_meter, threshold_score)
		score_poem = meter_and_score[1]
		if score_poem > score:
			score = score_poem
			meter = meter_and_score[0]
			equal = False
		elif score_poem == score:
			meter = meter_and_score[0]
			equal = True
	if meter != "under_threshold" and equal == True:
		meter = "equal"
	return [meter, score]


# Qualitative meter:


def get_stressed_syllables_in_line(line_words):
	"""
	It outputs the stressed and unstressed syllables of a line.
	:param line_words: two-dimensional list whose elements are the words of the line.
	(It is two-dimensional because compound words can also be segmented into their
	components and the segments can be provided to the function; in this case, each word
	is an embedded list, split into compound parts as list elements.)
	:return: string consisting of "1" and "0" characters, representing the word-initial/stressed
	and non-word-initial/unstressed syllables of the line ("1" = word-initial syllable,
	"0" = non-word-initial syllable).
	"""
	vowels = "aáeéiíoóöőuúüűAÁEÉIÍOÓÖŐUÚÜŰ"
	rhythm_line = ""
	for item in line_words:
		for word in item:
			start_word = True
			for char in word:
				if char in vowels:
					if start_word == True:
						rhythm_line += "1"
						start_word = False
					else:
						rhythm_line += "0"
	return rhythm_line


def get_line_length(lines, threshold_qual):
	"""
	Based on a list of strings representing the word-initial and non-word-initial syllables
	of the lines, it determines the typical syllable length of the lines, if such typical
	length exists.
	:param lines: list containing strings of "1" and "0" characters, representing the
	word-initial and non-word-initial syllables of the poem's lines.
	:param threshold_qual: float, a number between 0 and 1, by which the line number should
	be multiplied. If the frequency of the most common syllable count found for the lines
	is greater than or equal to the result of the multiplication, the function's output
	will not be False, but the most common syllable count found.
	:return: integer indicating the syllable count of the lines. If there is no specific
	syllable count characteristic of the entire poem, the output will be a boolean value
	of False.
	"""
	syllable_nums = [len(line) for line in lines]
	max_syll_num_frequency = 0
	for num in syllable_nums:
		syll_num_frequency = syllable_nums.count(num)
		if syll_num_frequency > max_syll_num_frequency:
			max_syll_num_frequency = syll_num_frequency
	line_length = [num for num in syllable_nums if syllable_nums.count(num) == max_syll_num_frequency]
	line_length = list(dict.fromkeys(line_length))
	if len(line_length) == 1 and max_syll_num_frequency >= len(lines) * threshold_qual:
		line_length = line_length[0]
	else:
		line_length = False
	return line_length


def conclude_meter_poem(lines, line_length, threshold_qual, max_measure):
	"""
	It determines whether the lines with a characteristic syllable length have a
	qualitative meter and outputs the syllable count of the bars.
	There are two restrictions for determining the boundaries of bars:
		(1) The second syllable position cannot be the beginning of a new bar.
		(2) A certain proportion of the lines (as specified by the percentage parameter)
		must have a word-initial syllable in the given syllable position.
	:param lines: list containing strings of "1" and "0" characters, representing the
	word-initial and non-word-initial syllables of the lines. ("1" = word-initial syllable,
	"0" = non-word-initial syllable).
	:param line_length: integer indicating the characteristic syllable count of the lines.
	:param threshold_qual: float, a number between 0 and 1, by which the function multiplies
	the line number. If the stress score found for a given syllable position is greater than
	or equal to the result of the multiplication, then the given syllable is the first
	syllable of a new bar.
	:param max_measure: integer indicating the maximum possible syllable count of the bars.
	:return: string containing the syllable count of the identified bars. If no bars could
	be identified, or if any of the bars have a syllable count greater than the specified
	maximum possible syllable count, the output will be a boolean value of False.
	Note: A line can be a single bar if the line is not longer than the specified
	maximum possible syllable count of a bar.
	"""
	syllable_scores = []
	for syllable in range(line_length):
		score = 0
		for line in lines:
			if len(line) == line_length:
				score += int(line[syllable])
			else:
				pass
		syllable_scores.append(score)
	# The following line contains the restriction regarding the second syllable position and the bar start:
	meter = [score_syll[0] for score_syll in enumerate(syllable_scores)
			 if score_syll[0] != 1 and score_syll[1] >= len(lines) * threshold_qual]
	# The position numbers indicating the bar starts are converted into the syllable counts of the bars:
	meter1 = []
	for i, acc_syll in enumerate(meter):
		if i < len(meter) - 1:
			meter1.append(meter[i+1] - acc_syll)
		else:
			meter1.append(line_length - acc_syll)
	meter1 = tuple(meter1)
	if len(meter) == 0:
		meter1 = False
	for num_syll in meter1:
		if num_syll > max_measure: # The condition regarding the maximum possible syllable count of the bars.
			meter1 = False
			break
	return meter1


def analyse_poem_meter(rhythm_poem, threshold_qual, max_measure):
	"""
	It determines whether the poem have a qualitative meter and outputs the syllable
	count of the bars. It can recognize aaaa... and abab... meter structures.
	:param rhythm_poem: list containing strings of "1" and "0" characters, representing
	the word-initial and non-word-initial syllables of the lines. ("1" = word-initial
	syllable, "0" = non-word-initial syllable).
	:param threshold_qual: float, a number between 0 and 1, which specifies what percentage
	of the lines must meet the basic syllable count, and what percentage of the lines must
	have a word-initial syllable in a given syllable position for the program to determine
	a bar start.
	:param max_measure: integer indicating the maximum possible syllable count of the bars.
	:return: string indicating the syllable count of the identified bars. If no bars could
	be identified, or if any of the bars have a syllable count greater than the specified
	maximum possible syllable count, the output will be a boolean value of False.
	Note: A line can be a single bar if the line is not longer than the specified
	maximum possible syllable count of a bar.
	"""
	meter = False
	lines = []
	odd_lines = []
	even_lines = []
	for lg in rhythm_poem:
		for index, l in enumerate(lg):
			lines.append(l)
			if (index + 1) % 2 == 0:
				even_lines.append(l)
			else:
				odd_lines.append(l)
	line_length = get_line_length(lines, threshold_qual)
	if line_length and len(lines) > 1:	# Single-line poems cannot have a qualitative meter.
		meter = conclude_meter_poem(lines, line_length, threshold_qual, max_measure)
		if meter == False and len(lines) > 3:	# For a qualitative meter, at least two even and two odd lines are needed.
			odd_line_length = get_line_length(odd_lines, threshold_qual)
			even_line_length = get_line_length(even_lines, threshold_qual)
			if odd_line_length and even_line_length:
				meter_odd = conclude_meter_poem(odd_lines, odd_line_length, threshold_qual, max_measure)
				meter_even = conclude_meter_poem(even_lines, even_line_length, threshold_qual, max_measure)
				if meter_odd and meter_even:
					meter = (meter_odd, meter_even)
	elif len(lines) > 3: # For a qualitative meter, at least two even and two odd lines are needed.
		odd_line_length = get_line_length(odd_lines, threshold_qual)
		even_line_length = get_line_length(even_lines, threshold_qual)
		if odd_line_length and even_line_length:
			meter_odd = conclude_meter_poem(odd_lines, odd_line_length, threshold_qual, max_measure)
			meter_even = conclude_meter_poem(even_lines, even_line_length, threshold_qual, max_measure)
			if meter_odd and meter_even:
				meter = (meter_odd, meter_even)
	return meter


# Main code:

# Processing one file:

def process_one_file_meter_quantitative(folder, teixml, threshold_score, directory):
	"""
	Runs the test_all_meters() function, which recognizes quantitative meters, on a
	TEI XML file containing a poem. This function calls the other functions.
	:param folder: string, which is the name of the directory containing the XML file of
	the poem.
	:param teixml: string, which is the name of the XML file containing the poem.
	:param threshold_score: float between 0 and 1, representing the threshold for the poem's
	regularity score.
	:param directory: string, which is the name of the folder containing the TEI XML files.
	:return: list, whose first element is the meter recognized ("anapestic", "dactylic",
	"iambic", "trochaic" or "under_threshold"), and its second element is the regularity score
	for the recognized meter (float). If the poem's regularity score for all meters does
	not exceed the threshold, the output will be "under_threshold." If two or more meters
	result in the same highest score, the output will be "equal".
	"""
	tree = ET.parse(f"{directory}/{folder}/{teixml}")
	root = tree.getroot()
	poem_rhythms = [l_tag.get('real') for l_tag in root.iterfind(".//ns:l", TEI_NAMESPACE)]
	poem_rhythms = [rhythm.replace("1", "2") for rhythm in poem_rhythms]
	poem_rhythms = [rhythm.replace("0", "1") for rhythm in poem_rhythms]
	poem_words = [[token.text for token in l_tag if token.tag == "{http://www.tei-c.org/ns/1.0}w"]
				  for l_tag in root.iterfind(".//ns:l", TEI_NAMESPACE)]
	meter = test_all_meters(poem_rhythms, poem_words, threshold_score)
	return meter


def process_one_file_meter_qualitative(folder, teixml, threshold_qual, max_measure, directory):
	"""
	Runs the analyse_poem_meter() function, which recognizes qualitative meters, on a
	TEI XML file containing a poem. This function calls the other functions.
	:param folder: string, which is the name of the directory containing the XML file of
	the poem.
	:param teixml: string, which is the name of the XML file containing the poem.
	:param threshold_qual: float, a number between 0 and 1, which specifies what percentage
	of the lines must meet the basic syllable count, and what percentage of the lines must
	have a word-initial syllable in a given syllable position for the program to determine
	a bar start.
	:param max_measure: integer indicating the maximum possible syllable count of the bars.
	:param directory: string, which is the name of the folder containing the TEI XML files.
	:return: string indicating the syllable count of the identified bars. If no bars could
	be identified, or if any of the bars have a syllable count greater than the specified
	maximum possible syllable count, the output will be a boolean value of False.
	"""
	tree = ET.parse(f"{directory}/{folder}/{teixml}")
	root = tree.getroot()
	rhythm_poem = []
	for lg_tag in root.iterfind(".//ns:lg", TEI_NAMESPACE):
		rhythm_lg = []
		for l_tag in lg_tag.iterfind(".//ns:l", TEI_NAMESPACE):
			# Here line_words is a two-dimensional list because the program has a version
			# that splits words into their compound parts, and the components of compound
			# words can be represented as inner lists within the main list.
			line_words = [[token.text] for token in l_tag if token.tag == "{http://www.tei-c.org/ns/1.0}w"]
			rhythm_line = get_stressed_syllables_in_line(line_words)
			rhythm_lg.append(rhythm_line)
		rhythm_poem.append(rhythm_lg)
	meter = analyse_poem_meter(rhythm_poem, threshold_qual, max_measure)
	return meter


# Main functions:


def meter_quantitative(threshold_score, directory):
	"""
	It outputs the frequencies of different types of quantitative meter poems for each
	author in TSV format.
	:param threshold_score: float between 0 and 1, indicating the threshold for the poem's
	regularity score.
	:param directory: string, which is the name of the folder containing the TEI XML files.
	"""
	print("")
	print("Author", "All_poems", "Quantitative_poems", "Quantitative_ratio",
		  "Anap_all", "Anap_ratio", "Anap_mean", "Anap_median",
		  "Dact_all", "Dact_ratio", "Dact_mean", "Dact_median",
		  "Iamb_all", "Iamb_ratio", "Iamb_mean", "Iamb_median",
		  "Troch_all", "Troch_ratio", "Troch_mean", "Troch_median", sep="\t")
	folders = os.listdir(directory)
	folders.sort()
	for folder in folders:
		all_poem = 0
		metric_poem = 0
		dict_meter_scores = {"anapestic": [], "dactylic": [], "iambic": [], "trochaic": []}
		files = os.listdir(f"{directory}/{folder}")
		for teixml in files:
			all_poem += 1
			meter_quantitative = process_one_file_meter_quantitative(folder, teixml, threshold_score, directory)
			if meter_quantitative[0] != "under_threshold" and meter_quantitative[0] != "equal":
				metric_poem += 1
				dict_meter_scores[meter_quantitative[0]].append(meter_quantitative[1])
		metric_ratio = round(metric_poem / all_poem, 2)
		dict_meter_data = {"anapestic": [], "dactylic": [], "iambic": [], "trochaic": []}
		for meter_type in dict_meter_data:
			if len(dict_meter_scores[meter_type]) > 0:
				dict_meter_data[meter_type].extend([len(dict_meter_scores[meter_type]),
				round(len(dict_meter_scores[meter_type]) / metric_poem, 2),
				round(mean(dict_meter_scores[meter_type]), 2),
				round(median(dict_meter_scores[meter_type]), 2)])
			else:
				dict_meter_data[meter_type].extend([0, 0, "none", "none"])

		print(folder, all_poem, metric_poem, metric_ratio,
			  *sum([dict_meter_data[meter] for meter in ["anapestic", "dactylic", "iambic",
														 "trochaic"]], []), sep="\t")


def meter_qualitative(threshold_qual, max_measure, directory):
	"""
	It outputs the frequencies of qualitative meter poems for each author in TSV format.
	:param threshold_qual: a float, a number between 0 and 1, which specifies what percentage
	of the lines must meet the basic syllable count, and what percentage of the lines must
	have a word-initial syllable in a given syllable position for the program to determine
	a bar start.
	:param max_measure: integer indicating the maximum possible syllable count of the bars.
	:param directory: string, which is the name of the folder containing the TEI XML files.
	"""
	print("")
	print("Author", "All_poems", "Qualitative_poems", "Qualitative_ratio", sep="\t")
	folders = os.listdir(directory)
	folders.sort()
	for folder in folders:
		all_poem = 0
		metric_poem = 0
		files = os.listdir(f"{directory}/{folder}")
		for teixml in files:
			all_poem += 1
			meter_qualitative = process_one_file_meter_qualitative(folder, teixml, threshold_qual,
																   max_measure, directory)
			if meter_qualitative != False:
				metric_poem += 1
		metric_ratio = round(metric_poem / all_poem, 2)
		print(folder, all_poem, metric_poem, metric_ratio, sep="\t")


def meter_qualitative_frequency(threshold_qual, max_measure, directory):
	"""
	It outputs frequency lists of the different types of qualitative meters for each author.
	:param threshold_qual: a float, a number between 0 and 1, which specifies what percentage
	of the lines must meet the basic syllable count, and what percentage of the lines must
	have a word-initial syllable in a given syllable position for the program to determine
	a bar start.
	:param max_measure: integer indicating the maximum possible syllable count of the bars.
	:param directory: string, which is the name of the folder containing the TEI XML files.
	"""
	print("")
	print("Output format: same bar pattern in odd and even lines: '((bar pattern), number of poems)'; "
		  "different bar pattern in odd and even lines: '(((bar pattern), (bar pattern)), number of poems)'")
	print("For poems that do not have a qualitative meter, the value of the bar structure is 'False'.\n")
	folders = os.listdir(directory)
	folders.sort()
	for folder in folders:
		dict_meter = {}
		files = os.listdir(f"{directory}/{folder}")
		for teixml in files:
			meter_qualitative = process_one_file_meter_qualitative(folder, teixml, threshold_qual,
																   max_measure, directory)
			if dict_meter.get(meter_qualitative) != None:
				dict_meter[meter_qualitative] += 1
			else:
				dict_meter[meter_qualitative] = 1
		sorted_dict_meter = sorted(dict_meter.items(), key=lambda kv: kv[1], reverse=True)
		print(folder, sorted_dict_meter)
		print("")


def meter_simultan(threshold_score, threshold_qual, max_measure, directory):
	"""
	In TSV format, for each author, it outputs the frequencies of poems having quantitative
	and qualitative meters at the same time.
	:param threshold_score: float between 0 and 1, indicating the threshold for the poem's
	regularity score.
	:param threshold_qual: a float, a number between 0 and 1, which specifies what percentage
	of the lines must meet the basic syllable count, and what percentage of the lines must
	have a word-initial syllable in a given syllable position for the program to determine
	a bar start.
	:param max_measure: integer indicating the maximum possible syllable count of the bars.
	:param directory: string, which is the name of the folder containing the TEI XML files.
	"""
	print("")
	print("Author", "All_poems", "Simultaneous_poems", "Simultaneous_ratio",
		  "Sim_anap_all", "Sim_anap_ratio", "Sim_anap_mean", "Sim_anap_median",
		  "Sim_dact_all", "Sim_dact_ratio", "Sim_dact_mean", "Sim_dact_median",
		  "Sim_iamb_all", "Sim_iamb_ratio", "Sim_iamb_mean", "Sim_iamb_median",
		  "Sim_troch_all", "Sim_troch_ratio", "Sim_troch_mean", "Sim_troch_median", sep="\t")
	folders = os.listdir(directory)
	folders.sort()
	for folder in folders:
		all_poem = 0
		simultan_poem = 0
		dict_meter_scores = {"anapestic": [], "dactylic": [], "iambic": [], "trochaic": []}
		files = os.listdir(f"{directory}/{folder}")
		for teixml in files:
			all_poem += 1
			meter_qualitative = process_one_file_meter_qualitative(folder, teixml, threshold_qual,
																   max_measure, directory)
			if meter_qualitative != False:
				meter_quantitative = process_one_file_meter_quantitative(folder, teixml,
																		 threshold_score, directory)
				if meter_quantitative[0] != "under_threshold" and meter_quantitative[0] != "equal":
					simultan_poem += 1
					dict_meter_scores[meter_quantitative[0]].append(meter_quantitative[1])
		ratio_sim = round(simultan_poem / all_poem, 2)
		dict_meter_data = {"anapestic": [], "dactylic": [], "iambic": [], "trochaic": []}
		for meter_type in dict_meter_data:
			if len(dict_meter_scores[meter_type]) > 0:
				dict_meter_data[meter_type].extend([len(dict_meter_scores[meter_type]),
													round(len(dict_meter_scores[meter_type]) / simultan_poem, 2),
													round(mean(dict_meter_scores[meter_type]), 2),
													round(median(dict_meter_scores[meter_type]), 2)])
			else:
				dict_meter_data[meter_type].extend([0, 0, "none", "none"])
		print(folder, all_poem, simultan_poem, ratio_sim,
			  *sum([dict_meter_data[meter] for meter in ["anapestic", "dactylic", "iambic",
														 "trochaic"]], []), sep="\t")


def annotate_level3(threshold_score, threshold_qual, max_measure, directory):
	"""
	It annotates the qualitative meter, the quantitative meter, and the regularity
	score of the quantitative meter for the poems in the level3 layer of the ELTE
	Poetry Corpus. The annotations are inserted into the @met attribute of the <div>
	element. The annotated files overwrite the original files in the level3 folder.
	:param threshold_score: float between 0 and 1, indicating the threshold for the poem's
	regularity score.
	:param threshold_qual: a float, a number between 0 and 1, which specifies what percentage
	of the lines must meet the basic syllable count, and what percentage of the lines must
	have a word-initial syllable in a given syllable position for the program to determine
	a bar start.
	:param max_measure: integer indicating the maximum possible syllable count of the bars.
	:param directory: string, which is the name of the folder containing the TEI XML files.
	"""
	os.mkdir("level3")
	folders = os.listdir(directory)
	folders.sort()
	for folder in folders:
		os.mkdir(f"level3/{folder}")
		files = os.listdir(f"{directory}/{folder}")
		for teixml in files:
			print(teixml)
			meter_quantitative = process_one_file_meter_quantitative(folder, teixml,
																	 threshold_score, directory)
			meter_qualitative = process_one_file_meter_qualitative(folder, teixml, threshold_qual,
																   max_measure, directory)
			print(meter_qualitative)
			print(meter_quantitative)
			if type(meter_qualitative) == bool:
				converted_meter_qualitative = meter_qualitative
			else:
				converted_meter_qualitative = ""
				if type(meter_qualitative[0]) == int:
					for number in meter_qualitative:
						converted_meter_qualitative += f"{number}-"
				else:
					for bar in meter_qualitative:
						for number in bar:
							converted_meter_qualitative += f"{number}-"
						converted_meter_qualitative = converted_meter_qualitative[:-1] + "_"
				converted_meter_qualitative = converted_meter_qualitative[:-1]

			tree = ET.parse(f"{directory}/{folder}/{teixml}")
			root = tree.getroot()
			for div in root.iterfind('.//ns:div', TEI_NAMESPACE):
				div.set("met", f"Qual={converted_meter_qualitative}|Quan={meter_quantitative[0]}|QuanScore={round(meter_quantitative[1],2)}")

			change = ET.Element("{http://www.tei-c.org/ns/1.0}change", {"when": str(date.today())})
			change.text = "level3"
			for revisionDesc in root.iterfind(".//ns:revisionDesc", TEI_NAMESPACE):
				revisionDesc.append(change)

			xmlstr = ET.tostring(root, encoding="unicode")
			xml_declaration = '<?xml-model href="http://www.tei-c.org/release/xml/tei/custom/schema/relaxng/tei_all.rng" type="application/xml" schematypens="http://relaxng.org/ns/structure/1.0"?>\n<?xml-model href="http://www.tei-c.org/release/xml/tei/custom/schema/relaxng/tei_all.rng" type="application/xml" schematypens="http://purl.oclc.org/dsdl/schematron"?>\n'
			xmlstr = xml_declaration + xmlstr
			xmlstr = minidom.parseString(xmlstr).toprettyxml(newl='\n', encoding='utf-8')
			xmlstr = os.linesep.join(s for s in xmlstr.decode("utf-8").splitlines() if s.strip())
			with open(f"level3/{folder}/{teixml}", "w", encoding="utf-8") as output:
				output.write(xmlstr)


def get_tsv(directory):
	"""
	 It analyzes the metrical features of the TEI XML files in the level3_without_meter
	 folder and outputs the results to the screen in TSV format.
	:param directory: string, which is the name of the folder containing the TEI XML files.
	"""
	intsruction_max_bar_length = ("Add meg az ütemek maximális szótagszámát (pl. 6).\n"
								  "Specify the maximum number of syllables per measure (e.g., 6).\n")
	instruction_quantitative_threshold = ("Adj meg egy 0 és 1 közötti számot (pl. 0.5).\n"
		"A program csak azokat a verseket tekinti időmértékesnek, amelyeknek a szabályossági pontszáma meghaladja a megadott küszöbértéket.\n"
		"Provide a number between 0 and 1 (e.g., 0.5).\n"
		"The program only considers poems to have quantitative meter if their regularity score exceeds the given threshold.\n")
	instruction_qualitative_threshold = ("Adj meg egy 0 és 1 közötti számot (pl. 0.75).\n"
		"A szám azt jelzi, hogy a verssorok hány százalékának kell azonos szótagszámmal és azonos ütembeosztással rendelkeznie ahhoz, hogy a program ütemhangsúlyosnak tekintse a verset.\n"
		"Provide a number between 0 and 1 (e.g., 0.75).\n"
		"This number indicates the proportion of lines that must have the same number of syllables and the same bar pattern for the program to consider the poem to have qualitative meter.\n")

	print("Ahhoz, hogy működjön a program, a level3_without_meter mappának és a programnak (poetry_corpus_level3_meter.py) ugyanabban a mappában kell lenniük. "
		  "A level3_without_meter mappán belül az egyes szerzőkhöz tartozó versek külön mappákban legyenek. (Az ELTE Verskorpuszban ezek eleve így szerepelnek.)\n"
		 "In order for the program to work, the level3_without_meter folder and the program (poetry_corpus_level3_meter.py) must be in the same directory. "
		  "Within the 'level3_without_meter' folder, the poems belonging to different authors should be placed in separate subfolders. (They are already organized this way in the ELTE Poetry Corpus.)\n")
	print("Nyomd meg a program öt funkciójából annak a számát, amelyiket használni szeretnéd, majd nyomj egy entert.\n"
		  "Press the number of the function you want to use from the program's five functions, then press Enter.\n")
	print("1 Időmértékes metrumú versek gyakorisági adatai \n Frequency data of poems with quantitative meter\n")
	print("2 Ütemhangsúlyos metrumú versek gyakorisági adatai \n Frequency data of poems with qualitative meter\n")
	print("3 Ütemhangsúlyos metrumok gyakorisági listája \n Frequency list of poems with qualitative meter\n")
	print("4 Szimultán metrumú versek gyakorisági adatai \n Frequency data of poems having quantitative and qualitative meters at the same time\n")
	print("5 Az ELTE Verskorpusznak a level3_without_meter mappájában lévő verseiben annotálja a metrumot és az eredményt kiírja az újonnan létrehozott level3 mappába.\n"
		  "It annotates the meter of the poems in the level3_without_meter folder of the ELTE Poetry Corpus and saves the new files in a new folder called level3.\n")
	method = input()
	if method == "1":
		threshold_score = float(input(instruction_quantitative_threshold))
		meter_quantitative(threshold_score, directory)
	elif method == "2":
		threshold_qual = float(input(instruction_qualitative_threshold))
		max_measure = int(input(intsruction_max_bar_length))
		meter_qualitative(threshold_qual, max_measure, directory)
	elif method == "3":
		threshold_qual = float(input(instruction_qualitative_threshold))
		max_measure = int(input(intsruction_max_bar_length))
		meter_qualitative_frequency(threshold_qual, max_measure, directory)
	elif method == "4" or method == "5":
		threshold_score = float(input(instruction_quantitative_threshold))
		threshold_qual = float(input(instruction_qualitative_threshold))
		max_measure = int(input(intsruction_max_bar_length))
		if method == "4":
			meter_simultan(threshold_score, threshold_qual, max_measure, directory)
		elif method == "5":
			annotate_level3(threshold_score, threshold_qual, max_measure, directory)
	else:
		print("Rossz gombot nyomtál. / You pressed the wrong button.")


#get_tsv("level3_without_meter")
annotate_level3(0, 0.75, 6, "level3_without_meter")