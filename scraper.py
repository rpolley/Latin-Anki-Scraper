from requests import get
from requests.exceptions import RequestException
from contextlib import closing
from bs4 import BeautifulSoup
from time import sleep
from os.path import isfile

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
    return "http://old.reddit.com"+name+"/top/?sort=top&t=all"

def get_html_from_url(url):
    raw_html = simple_get(url)
    if(raw_html == None):
        return None
    tree_html = BeautifulSoup(raw_html, 'html.parser')
    return tree_html
    

