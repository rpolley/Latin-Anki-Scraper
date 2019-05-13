# Latin-Anki-Scraper
Given a csv file wordlist of latin words generates an Anki deck

The words in the list can use ancient roman style spelling or midieval style spelling.
Scrapes definitions for the words from an online dictionary, and generates production, recognition, and gender cards based off the dictionary entry.
If more than one entry is found for a word it will generate a note for each of them.

## Installing


depends on https://github.com/kerrickstaley/genanki and beautifulsoup
install genanki and place the scripts into a lib directory

## Usage


basic usage: python scraper.py \[flags\] csv_file deck_file
flags:

--name/-n: sets the name of the deck
--format/-f: can be either row_major or column_major, indicates whether the words are in the same row as each other or the same column
--indices/-i: a list of rows/columns containing data
--start/-s: the first row/column containing data
