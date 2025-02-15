#!/usr/bin/env python3
# -*- coding: utf-8, vim: expandtab:ts=4 -*-

"""
annotate_level3(0, 0.75, 6) metódus: A program annotálja a level3 mappában lévő
level3-as verziójú fájlokat az időmértékes és ütemhangsúlyos metrum jellemzőivel.
Az annotált fájlokkal felülírja a level3 mappa eredeti fájljait. A program
részletesebb működését lásd alább.

get_tsv() metódus: A program besorolja a verseket a daktilikus, anapesztikus,
trochaikus vagy jambikus időmértékes kategóriákba, és megad egy 0 és 1 közötti
szabályossági pontszámot, amely azt jelzi, hogy a vers ritmusa milyen mértékben
felel meg a felismert metrum elvont ritmusképletének. A program úgyszintén felismeri
az aaaa... és abab... szerkezetű ütemhangsúlyos metrumú verseket, valamint a szimultán
metrumú, egyszerre időmértékes és ütemhangsúlyos verseket.

Az eredményeket TSV formában írja ki, amelyet bármilyen táblázatkezelő programba
bemásolhatunk.

A program bemenete az ELTE Verskorpusz (https://github.com/ELTE-DH/poetry-corpus) level3
TEI XML fájljai (minden vers egy külön fájl), amelyekben szerepelnek a sorok időmértékes
ritmusára vonatkozó annotációk. Ezekben a 0 karakter a rövid, az 1 karakter pedig a
hosszú szótagokat jelöli. A program ezeket átkonvertálja 1 (rövid szótag) és 2 (hosszú
szótag) karakterekké, és az így átkonvertált, a szótagok moraszámát jelző számokkal végzi
el a számításokat.

A program működtetése: másoljuk be egy level3 nevű mappába a TEI XML-eket úgy, hogy a
level3 mappán belül az egyes szerzőkhöz tartozó versek külön mappákban legyenek
(pl. level3/Kosztolanyi/file1, level3/Kosztolanyi/file2, level3/Babits/file3). Az ELTE
Verskorpusz github mappájában a fájlok már eleve így szerepelnek. A level3 mappának és
a hunpoem_meter_analyzer.py programnak ugyanabban a mappában kell lennie.
Természetesen a verseket nem csak szerzők szerint csoportosíthatjuk mappákba.

Futtatás során az alábbi négy fő metódusból választhatunk:
1. meter_quantitative() : Kiírja TSV-ként az időmértékesként felismert versek
előfordulási adatait szerzőkre lebontva.
2. meter_qualitative() : Kiírja TSV-ként az ütemhangsúlyosként felismert versek
előfordulási adatait szerzőkre lebontva.
3 meter_qualitative_frequency() : Szerzőkre lebontva megadja a különböző típusú
ütemhangsúlyos metrumok gyakorisági listáját.
4. meter_simultan() : Kiírja TSV-ként a szimultánként felismert versek előfordulási
adatait szerzőkre lebontva.
"""


from statistics import mean, median
import os
import xml.etree.ElementTree as ET
from xml.dom import minidom

ET.register_namespace("", "http://www.tei-c.org/ns/1.0")

TEI_NAMESPACE = {"ns": "http://www.tei-c.org/ns/1.0"}


# időmértékes:


def pentameter(rhythm, words):
	"""
	Megpróbál leelemezni egy sort pentameterként.
	:param rhythm: a verssor ritmusát reprezentáló string, amely "1" és "2" karakterekből
	áll ("1" = rövid szótag, "2" = hosszú szótag).
	:param words: lista, amely a verssor szavait tartalmazza.
	:return: lista, amelynek elemei az 1 és 2 karakterekből álló verslábak.
	Ha nem lehetett pentameterként leelemezni a sort, akkor a kimenet [0].
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
	A verssor ritmusát reprezentáló, "1" és "2" karakterekből álló stringet
	próbálja felosztani négymorás verslábakat tartalmazó listára.
	:param rhythm: a verssor ritmusát reprezentáló string, amely "1" és "2"
	karakterekből áll ("1" = rövid szótag, "2" = hosszú szótag).
	:return: lista, amely a sor négymoránként felosztott verslábait tartalmazza
	(pl. ["211", "211", "22"]). Ha a sort nem lehetett négymorás verslábakra
	felosztani, akkor a kimenet: [0]
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

	# Az utolsó rövid szótag hosszúként, az utolsó hosszú szótag pedig rövidként
	# is értelmezhető:
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
	A négymorás verslábakra felosztott sort teszteli anapesztikus vagy daktilikus
	metrumra, amelynek eredményeképpen ad egy verssort jellemző, 0 és 1 közötti
	pontszámot, amely a tesztelt metrumra kapott szabályossági pontszám.
	:param feet: lista, amelynek elemei az "1" és "2" karaktereket tartalmazó
	négymorás verslábak.
	:param checked_meter4: string, amely a tesztelt metrumot jelzi ("anapestic" vagy
	"dactylic")
	:return: 0 és 1 közötti float, amely a tesztelt metrumra kapott szabályossági pontszám.
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
	A verssor ritmusát reprezentáló, "1" és "2" karakterekből álló stringet két
	szótagonként felosztja verslábakra.
	:param rhythm: a verssor ritmusát reprezentáló string, amely "1" és "2"
	karakterekből áll ("1" = rövid szótag, "2" = hosszú szótag).
	:return: lista, amelynek elemei a sor kétszótagonként felosztott verslábai
	(pl. ["11", "12", "22", "12"]).
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
	A kétszótagonként verslábakra osztott sort teszteli jambikus vagy trochaikus
	metrumra, amelynek eredményeképpen ad egy verssort jellemző, 0 és 1 közötti
	pontszámot, amely a tesztelt metrumra kapott szabályossági pontszám.
	:param feet: lista, amelynek elemei az "1" és "2" karaktereket tartalmazó
	kétszótagos verslábak.
	:param checked_meter2: string, amely a tesztelt metrumot jelzi ("iambic" vagy
	"trochaic")
	:return: 0 és 1 közötti float, amely a tesztelt metrumra kapott szabályossági pontszám.
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
	Fő függvény, amely egy megadott időmértékes metrumra (anapesztikus, daktilikus,
	jambikus vagy trochaikus) letesztel egy verssort, és kimenetként kiad egy 0 és 1
	közötti szabályossági pontszámot.
	:param rhythm: a verssor ritmusát reprezentáló, "1" és "2" karakterekből álló string,
	amelyben "1" rövid szótag, "2" hosszú szótag.
	:param words: lista, amely a verssor szavait tartalmazza.
	:param checked_meter: string, amely a tesztelendő időmértékes metrum ("anapestic",
	"dactylic", "iambic" vagy "trochaic").
	:return: float, amely a sornak a tesztelt metrumra kapott szabélyossági pontszáma.
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


def test_meter_poem(poem_rhythms, poem_words, checked_meter, threshold):
	"""
	Fő függvény, amely egy megadott időmértékes metrumra (anapesztikus, daktilikus,
	jambikus vagy trochaikus) leteszteli a verset, és kimenetként kiad egy 0 és 1
	közötti szabályossági pontszámot.
	:param poem_rhythms: lista, amely egy vers sorainak "1" és "2" karakterekből álló
	ritmusát tartalmazza listaelemekként. (pl. ["121112", "2212", "11112222", "22221"]
	- "1" = rövid szótag, "2" = hosszú szótag)
	:param poem_words: lista, amely listákként tartalmazza a verssorok szavait.
	:param checked_meter: string, amely a tesztelt metrumot jelzi ("anapestic", "dactylic",
	"iambic" vagy "trochaic").
	:param threshold: 0 és 1 közötti float, amely a vers szabályossági pontszámának a
	küszöbértéke.
	:return: lista, amelynek első eleme a tesztelt metrum ("anapestic", "dactylic", "iambic",
	"trochaic" vagy "under_threshold"), második eleme pedig a tesztelt metrumra kapott
	szabélyossági érték (float). Ha a versnek a tesztelt metrumra kapott szabályossági
	pontszáma nem haladja meg a küszöbértéket, akkor a kimenet "under_threshold".
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
	if score_poem <= threshold:
		checked_meter = "under_threshold"
	return [checked_meter, score_poem]


def test_all_meters(poem_rhythms, poem_words, threshold):
	"""
	Fő függvény, amely mind a négy időmértékes metrumot (anapesztikus, daktilikus,
	jambikus, trochaikus) végigteszteli egy versen, és a legnagyobb szabályossági
	pontszámút adja meg kimenetként a szabályossági pontszámmal együtt.
	:param poem_rhythms: lista, amely egy vers sorainak "1" és "2" karakterekből álló
	ritmusát tartalmazza listaelemekként. (pl. ["121112", "2212", "11112222", "22221"]
	- "1" = rövid szótag, "2" = hosszú szótag)
	:param poem_words: lista, amely listákként tartalmazza a verssorok szavait.
	:param threshold: 0 és 1 közötti float, amely a vers szabályossági pontszámának a
	küszöbértéke.
	:return: lista, amelynek első eleme a megállapított metrum ("anapestic", "dactylic",
	"iambic", "trochaic", "under_threshold" vagy "equal"), második eleme pedig a megállapított,
	0 és 1 közötti szabályossági pontszám. Ha a legnagyobb pontszámú metrum sem haladja meg a
	küszöbértéket, akkor a kimenet "under_threshold". Ha kettő vagy több metrumra is ugyanaz
	a legnagyobb pontszám jön ki, akkor a kimenet "equal".
	"""
	meters = ["anapestic", "dactylic", "iambic", "trochaic"]
	meter = ""
	score = 0
	equal = False
	for checked_meter in meters:
		meter_and_score = test_meter_poem(poem_rhythms, poem_words, checked_meter, threshold)
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


# ütemhangsúlyos:


def get_stressed_syllables_in_line(line_words):
	"""
	Egy verssornak megadja a hangsúlyos és hangsúlytalan szótagjait.
	:param line_words: kétdimenziós lista, amelynek elemei egy verssor szavai. (Azért
	kétdimenziós, mert az összetett szavak összetételi tagokra bontott verziója is beadható
	a függvénynek, ebben az esetben egy szó a hozzátartozó listán belül lesz listaelemkre
	bontva az összetételi tagoknak megfelelően.
	:return: "1" és "0" karakterekből álló string, amely a verssor szó eleji/hangsúlyos és nem
	szó eleji/hangsúlytalan szótagjait reprezentálja ("1" = szó eleji szótag, "0" = nem szó
	eleji szótag).
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


def get_line_length(lines, percentage):
	"""
	A verssorok szó eleji és nem szó eleji szótagjait reprezentáló stringek listája alapján
	megállapítja a sorok jellemző szótagszámát, amennyiben van ilyen.
	:param lines: lista, amely az "1" és "0" karakterekből álló, a sorok szó eleji és
	nem szó eleji szótagjait reprezentáló stringeket tartalmazza.
	:param percentage: float, egy 0 és 1 közötti szám, amellyel meg kell szorozni a sorszámot.
	Ha a sorok esetében talált leggyakoribb szótagszám előfordulási száma nagyobb vagy egyenlő,
	mint a szorzás eredményeképpen kapott szám, akkor a függvény kimenete nem False lesz, hanem
	a talált leggyakoribb szótagszám.
	:return: integer, amely a verssoroknak a szótagszámát jelzi. Ha a sorok egészére nem
	jellemző valamilyen meghatározott szótagszám, akkor a kimenet False értékű boolean.
	"""
	syllable_nums = [len(line) for line in lines]
	max_syll_num_frequency = 0
	for num in syllable_nums:
		syll_num_frequency = syllable_nums.count(num)
		if syll_num_frequency > max_syll_num_frequency:
			max_syll_num_frequency = syll_num_frequency
	line_length = [num for num in syllable_nums if syllable_nums.count(num) == max_syll_num_frequency]
	line_length = list(dict.fromkeys(line_length))
	if len(line_length) == 1 and max_syll_num_frequency >= len(lines) * percentage:
		line_length = line_length[0]
	else:
		line_length = False
	return line_length


def conclude_meter_poem(lines, line_length, percentage, max_measure):
	"""
	Megállapítja, hogy jellemzően azonos szótagszámú verssorokra jellemző-e valamilyen
	ütemhangsúlyos metrum, és megadja az ütemek szótagszámát.
	Az ütemhatár megállapításának két megszorítása:
		(1) A második szótag nem lehet ütemhatár.
		(2) A sorok egy megadott százalékában (percentage paraméter) szó eleji szótagnak
		kell esnie a szótaghelyre.
	:param lines: lista, amely "1" és "0" karakterekből álló stringekként tartalmazza
	a verssorok szó eleji és nem szó eleji szótagjainak a reprezentációit ("1" =
	szó eleji szótag, "0" = nem szó eleji szótag).
	:param line_length: integer, amely a verssorok jellemző szótagszáma.
	:param percentage: float, egy 0 és 1 közötti szám, amellyel a függvény megszorozza a
	sorszámot. Ha egy adott sorszámú szótag esetében talált hangsúlypontszám nagyobb vagy
	egyenlő, mint a szorzás eredményeképpen kapott szám, akkor az adott szótag egy új ütem
	első szótagja.
	:param max_measure: integer, amely az ütemek maximális szótagszáma.
	:return: string, amely a megállapított ütemek szótagszámát tartalmazza. Ha nem sikerült
	ütemeket megállapítani, vagy pedig az ütemek között van a megadott maximális szótagszámnál
	nagyobb szótagszámú, akkor a kimenet False értékű boolean.
	Figyelem: Egy verssor lehet egy darab ütem is, amennyiben a sor nem hosszabb a megadott
	maximális szótagszámnál.
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
	# Az alábbi sorban szerepel a második szótaghelyre és az ütemkezdetre vonatkozó megszorítás:
	meter = [score_syll[0] for score_syll in enumerate(syllable_scores)
			 if score_syll[0] != 1 and score_syll[1] >= len(lines) * percentage]
	# Az ütemkezdeteket jelölő szótag-sorszámokat át kell konvertálni az ütemek szótagszámává:
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
		if num_syll > max_measure: # az ütemek maximális szótagszámára vonatkozó feltétel
			meter1 = False
			break
	return meter1


def analyse_poem_meter(rhythm_poem, percentage, max_measure):
	"""
	Megállapítja, hogy egy vers ütemhangsúlyos-e, és megadja a vers ütemeinek a
	szótagszámát. Ütemhangsúlyosság szempontjából aaaa..., valamint abab... metrumú
	verseket ismer fel.
	:param rhythm_poem: lista, amely a verssorok szó eleji és nem szó eleji szótagjait
	reprezentáló, "1" és "0" karakterekből álló stringekből áll ("1" = szó eleji szótag,
	"0" = nem szó eleji szótag).
	:param percentage: float, egy 0 és 1 közötti szám, amely azt adja meg, hogy a
	verssorok hány százalékának kell teljesítenie az alapszótagszámot, és hogy a
	verssorok hány százalékában kell szó eleji szótagnak esnie egy adott szótaghelyre,
	hogy a program ütemkezdetet állapítson meg.
	:param max_measure: integer, amely az ütemek maximális szótagszáma.
	:return: string, amely a megállapított ütemek szótagszámát tartalmazza. Ha nem sikerült
	ütemeket megállapítani, vagy pedig az ütemek között van a küszöbértéknél nagyobb
	szótagszámú, akkor a kimenet False értékű boolean.
	Figyelem: Egy verssor lehet egy darab ütem is, amennyiben a sor nem hosszabb a megadott
	maximális szótagszámnál.
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
	line_length = get_line_length(lines, percentage)
	if line_length and len(lines) > 1:	# egysoros versek nem lehetnek ütemhangsúlyosak
		meter = conclude_meter_poem(lines, line_length, percentage, max_measure)
		if meter == False and len(lines) > 3:	# az ütemhangsúlyossághoz a páros és páratlan sorból is minimum kettő kell.
			odd_line_length = get_line_length(odd_lines, percentage)
			even_line_length = get_line_length(even_lines, percentage)
			if odd_line_length and even_line_length:
				meter_odd = conclude_meter_poem(odd_lines, odd_line_length, percentage, max_measure)
				meter_even = conclude_meter_poem(even_lines, even_line_length, percentage, max_measure)
				if meter_odd and meter_even:
					meter = (meter_odd, meter_even)
	elif len(lines) > 3: # az ütemhangsúlyossághoz a páros és páratlan sorból is minimum kettő kell.
		odd_line_length = get_line_length(odd_lines, percentage)
		even_line_length = get_line_length(even_lines, percentage)
		if odd_line_length and even_line_length:
			meter_odd = conclude_meter_poem(odd_lines, odd_line_length, percentage, max_measure)
			meter_even = conclude_meter_poem(even_lines, even_line_length, percentage, max_measure)
			if meter_odd and meter_even:
				meter = (meter_odd, meter_even)
	return meter


# Main code:

# Processing one file:

def process_one_file_meter_quantitative(folder, teixml, threshold):
	"""
	Egy TEI XML fájlon (amely egy verset tartalmaz) lefuttatja az időmértékes metrumot felismerő
	test_all_meters függvényt, ami hívja a többi függvényt.
	:param folder: string, amely a könyvtár neve, amelyben a verset tartalmazó XML fájl van.
	:param teixml: string, amely az XML fájl neve, amely a verset tartalmazza.
	:param threshold: 0 és 1 közötti float, amely meghatározza a vers szabályossági
	pontszámának a küszöbértékét.
	:return: lista, amelynek első eleme a megállapított metrum ("anapestic", "dactylic",
	"iambic", "trochaic", "under_threshold" vagy "equal"), második eleme pedig a megállapított,
	0 és 1 közötti szabályossági pontszám. Ha a legnagyobb pontszámú metrum sem haladja meg a
	küszöbértéket, akkor a kimenet "under_threshold". Ha kettő vagy több metrumra is ugyanaz
	a legnagyobb pontszám jön ki, akkor a kimenet "equal".
	"""
	tree = ET.parse(f"level3/{folder}/{teixml}")
	root = tree.getroot()
	poem_rhythms = [l_tag.get('real') for l_tag in root.iterfind(".//ns:l", TEI_NAMESPACE)]
	poem_rhythms = [rhythm.replace("1", "2") for rhythm in poem_rhythms]
	poem_rhythms = [rhythm.replace("0", "1") for rhythm in poem_rhythms]
	poem_words = [[token.text for token in l_tag if token.tag == "{http://www.tei-c.org/ns/1.0}w"]
				  for l_tag in root.iterfind(".//ns:l", TEI_NAMESPACE)]
	meter = test_all_meters(poem_rhythms, poem_words, threshold)
	return meter


def process_one_file_meter_qualitative(folder, teixml, percentage, max_measure):
	"""
	Egy TEI XML fájlon (amely egy verset tartalmaz) lefuttatja az ütemhangsúlyos metrumot
	felismerő analyse_poem_meter függvényt, ami hívja a többi függvényt.
	:param folder: string, amely a könyvtár neve, amiben a verset tartalmazó XML fájl van.
	:param teixml: string, amely az XML fájl neve, ami a verset tartalmazza.
	:param percentage: float, egy 0 és 1 közötti szám, amely azt adja meg, hogy a verssorok
	hány százalékának kell teljesítenie az alapszótagszámot, és hogy a verssorok hány
	százalékában kell szó eleji szótagnak esnie egy adott szótaghelyre ahhoz, hogy a program
	ütemkezdetet állapítson meg.
	:param max_measure: integer, amely az ütemek maximális szótagszáma.
	:return: string, amely a megadott ütemek szótagszámát tartalmazza. Ha nem sikerült ütemeket
	megállapítani, vagy pedig az ütemek között van a megadott maximális szótagszámnál nagyobb
	szótagszámú, akkor a kimenet False értékű boolean.
	"""
	tree = ET.parse(f"level3/{folder}/{teixml}")
	root = tree.getroot()
	rhythm_poem = []
	for lg_tag in root.iterfind(".//ns:lg", TEI_NAMESPACE):
		rhythm_lg = []
		for l_tag in lg_tag.iterfind(".//ns:l", TEI_NAMESPACE):
			# Itt a line_words azért kétdimenziós lista, mert a programnak van egy változata, amely
			# a szavakat szétbontja összetételi tagokra, és a szavak összetételi tagjai listán belüli
			# listákként reprezentálhatók.
			line_words = [[token.text] for token in l_tag if token.tag == "{http://www.tei-c.org/ns/1.0}w"]
			rhythm_line = get_stressed_syllables_in_line(line_words)
			rhythm_lg.append(rhythm_line)
		rhythm_poem.append(rhythm_lg)
	meter = analyse_poem_meter(rhythm_poem, percentage, max_measure)
	return meter


# 5 main methods:


def meter_quantitative(threshold):
	"""
	Kiírja TSV-ként az időmértékesként felismert versek előfordulási adatait szerzőkre
	lebontva.
	:param threshold: 0 és 1 közötti float, amely a vers szabályossági pontszámának a
	küszöbértéke.
	"""
	print("")
	print("Szerző", "Összes_vers", "Időmértékes_vers", "Időmértékes_arány",
		  "Anap_összes", "Anap_arány", "Anap_átlag", "Anap_medián",
		  "Dakt_összes", "Dakt_arány", "Dakt_átlag", "Dakt_medián",
		  "Jamb_összes", "Jamb_arány", "Jamb_átlag", "Jamb_medián",
		  "Troch_összes", "Troch_arány", "Troch_átlag", "Troch_medián", sep="\t")
	folders = os.listdir("level3")
	folders.sort()
	for folder in folders:
		all_poem = 0
		metric_poem = 0
		anapestic = []
		dactylic = []
		iambic = []
		trochaic = []
		files = os.listdir("level3/" + folder)
		for teixml in files:
			all_poem += 1
			meter_quantitative = process_one_file_meter_quantitative(folder, teixml, threshold)
			if meter_quantitative[0] != "under_threshold" and meter_quantitative[0] != "equal":
				metric_poem += 1
				if meter_quantitative[0] == "anapestic":
					anapestic.append(meter_quantitative[1])
				elif meter_quantitative[0] == "dactylic":
					dactylic.append(meter_quantitative[1])
				elif meter_quantitative[0] == "iambic":
					iambic.append(meter_quantitative[1])
				elif meter_quantitative[0] == "trochaic":
					trochaic.append(meter_quantitative[1])
		metric_ratio = round(metric_poem / all_poem, 2)
		num_anapestic = len(anapestic)
		if num_anapestic > 0:
			ratio_anapestic = round(num_anapestic / metric_poem, 2)
			mean_anapestic = round(mean(anapestic), 2)
			median_anapestic = round(median(anapestic), 2)
		else:
			ratio_anapestic = 0
			mean_anapestic = "none"
			median_anapestic = "none"
		num_dactylic = len(dactylic)
		if num_dactylic > 0:
			ratio_dactylic = round(num_dactylic / metric_poem, 2)
			mean_dactylic = round(mean(dactylic), 2)
			median_dactylic = round(median(dactylic), 2)
		else:
			ratio_dactylic = 0
			mean_dactylic = "none"
			median_dactylic = "none"
		num_iambic = len(iambic)
		if num_iambic > 0:
			ratio_iambic = round(num_iambic / metric_poem, 2)
			mean_iambic = round(mean(iambic), 2)
			median_iambic = round(median(iambic), 2)
		else:
			ratio_iambic = 0
			mean_iambic = "none"
			median_iambic = "none"
		num_trochaic = len(trochaic)
		if num_trochaic > 0:
			ratio_trochaic = round(num_trochaic / metric_poem, 2)
			mean_trochaic = round(mean(trochaic), 2)
			median_trochaic = round(median(trochaic), 2)
		else:
			ratio_trochaic = 0
			mean_trochaic = "none"
			median_trochaic = "none"

		print(folder, all_poem, metric_poem, metric_ratio,
			  num_anapestic, ratio_anapestic, mean_anapestic, median_anapestic,
			  num_dactylic, ratio_dactylic, mean_dactylic, median_dactylic,
			  num_iambic, ratio_iambic, mean_iambic, median_iambic,
			  num_trochaic, ratio_trochaic, mean_trochaic, median_trochaic, sep="\t")


def meter_qualitative(percentage, max_measure):
	"""
	Kiírja TSV-ként az ütemhangsúlyosként felismert versek előfordulási adatait
	szerzőkre lebontva.
	:param percentage: float, egy 0 és 1 közötti szám, amely azt adja meg, hogy a
	verssorok hány százalékának kell teljesítenie az alapszótagszámot, és hogy a
	verssorok hány százalékában kell szóeleji szótagnak esnie egy adott szótaghelyre
	ahhoz, hogy a program ütemkezdetet állapítson meg.
	:param max_measure: integer, amely az ütemek maximális szótagszáma.
	"""
	print("")
	print("Szerző", "Összes_vers", "Ütemhangsúlyos", "Ütemhangsúlyos_arány", sep="\t")
	folders = os.listdir("level3")
	folders.sort()
	for folder in folders:
		all_poem = 0
		metric_poem = 0
		files = os.listdir("level3/" + folder)
		for teixml in files:
			all_poem += 1
			meter_qualitative = process_one_file_meter_qualitative(folder, teixml, percentage, max_measure)
			if meter_qualitative != False:
				metric_poem += 1
		metric_ratio = round(metric_poem / all_poem, 2)
		print(folder, all_poem, metric_poem, metric_ratio, sep="\t")


def meter_qualitative_frequency(percentage, max_measure):
	"""
	Szerzőkre lebontva megadja a különböző típusú ütemhangsúlyos metrumok gyakorisági
	listáját.
	:param percentage: float, egy 0 és 1 közötti szám, amely azt adja meg, hogy a
	verssorok hány százalékának kell teljesítenie az alapszótagszámot, és hogy a
	verssorok hány százalékában kell szóeleji szótagnak esnie egy adott szótaghelyre
	ahhoz, hogy a program ütemkezdetet állapítson meg.
	:param max_measure: integer, amely az ütemek maximális szótagszáma.
	"""
	print("")
	print("Kimenet formátuma: egységes ütemosztás: '((ütemosztás), előfordulás)'; páratlan és "
	"páros sorokban eltérő ütemosztás: '(((ütemosztás), (ütemosztás)), előfordulás)'")
	print("A nem ütemhangsúlyos verseknél 'False' szerepel.\n")
	folders = os.listdir("level3")
	folders.sort()
	for folder in folders:
		dict_meter = {}
		files = os.listdir("level3/" + folder)
		for teixml in files:
			meter_qualitative = process_one_file_meter_qualitative(folder, teixml, percentage, max_measure)
			if dict_meter.get(meter_qualitative) != None:
				dict_meter[meter_qualitative] += 1
			else:
				dict_meter[meter_qualitative] = 1
		sorted_dict_meter = sorted(dict_meter.items(), key=lambda kv: kv[1], reverse=True)
		print(folder, sorted_dict_meter)
		print("")


def meter_simultan(threshold, percentage, max_measure):
	"""
	Kiírja TSV-ként a szimultánként felismert versek előfordulási adatait szerzőkre
	lebontva.
	:param threshold: 0 és 1 közötti float, amely meghatározza a vers szabályossági
	pontszámának a küszöbértékét.
	:param percentage: 0 és 1 közötti float, amely azt adja meg, hogy a verssorok
	hány százalékának kell teljesítenie az alapszótagszámot, és hogy a verssorok
	hány százalékában kell szóeleji szótagnak esnie egy adott szótaghelyre ahhoz,
	hogy a program ütemkezdetet állapítson meg.
	:param max_measure: integer, amely az ütemek maximális szótagszáma.
	"""
	print("")
	print("Szerző", "Összes_vers", "Szimultán_vers", "Szimultán_arány",
		  "Szim_anap", "Szim_dakt", "Szim_jamb", "Szim_troch", sep="\t")
	folders = os.listdir("level3")
	folders.sort()
	for folder in folders:
		all_poem = 0
		simultan_poem = 0
		sim_ana = []
		sim_dact = []
		sim_iamb = []
		sim_troch = []
		files = os.listdir("level3/" + folder)
		for teixml in files:
			all_poem += 1
			meter_qualitative = process_one_file_meter_qualitative(folder, teixml, percentage, max_measure)
			if meter_qualitative != False:
				meter_quantitative = process_one_file_meter_quantitative(folder, teixml, threshold)
				if meter_quantitative[0] != "under_threshold" and meter_quantitative[0] != "equal":
					simultan_poem += 1
					if meter_quantitative[0] == "anapestic":
						sim_ana.append(meter_quantitative[1])
					elif meter_quantitative[0] == "dactylic":
						sim_dact.append(meter_quantitative[1])
					elif meter_quantitative[0] == "iambic":
						sim_iamb.append(meter_quantitative[1])
					elif meter_quantitative[0] == "trochaic":
						sim_troch.append(meter_quantitative[1])
		num_sim_ana = len(sim_ana)
		num_sim_dact = len(sim_dact)
		num_sim_iamb = len(sim_iamb)
		num_sim_troch = len(sim_troch)
		ratio_sim = round(simultan_poem / all_poem, 2)
		print(folder, all_poem, simultan_poem, ratio_sim,
			  num_sim_ana, num_sim_dact, num_sim_iamb, num_sim_troch, sep="\t")


def annotate_level3(threshold, percentage, max_measure):
	"""
	Az ELTE Verskorpusz level3-as verseinek annotálja az ütemhangsúlyos netrumát, az
	időmértékes metrumát, valamint az időmértékes metrum szabályossági pontszámát. Az
	annotációkat a <div> elem @met attribútumába rakja bele. Az annotált fájlokkal
	felülírja a level3 mappa fájéjait.
	:param threshold: 0 és 1 közötti float, amely meghatározza a vers szabályossági
	pontszámának a küszöbértékét.
	:param percentage: 0 és 1 közötti float, amely azt adja meg, hogy a verssorok
	hány százalékának kell teljesítenie az alapszótagszámot, és hogy a verssorok
	hány százalékában kell szóeleji szótagnak esnie egy adott szótaghelyre ahhoz,
	hogy a program ütemkezdetet állapítson meg.
	:param max_measure: integer, amely az ütemek maximális szótagszáma.
	"""
	# os.mkdir("level33")
	folders = os.listdir("level3")
	folders.sort()
	for folder in folders:
		# os.mkdir(f"level33/{folder}")
		files = os.listdir("level3/" + folder)
		for teixml in files:
			print(teixml)
			meter_quantitative = process_one_file_meter_quantitative(folder, teixml, threshold)
			meter_qualitative = process_one_file_meter_qualitative(folder, teixml, percentage, max_measure)
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

			tree = ET.parse(f"level3/{folder}/{teixml}")
			root = tree.getroot()
			for div in root.iterfind('.//ns:div', TEI_NAMESPACE):
				div.set("met", f"Qual={converted_meter_qualitative}|Quan={meter_quantitative[0]}|QuanScore={round(meter_quantitative[1],2)}")
			xmlstr = ET.tostring(root, encoding="unicode")
			xml_declaration = '<?xml-model href="http://www.tei-c.org/release/xml/tei/custom/schema/relaxng/tei_all.rng" type="application/xml" schematypens="http://relaxng.org/ns/structure/1.0"?>\n<?xml-model href="http://www.tei-c.org/release/xml/tei/custom/schema/relaxng/tei_all.rng" type="application/xml" schematypens="http://purl.oclc.org/dsdl/schematron"?>\n'
			xmlstr = xml_declaration + xmlstr
			xmlstr = minidom.parseString(xmlstr).toprettyxml(newl='\n', encoding='utf-8')
			xmlstr = os.linesep.join(s for s in xmlstr.decode("utf-8").splitlines() if s.strip())
			with open(f"level3/{folder}/{teixml}", "w", encoding="utf-8") as output:
				output.write(xmlstr)





def get_tsv():
	print("Ahhoz, hogy működjön a program, az ELTE Verskorpusz (https://github.com/ELTE-DH/poetry-corpus) "
		  "level3 mappájában lévő verseket be kell másolni egy level3 nevű mappába úgy, hogy a level3 "
		  "mappán belül az egyes szerzőkhöz tartozó versek külön mappákban legyenek. (Az ELTE Verskorpusz "
		  "github repozitóriumában ezek eleve így szerepelnek.) "
		  "Pl. level3/Kosztolanyi/file1, level3/Kosztolanyi/file2, level3/Babits/file3 "
		  "A létrehozott level3 mappának és a hunpoem_meter_analyzer.py programnak ugyanabban a mappában "
		  "kell lennie.\n")
	print("Nyomd meg a program négy funkciójából annak a számát, amelyiket használni szeretnéd, majd nyomj "
		  "egy entert.\n")
	print("1 Időmértékes metrumú versek gyakorisági adatai")
	print("2 Ütemhangsúlyos metrumú versek gyakorisági adatai")
	print("3 Ütemhangsúlyos metrumok gyakorisági listája")
	print("4 Szimultán metrumú versek gyakorisági adatai")
	print("5 Az ELTE Verskorpusz level3-as verseiben annotálja a metrumot és az eredményt kiírja a level33 mappába")
	method = input()
	if method == "1":
		threshold = float(input("Adj meg egy 0 és 1 közötti számot (pl. 0.5).\n"
					 "A program csak azokat a verseket tekinti időmértékesnek, amelyeknek "
					 "a szabályossági pontszáma meghaladja a megadott küszöbértéket. Minél "
					  "alacsonyabb számot adunk meg, annál több verset fog a program besorolni "
						  "valamelyik időmértékes metrumkategóriába.\n"))
		meter_quantitative(threshold)
	elif method == "2":
		percentage = float(input("Adj meg egy 0 és 1 közötti számot (pl. 0.75).\n"
						   "A szám azt jelzi, hogy a verssorok hány százalékának kell azonos szótagszámmal "
						   "és azonos ütembeosztással rendelkeznie ahhoz, hogy a program ütemhangsúlyosnak "
						   "tekintse a verset.\n"))
		max_measure = int(input("Add meg az ütemek maximális szótagszámát (pl. 6).\n"))
		meter_qualitative(percentage, max_measure)
	elif method == "3":
		percentage = float(input("Adj meg egy 0 és 1 közötti számot (pl. 0.75).\n"
						   "A szám azt jelzi, hogy a verssorok hány százalékának kell azonos szótagszámmal "
						   "és azonos ütembeosztással rendelkeznie ahhoz, hogy a program ütemhangsúlyosnak "
						   "tekintse a verset.\n"))
		max_measure = int(input("Add meg az ütemek maximális szótagszámát (pl. 6).\n"))
		meter_qualitative_frequency(percentage, max_measure)
	elif method == "4" or method == "5":
		threshold = float(input("Adj meg egy 0 és 1 közötti számot (pl. 0.5).\n"
					 "A program csak azokat a verseket tekinti időmértékesnek, amelyeknek "
					 "a szabályossági pontszáma meghaladja a megadott küszöbértéket. Minél "
					  "alacsonyabb számot adunk meg, annál több verset fog a program besorolni "
						  "valamelyik időmértékes metrumkategóriába, és így annál több verset fog "
						  "szimultánként elemezni.\n"))
		percentage = float(input("Adj meg egy 0 és 1 közötti számot (pl. 0.75).\n"
						   "A szám azt jelzi, hogy a verssorok hány százalékának kell azonos szótagszámmal "
						   "és azonos ütembeosztással rendelkeznie ahhoz, hogy a program ütemhangsúlyosnak "
						   "tekintse a verset.\n"))
		max_measure = int(input("Add meg az ütemek maximális szótagszámát (pl. 6).\n"))
		if method == "4":
			meter_simultan(threshold, percentage, max_measure)
		elif method == "5":
			annotate_level3(threshold, percentage, max_measure)
	else:
		print("Rossz gombot nyomtál.")


# get_tsv()
annotate_level3(0, 0.75, 6)