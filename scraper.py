from requests import get
from requests.exceptions import RequestException
from contextlib import closing
from bs4 import BeautifulSoup
from time import sleep
from os.path import isfile
from parse import *

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

def get_next_url(t_html):
    buttons = list(t_html.select(".next-button a"))
    if(len(buttons)>0):
        next = buttons[0]
        return next['href']
    else:
        return None
    
def url_from_word(name):
    return "http://www.latin-dictionary.net/search/latin/"+name

def get_html_from_url(url):
    raw_html = simple_get(url)
    if(raw_html == None):
        return None
    tree_html = BeautifulSoup(raw_html, 'html.parser')
    return tree_html
    
"""
convert ancient roman style latin text to modern style latin text
"""
def roman_to_modern(text):
    #the romans wrote in all caps, but we don't want that
    text = text.lower()
    #some word lists provide a declension number affixed to the word, remove that
    #since we're scraping the principle parts from the dictionary instead
    text = parse("{word:l}{}",text)["word"]
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
        
        if(prev == "#" and next in vowels): # #_V
            consonantal = True
        elif(prev in vowels and not next not in vowels): # V_V, V_#
            consonantal = True
        elif(prev not in vowels and prev != "#" and next == "#"): # C_#
            consonantal = True
        
        if(curr == "u" and prev == "q" or prev == "c"):
            consonantal = False
        
        #sometimes i's are consonants, but they follow the same rules, so replace them with j
        if (consonantal and curr == "i"):
            text[i] = "j"
        
        #replace the v's with u's
        if (not consonantal and curr == "v"):
            text[i] = "u"
    return "".join(text[1:-1])
    
