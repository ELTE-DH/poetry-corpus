
# ELTE Poetry Corpus


ELTE Poetry Corpus is a continuously expanding database developed by the [_Department of Digital Humanities at Eötvös Loránd University_](https://elte-dh.hu/). Currently, the corpus contains the complete poems of 52 Hungarian canonical poets, the sound devices of the poems and the grammatical features of words in XML format (in TEI and non-TEI XML format).

## Size

- number of poets: 53
- number of poems: 14 358
- number of words: 2 859 163
- number of tokens: 3 621 416

For more information of the size of subcorpora and the authors' year of birth and death, see the files subcorpus\_sizes.tsv and poets\_birth\_and\_death.tsv 

## TEI Levels

The source of the corpus was the collection of the [_Hungarian Electronic Library_](http://mek.oszk.hu), which contains numerous poetic oeuvres in digitized form.

1. The texts from the Hungarian Electronic Library were converted into TEI XML format based on the [_Text Encoding Initiative_](https://tei-c.org/).
2. The automatically converted poems containing the annotations of structural units were checked manually (level1).
3. Then, we tokenized the poems and annotated the grammatical features of words by using [_e-magyar_](https://github.com/nytud/emtsv), an NLP tool chain for Hungarian texts. The level2 folder contains the TEI XML files in which the morphosyntactic features (values of the msd attributes) are annotated in the format of universal dependencies, while the level2\_emMorph folder contains the same files in which the morphosyntactic features are annotated in its own, [_emMorph_](https://e-magyar.hu/en/textmodules/emmorph_codelist) format of e-magyar.
4. After the grammatical annotation, we also annotated the rhyme patterns, the rhyme pairs, the rhythm of lines, the alliterations, the phonological features of words, and the meter of the poems (level3).
5. Finally, we added further annotations of poetic features to the corpus and changed the name and the position of some elements and attributes, using a non-TEI XML format defined for the project (level4).

## poem_texts

The poem_texts folder contains the poems in TXT format, without the XML annotations. This version of the corpus was generated from the level1 files. The TXT files contain the editorial notes related to date and place, which are in `<p>` elements in the TEI versions.

## hunpoem_meter_analyzer

The folder hunpoem\_meter\_analyzer contains the program annotating the TEI XML files in the level3\_without\_meter folder with features
of both quantitative and qualitative meters. It categorizes poems as dactylic, anapestic, trochaic, or iambic, and provides a regularity score between 0 and 1, indicating how consistently the rhythm of the poem follows the recognized abstract quantitative meter. In addition, the program identifies qualitative meters that have an "aaaa..." or "abab..." structure. The file evaluation\_based\_on\_Szepes\_Szerdahelyi.xlsx contains evaluation data based on the example poems from the book Verstan by Erika Szepes and István Szerdahelyi, published in 1981.

# Elements and attributes

## Level1 -- annotation of structural units

- `<head>` : title
- `<lg>`: stanza
- `<l>`: line
- `<p>`: subtitle, epigraph, separator, editorial note


## Level2 -- tokenization and annotation of grammatical features of words

- `<w>` : word
- `<pc> `: punctuation mark
- `@lemma` : lemma
- `@pos `: part of speech
- `@msd` : morphosyntactic features ([Universal Dependencies](https://universaldependencies.org/))


## Level3 -- annotation of sound devices

- `@met `: meter
	- `Qual` : qualitative meter based on stressed and unstressed syllables
	- `Quan` : quantitative meter based on long and short syllables (possible values: iambic, trochaic, dactylic, anapestic)
	- `QuanScore` : score of quantitative meter (before 0.5, the poem does not really have any intended quantitative meter)
- `@rhyme `: rhyme pattern
- `@real `: rhythm (0: short syllable; 1: long syllable)
- `<spanGrp type="phonStructures">` : standoff annotation of the phonological features of words
- `<span>` : standoff annotation of the phonological features of a word
	content of `<span>` : phonological representation of the word
	- `c`: consonant
	- `b`: short back vowel
	- `B`: long back vowel
	- `f`: short front vowel
	- `F`: long front vowel
- `@subtype` : syllable number
- `@type` : type of vowels
	- `low`: only back vowels in the word
	- `high`: only front vowels in the word
	- `mixed`: front and back vowels in the word
- `@target` : the `xml:id` of the annotated word
- `<linkGrp type="rhymePairs">` : standoff annotation of rhyme pairs
- `<link>` : standoff annotation of a rhyme pair
- `@target` : xml:id of the two words in a rhyme pair
- `<spanGrp type="alliterations">` : standoff annotation of alliterations
- `<span>` : standoff annotation of an alliteration
- `@target` : `xml:id` of the words in the alliteration
- `@type` : structure of the alliteration
	- `a`: alliterating word
	- `n`: non-alliterating word (only one non-alliterating word can be between two alliterating words)

## Level4 -- conversion of the TEI format into non-TEI format 

By changing the name and the position of certain elements and attributes in level3 and by adding further annotations to the corpus, it is easier to process but cannot be expressed in valid TEI XML format.

- `@met_qual` : qualitative meter based on stressed and unstressed syllables (conversion of level3's `@met` in `<div>`)
- `@met_quan` : quantitative meter based on long and short syllables, possible values: iambic, trochaic, dactylic, anapestic (conversion of level3's `@met` in `<div>`)
- `@met_quanScore` : score of quantitative meter, before 0.5, the poem does not really have any intended quantitative meter (conversion of level3's `@met` in `<div>`)
- `@div_numStanza` : number of stanzas in the poem
- `@div_numLine `: number of lines in the poem
- `@div_numWord `: number of words in the poem
- `@div_numSyll `: number of syllables in the poem
- `@div_numShortSyll` : number of short syllables in the poem
- `@div_numLongSyll `: number of long syllables in the poem
- `@div_rhyme` : the rhyme pattern of the poem
- `@div_syllPattern` : syllable numbers of lines in the poem
- `@lg_numLine `: number of lines in the stanza
- `@lg_numWord `: number of words in the stanza
- `@lg_numSyll `: number of syllables in the stanza
- `@lg_numShortSyll` : number of short syllables in the stanza
- `@lg_numLongSyll `: number of long syllables in the stanza
- `@lg_syllPattern `: syllable numbers of lines in the stanza
- `@l_numWord `: number of words in the line
- `@l_numSyll `: number of syllables in the line
- `@l_numShortSyll` : number of short syllables in the line
- `@l_numLongSyll `: number of long syllables in the line 
- `@w_numSyll` : syllable number of word (conversion of level3's `@subtype` in `<span>`)
- `@phonType` : type of vowels in the word (conversion of level3's `@type` in `<span>`)
- `@phonStruct` : phonological representation of the word (conversion of level3's `<span>` content)
- `<rhymePairs> `: standoff annotation of rhyme pairs (conversion of level3's `<linkGrp type="rhymePairs">`)
- `<rhymePair>` : standoff annotation of a rhyme pair (conversion of level3's `<link>`)
- `<firstRhyme>`, `<secondRhyme>` : standoff annotation of the first and second word of a rhyme pair
	- content of `<firstRhyme>` and `<secondRhyme>` : the rhyming word form
- `@rhyme_lemma` : the lemma of the rhyming word
- `@rhyme_pos` : the part of speech of the rhyming word
- `@rhyme_msd` : the morphosyntactic features of the rhyming word (Universal Dependencies)
- `@rhyme_numSyll` : the syllable number of the rhyming word
- `@rhyme_phonType `: the type of vowels in the rhyming word
- `@rhyme_phonStruct` : the phonological representation of the rhyming word
- `<alliterations>` : standoff annotation of alliterations (conversion of level3's `<spanGrp type="alliterations">`)
- `<alliteration>` : standoff annotation of an alliteration (conversion of level3's `<span>`)
	- content of `<alliteration>` : the alliterating word forms
- `@allStruct` : structure of the alliteration (conversion of level3's `@type` in `<span>`)
- `@posTags` : the parts of speech of the alliterating words
- `@msdTags `: the morphosyntactic features of the alliterating words
- `@lemmas` : the lemmas of the alliterating words


# Contributors

- [Gábor Palkó](https://github.com/luhpeg) (design, data model)
- [Péter Horváth](https://github.com/horvathpeti99) (design, annotation scripts)
- [Balázs Indig](https://github.com/dlazesz) (linguistic analysis)
- [Zsófia Fellegi](https://github.com/zsofiafellegi) (TEI XML specification)
- [Eszter Szlávich](https://github.com/sz-eszter) (data checking)
- [Bajzát Tímea Borbála](https://github.com/bajzattimi) (data checking)
- [Zsófia Sárközi-Lindner](https://github.com/sarkozizsofia) (data checking)
- [Bence Vida](https://github.com/VidaBence) (data checking)
- [Aslihan Karabulut](https://github.com/arakaslihan) (data checking)
- [Mária Timári](https://github.com/MariaTimari) (data checking)

# Citing and License

If you use ELTE Poetry Corpus, please cite one of the following articles:

Horváth Péter – Kundráth Péter – Indig Balázs – Fellegi Zsófia – Szlávich Eszter – Bajzát Tímea Borbála – Sárközi-Lindner Zsófia – Vida Bence – Karabulut Aslihan – Timári Mária – Palkó Gábor 2022. ELTE Verskorpusz – a magyar kanonikus költészet gépileg annotált adatbázisa. In: Berend Gábor – Gosztolya Gábor – Vincze Veronika (szerk.): XVIII. Magyar Számítógépes Nyelvészeti Konferencia. Szeged: Szegedi Tudományegyetem TTIK, Informatikai Intézet. 375–388.

Horváth, Péter – Kundráth, Péter – Indig, Balázs – Fellegi, Zsófia – Szlávich, Eszter – Bajzát, Tímea Borbála – Sárközi-Lindner, Zsófia – Vida, Bence – Karabulut, Aslihan – Timári, Mária – Palkó, Gábor 2022. ELTE Poetry Corpus: A Machine Annotated Database of Canonical Hungarian Poetry. In: Calzolari, Nicoletta – Béchet, Frédéric – Blache, Philippe – Choukri, Khalid – Cieri, Christopher – Declerck, Thierry – Goggi, Sara – Isahara, Hitoshi – Maegaard, Bente – Mariani, Joseph – Mazo, Hélène – Odijk, Jan – Piperidis, Stelios (eds.): Proceedings of the 13th Conference on Language Resources and Evaluation (LREC 2022). Paris: European Language Resources Association (ELRA). 3471–3478.

The content of the repository is licensed under the [CC BY-NC-ND](https://creativecommons.org/licenses/by-nc-nd/4.0/) license.

All texts of the corpus are in the public domain.
