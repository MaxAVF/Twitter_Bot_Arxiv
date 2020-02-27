import tweepy as tp
import time
import os
import urllib
import datetime
from collections import Counter, defaultdict
import xml.etree.ElementTree as ET
import urllib.error,urllib.request
import pyparsing
import re

import matplotlib.pylab as plt
import pandas as pd
import numpy as np
from apscheduler.schedulers.blocking import BlockingScheduler
from datetime import date,timedelta

import textwrap

plt.style.use('seaborn')

# credentials to login to twitter api
consumer_key = os.environ['CONSUMER_KEY']
consumer_secret = os.environ['CONSUMER_SECRET']
access_token = os.environ['ACCESS_TOKEN']
access_secret = os.environ['ACCESS_SECRET']

# login to twitter account api
auth = tp.OAuthHandler(consumer_key, consumer_secret)
auth.set_access_token(access_token, access_secret)
api = tp.API(auth)


                                 
OAI = "{http://www.openarchives.org/OAI/2.0/}"
ARXIV = "{http://arxiv.org/OAI/arXiv/}"

def harvest(arxiv_set="math",date='2020-01-10'):
    df = pd.DataFrame(columns=("title", "abstract", "categories", "created", "id", "doi",'authors'))
    base_url = "http://export.arxiv.org/oai2?verb=ListRecords&"
    url = (base_url +
           "from={}&until={}&".format(date,date) +
           "metadataPrefix=arXiv&set=%s"%arxiv_set)
    
    while True:
        print("fetching", url)
        try:
            response = urllib.request.urlopen(url)
            
        except urllib.error.HTTPError as e:
            if e.code == 503:
                to = int(e.hdrs.get("retry-after", 30))
                print("Got 503. Retrying after {0:d} seconds.".format(to))

                time.sleep(to)
                continue
                
            else:
                raise
            
        xml = response.read()

        root = ET.fromstring(xml)
        if root.find(OAI+'ListRecords') is not None:
            for record in root.find(OAI+'ListRecords').findall(OAI+"record"):
                arxiv_id = record.find(OAI+'header').find(OAI+'identifier')
                meta = record.find(OAI+'metadata')
                info = meta.find(ARXIV+"arXiv")
                created = info.find(ARXIV+"created").text
                created = datetime.datetime.strptime(created, "%Y-%m-%d")
                categories = info.find(ARXIV+"categories").text


                authors=info.find(ARXIV+"authors")
                authors_list=[]

                for author in authors.findall(ARXIV + 'author'):
                     try: 
                      fullname= author.find(ARXIV + 'forenames').text + ' ' + author.find(ARXIV + 'keyname').text
                     except:
                      try: 
                       fullname=author.find(ARXIV + 'forenames').text
                      except:
                       fullname=author.find(ARXIV + 'keyname').text  
                     authors_list.append(fullname)


                doi = info.find(ARXIV+"doi")
                if doi is not None:
                    doi = doi.text.split()[0]

                contents = {'title': info.find(ARXIV+"title").text,
                            'id': info.find(ARXIV+"id").text,#arxiv_id.text[4:],
                            'abstract': info.find(ARXIV+"abstract").text.strip(),
                            'created': created,
                            'categories': ",".join(categories.split()),
                            'doi': doi,
                            'authors': ", ".join(authors_list),
                            }

                df = df.append(contents, ignore_index=True)

            # The list of articles returned by the API comes in chunks of
            # 1000 articles. The presence of a resumptionToken tells us that
            # there is more to be fetched.
            token = root.find(OAI+'ListRecords').find(OAI+"resumptionToken")
            if token is None or token.text is None:
                break

            else:
                url = base_url + "resumptionToken=%s"%(token.text)
        else:
          return df
            
    return df[(datetime.datetime.strptime(date,"%Y-%m-%d")-pd.to_datetime(df['created'],"%Y-%m-%d"))<timedelta(days=30)]
 
def curator():
  df_math=harvest(arxiv_set='math',date=(date.today()- timedelta(days = 1)).strftime("%Y-%m-%d"))
  time.sleep(5)
  df_cs=harvest(arxiv_set='cs',date=(date.today()- timedelta(days = 1)).strftime("%Y-%m-%d"))
  time.sleep(5)
  df_physics=harvest(arxiv_set='physics',date=(date.today()- timedelta(days = 1)).strftime("%Y-%m-%d"))
  df= pd.concat([df_math,df_cs,df_physics])
  
  with open('list_keywords.txt', 'r') as f:
    list_keywords = [line.rstrip('\n') for line in f] 
  
  regstr = '|'.join(list_keywords)
  df=df[df['abstract'].str.lower().str.contains(regstr)]
  df.drop_duplicates(inplace=True)
  return df


def latex_curator(text):
    text=text.replace('\n',' ')
    text=re.sub(' {2,}',' ',text)
    pattern = re.compile('\$(.*?)[\$]')
    math_mode = re.findall(pattern, text)
    for formula in math_mode:
       text=text.replace(formula,formula.replace(' ', ''))
    return text

def render_latex(title,formula,authors,name, fontsize=12, dpi=300, format_='svg'):
    """Renders LaTeX formula into image.
    """
    fig = plt.figure(figsize=(9, 5))
    ax = fig.add_axes([0,0,1,1])
    ax.grid(False)
    ax.autoscale(True)
    fig.dpi=dpi
    fig.text(0.5,0.86,u'{}'.format('\n'.join(textwrap.wrap(latex_curator(title),width=60,break_long_words=False, replace_whitespace=False))), fontsize=fontsize+8, weight='bold', \
             horizontalalignment='center',verticalalignment='bottom')
    fig.text(0.5,0.84, u'{}'.format('\n'.join(textwrap.wrap(authors.upper().replace('\n', ' '),break_long_words=False, replace_whitespace=False))), fontsize=fontsize,fontstyle='italic',horizontalalignment='center',verticalalignment='top')
    fig.text(0.5,0.75, u'{}'.format('\n'.join(textwrap.wrap(latex_curator(formula),width=100,break_long_words=False, replace_whitespace=False))), \
             fontsize=fontsize,horizontalalignment='center',verticalalignment='top')
    fig.savefig('abstract{}.png'.format(name), dpi=fig.dpi, transparent=False, format=format_)
    plt.close(fig)
    return 'abstract{}.png'.format(name)

  
  
  
def tweet_daily():
  df=curator()
  for index, row in df.iterrows():
    try:
        img=render_latex(title=row['title'],
            formula=row['abstract'],authors=row['authors'],name=index,
            fontsize=10, dpi=300, format_='png')
        api.update_with_media(img, status='𝗧𝗶𝘁𝗹𝗲: ' + row['title'].replace('\n ','') + '.\n' + '𝗔𝘂𝘁𝗵𝗼𝗿𝘀: ' + row['authors'] + '.\n' + 'https://arxiv.org/abs/'+ row['id'])
        os.remove(img)
        time.sleep(60*20)
    except tp.TweepError as error:
        if error.api_code == 187:
            pass
        else:
            raise error
    except:
        pass
    
                             
if __name__ == "__main__":  
   scheduler = BlockingScheduler()
   scheduler.add_job(tweet_daily, 'interval',hours=24,next_run_time=datetime.datetime.now())
   scheduler.start()
