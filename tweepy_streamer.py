from tweepy import OAuthHandler
from tweepy import Stream
from tweepy import API
from tweepy import TweepError
import numpy as numpy
import pandas as pd
from environs import Env
import os
from datetime import datetime

from textblob import TextBlob

import re

import logging

# A logger is used to avoid writing everything to screen and it is easier to identify issues.
logging.basicConfig(filename='data/customer_xp.log',
                            filemode='a',
                            format='%(asctime)s,%(msecs)d %(name)s %(levelname)s %(message)s',
                            datefmt='%H:%M:%S',
                            level=logging.DEBUG)

logging.info("POC - Twitter API - Streamer")

LOGGER = logging.getLogger('CustomerXP')

## twitter client
class TwitterAPI():
    
    def __init__(self, twitter_user=None):
        self.twitter_authenticator = TwitterAuthenticator().authenticate_twitter_app()
        self.twitter_client = API(self.twitter_authenticator)
        self.twitter_user = twitter_user

    def get_twitter_client_api(self):
        return self.twitter_client

class TwitterAuthenticator():
    
    def authenticate_twitter_app(self):
        env = Env()
        env.read_env()
        consumer_key = os.getenv("CONSUMER_KEY")
        consumer_secret = os.getenv("CONSUMER_SECRET")
        access_token = os.getenv("ACCESS_TOKEN")
        access_token_secret = os.getenv("ACCESS_TOKEN_SECRET")
        auth = OAuthHandler(consumer_key, consumer_secret)
        auth.set_access_token(access_token, access_token_secret)
        return auth


class TwitterUtility():
    """
    function for analysing and categorizing contents from tweets
    The following regex just strips of an URL (not just http), any punctuations, User Names or Any non alphanumeric characters. It also separates the word with a single space. 
    """

    def tweet_remove_special_char_and_hyperlink(self,tweet):
        return ' '.join(re.sub("(@[A-Za-z0-9]+)|([^0-9A-Za-z \t])|(\w+:\/\/\S+)", " ", tweet).split())

    def analyse_sentiment(self, tweet):
        analysis = TextBlob(self.tweet_remove_special_char_and_hyperlink(tweet))
        return analysis.sentiment.polarity

    def tweets_to_data_frame(self,tweets):
        df = pd.DataFrame(data=[tweet.text for tweet in tweets], columns=['tweets'])
        df['id'] = numpy.array([tweet.id for tweet in tweets])
        df['len'] = numpy.array([len(tweet.text) for tweet in tweets])
        df['date'] = numpy.array([tweet.created_at for tweet in tweets])
        df['source'] = numpy.array([tweet.source for tweet in tweets])
        df['likes'] = numpy.array([tweet.favorite_count for tweet in tweets])
        df['sentiment'] = numpy.array([self.analyse_sentiment(tweet) for tweet in df['tweets']])
        return df

    def generate_data(self, user):
        path = 'data/'
        file = path + user + '.csv'
        
        file_exists = os.path.isfile(file)
        
        if(file_exists):
            utc_time = datetime.utcfromtimestamp(os.path.getmtime(file))

            today_time = datetime.utcnow()
            diff_day_delta = today_time - utc_time
            #if the file has been there for more than 12 hours, create it again.
            if(diff_day_delta.total_seconds()/60/60 > 12):
                LOGGER.debug("File exists but it is more than an 12 hours old -> Fetching the file again to get latest data. ")
                try:
                    twitter_api = TwitterAPI()
                    api = twitter_api.get_twitter_client_api()
                    tweets = api.user_timeline(screen_name=user,count=50)
                    df = self.tweets_to_data_frame(tweets)
                    df.to_csv(file)
                except TweepError as identifier:
                    LOGGER.debug(identifier)
                
            else:
                LOGGER.debug("Files exists and is less than an 12 hours, not fetching it for now.")
        else:
            LOGGER.debug("File does not exist. It has to be fetched.")
            try:
                twitter_api = TwitterAPI()
                api = twitter_api.get_twitter_client_api()
                tweets = api.user_timeline(screen_name=user,count=50)
                df = self.tweets_to_data_frame(tweets)
                df.to_csv(file)
            except TweepError as identifier:
                LOGGER.error(identifier)
        

    def validate_twitter_user(self,user):
        user_valid = False
        
        # first check for user in local file
        with open("data/users_valid.csv", "r") as f:
            data = f.readlines()
 
            for line in data:
                if line.capitalize().rstrip() == user.capitalize().rstrip():
                    user_valid = True
                    return user_valid
                
        with open("data/users_invalid.csv", "r") as f:
            data = f.readlines()
 
            for line in data:
                if line.capitalize().rstrip() == user.capitalize().rstrip():
                    user_valid = False
                    return user_valid


        twitter_api = TwitterAPI()
        api = twitter_api.get_twitter_client_api()
        
        try:
            u = api.get_user(user)
            LOGGER.debug(f"Twitter user id - {u.id_str}")
            LOGGER.debug(f"Twitter user screen name - {u.screen_name}")
            user_valid = True
            with open("data/users_valid.csv", "a") as f:
                f.writelines(u.screen_name + "\n")
        except TweepError:
            user_valid = False
            with open("data/users_invalid.csv", "a") as f:
                f.writelines(user + "\n")

        return user_valid
