# Twitter_Bot_Arxiv
[![GitHub issues](https://img.shields.io/github/issues/MaxAVF/Twitter_Bot_Arxiv)](https://github.com/MaxAVF/Twitter_Bot_Arxiv/issues)
[![Twitter](https://img.shields.io/twitter/url?label=%40arXiv_CT&style=social&url=https%3A%2F%2Ftwitter.com%2FarXiv_CT)](https://twitter.com/intent/tweet?text=Wow:&url=https%3A%2F%2Fgithub.com%2FMaxAVF%2FTwitter_Bot_Arxiv)

Daily tweets of abstracts of papers submitted to http://arxiv.org. 
Create your own Twitter bot.

## Prerequisites

tweepy

apscheduler

## Deployment
You can clone this repository and install all the necesary dependencies 

```
git clone https://github.com/MaxAVF/Twitter_Bot_Arxiv.git
pip install -r /Twitter_Bot_Arxiv/requirements.txt
```
Before you launch the script, make sure to modify these parameter with your credentials to login to twitter api

```
consumer_key = os.environ['CONSUMER_KEY']
consumer_secret = os.environ['CONSUMER_SECRET']
access_token = os.environ['ACCESS_TOKEN']
access_secret = os.environ['ACCESS_SECRET']
```
Also, you have to add the keywords you want to match to the papers, one per line, in the file list_keywords.txt.

Now you can run the main script, this will process the submissions made to arxiv.org the day before, filter all those than match any of the keywords you provided before, and start posting tweets for every submission, every 20 minutes. This script will run every 24 hours.
```
python main.py
```



## Improve this project
Every contribution to this project is more than welcome! By either adding new features or modifying existing ones, please modify the code of your local repository and commit it. Then, create a pull request to this project, and we will review your request.
