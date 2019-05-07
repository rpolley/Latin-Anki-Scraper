from requests import get
from requests.exceptions import RequestException
from contextlib import closing
from bs4 import BeautifulSoup
from time import sleep
from os.path import isfile
from parse import parse
from lib.genanki import *
import random
import csv
import argparse
from sys import argv

latin_noun = Model(
    2011023118,
    'Latin Noun',
    fields = [
        {'name': 'latin'},
        {'name': 'english'},
        {'name': 'gender'},
        {'name': 'notes'}
    ],
    templates=[
        {
            'name': 'comprehension',
            'qfmt': '{{latin}} {{gender}}.',
            'afmt': '{{latin}} {{gender}}.<br><hr id="answer">{{english}}<br>{{notes}}'
        },
        {
            'name': 'production',
            'qfmt': '{{english}}',
            'afmt': '{{english}}<br><hr id="answer">{{latin}} {{gender}}.<br>{{notes}}'
        },
        {
            'name': 'gender',
            'qfmt': 'what gender is {{latin}}',
            'afmt': 'what gender is {{latin}}<br><hr id="answer">{{gender}}.'
        }
    ])

latin = Model(
    1377365221,
    'Latin',
    fields = [
        {'name': 'latin'},
        {'name': 'english'},
        {'name': 'notes'}
    ],
    templates=[
        {
            'name': 'comprehension',
            'qfmt': '{{latin}}',
            'afmt': '{{latin}}<br><hr id="answer">{{english}}<br>{{notes}}'
        },
        {
            'name': 'production',
            'qfmt': '{{english}}',
            'afmt': '{{english}}<br><hr id="answer">{{latin}}<br>{{notes}}'
        }
    ])

def simple_get(url):
    try:
        #pretend to be firefox
        ua = 'Mozilla/5.0 (X11; Linux x86_64; rv:10.0) Gecko/20100101 Firefox/10.0'
        with closing(get(url, headers = {'User-agent': ua}, stream=True)) as resp:
            if is_good_response(resp):
                return resp.content
            else:
                log_error(resp)
                return None
    except RequestException as e:
        log_error('Error during requests to {0} : {1}'.format(url, str(e)))

def is_good_response(resp):
    content_type = resp.headers['Content-Type'].lower()
    return (resp.status_code == 200
            and content_type is not None
            and content_type.find('html') > -1)
     
def log_error(e):
    print(e)

class Entry():
    def __init__(self, word, speech_part, grammar, definitions):
        self.word = word
        self.speech_part = speech_part
        self.grammar = grammar
        self.definitions = definitions
    def __repr__(self):
        return str(vars(self))

def get_entries(target,t_html):
    entries = list(t_html.select(".entry"))
    entries_parsed = []
    for entry in entries:
        word = entry.select(".banner h3 a")[0].get_text()
        principle_parts = word.split(", ")
        if(target not in principle_parts):
            continue
        grammatical_points = {}
        speech_part = entry.select(".speech")[0].get_text()
        grammars = entry.select(".grammar ul li")
        if(len(grammars)>0):
            for g_item in grammars:
                key = g_item.select(".name")[0].get_text()
                value = g_item.select(".value")[0].get_text()
                grammatical_points[key] = value
        definitions = list(entry.select(".definitions ol li"))
        definitions_parsed = []
        for definition in definitions:
            definitions_parsed.append(definition.get_text())
        entries_parsed.append(Entry(word,speech_part,grammatical_points,definitions_parsed))
    return entries_parsed
            
        
def get_next_url(t_html):
    buttons = list(t_html.select(".next-button a"))
    if(len(buttons)>0):
        next = buttons[0]
        return next['href']
    else:
        return None
    
def url_from_word(name):
    return "http://latin-dictionary.net/search/latin/"+name

def get_html_from_url(url):
    raw_html = simple_get(url)
    if(raw_html == None):
        return None
    tree_html = BeautifulSoup(raw_html, 'html.parser')
    return tree_html
    
def generate_deck(name,entries):
    global latin
    global latin_noun
    
    deck_id = random.randrange(1<<30,1<<31)
    deck = Deck(deck_id,name)
    
    for entry in entries:
        model = latin
        fields = [entry.word, "; ".join(entry.definitions)]
        if(entry.speech_part == 'noun'):
            model = latin_noun
            if('gender' in entry.grammar.keys()):
                gender_long = entry.grammar['gender']
                gender = ""
                if(gender_long == "masculine"):
                    gender = "m"
                elif(gender_long == "feminine"):
                    gender = "f"
                elif(gender_long == "neuter"):
                    gender = "n"
                fields.append(gender)
        fields.append("") #todo: format grammar into 
        note = Note(model=model,fields=fields)
        deck.add_note(note)
    return deck
        
    
"""
convert ancient roman style latin text to modern style latin text
"""
def roman_to_modern(text):
    #the romans wrote in all caps, but we don't want that
    text = text.lower()
    #some word lists provide a declension number affixed to the word, remove that
    #since we're scraping the principle parts from the dictionary instead
    text = parse("{word:l}{}",text+" ")["word"]
    #the romans used the letter v to write both u and v, but the dictionaries we're using dont
    #thankfully we can convert between the two based on some linquistic rules
    
    #first add in some word boundary symbols
    text = list("#"+text+"#")
    
    vowels = "aeiouv"
    for i in range(1,len(text)-1):
        prev = text[i-1]
        curr = text[i]
        next = text[i+1]
        consonantal = False
        ambiguous = False        
        
        if(len(prev)>1):
            ambiguous = True
        else:
            if(prev == "#" and next in vowels): # #_V
                consonantal = True
            elif(prev in vowels and not next not in vowels): # V_V, V_#
                consonantal = True
            elif(prev not in vowels and prev != "#" and next in vowels): # C_V
                 ambiguous = True
            
        
        #sometimes i's are consonants, but they follow the same rules, so replace them with j
        if(curr == "i"):
            if(ambiguous):
                text[i] = ("i","j")
            elif (consonantal):
                text[i] = "j"
            
        
        #replace the v's with u's
        if(curr == "v"):
            if(ambiguous):
                text[i] = ("v","u")
            elif (not consonantal):
                text[i] = "u"
            
    return enumerate_ambiguities(text[1:-1])
    
def enumerate_ambiguities(text):
    l = [""]
    for i in range(len(text)):
        ln = []
        for word in l:
            for item in list(text[i]):
                ln.append(word+item)
        l = ln
    return l

def deck_from_words(name, word_list):
    entries = []
    for word in word_list:
        word_entries = lookup_word(word)
        entries.extend(word_entries)
    return generate_deck(name, entries)
        

def lookup_word(word):
    words_modern = roman_to_modern(word)
    entries = []
    
    print(words_modern)
    for word_modern in words_modern:
        url = url_from_word(word_modern)
        html = get_html_from_url(url)
        entries.extend(get_entries(word_modern,html))
    return entries

def deck_file_from_csv(words_csv, target_file, name=None, data_indices=[0], data_format="column_major", data_start_index=1):
    wordlist = []
    with open(words_csv, newline="") as csvfile:
        dialect = csv.Sniffer().sniff(csvfile.read(1024)) #attempt to guess the format of the file
        csvfile.seek(0)
        csvreader = csv.reader(csvfile, dialect)
        if(data_format == "column_major"):
            i = 0
            for row in csvreader:
                if(i>=data_start_index):
                    for j in data_indices:
                        wordlist.append(row[j])
                i += 1
        elif(data_format == "row_major"):
            i = 0
            for row in csvreader:
                if i in data_indices:
                    for word in row[data_start_index:]:
                        wordlist.append(word)
                i += 1
    if(not name):
        name=words_csv.split(".")[0]
    deck = deck_from_words(name,wordlist)
    Package(deck).write_to_file(target_file)

parser = argparse.ArgumentParser(description="Build and Anki Deck from a csv wordlist", prog="PROG")
parser.add_argument('infile', metavar='INFILE')
parser.add_argument('outfile', metavar='OUTFILE')
parser.add_argument('--format','-f', choices=["column_major","row_major"],default="column_major")
parser.add_argument('--indices', '-i', type=int,default=[0], nargs='*')
parser.add_argument('--start', '-s', default=1,type=int, nargs=1)
parser.add_argument('--name', '-n', nargs=1)

args = parser.parse_args(argv[1:])

deck_file_from_csv(args.infile,args.outfile,name=args.name[0], data_indices=args.indices,data_start_index=args.start,data_format=args.format)
