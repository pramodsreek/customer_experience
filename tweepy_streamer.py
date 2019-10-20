#!/usr/bin/python3
"""
All the calls to twitter API are managed here. 
"""
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
logging.basicConfig(
    filename="data/customer_xp.log",
    filemode="a",
    format="%(asctime)s,%(msecs)d %(name)s %(levelname)s %(message)s",
    datefmt="%H:%M:%S",
    level=logging.DEBUG,
)

logging.info("POC - Twitter API - Streamer")

LOGGER = logging.getLogger("CustomerXP")


class TwitterApiException(Exception):
    """
    Defining a customised exception
    All the error with the API like the invalid API keys and connection errors are raised using this extended exception. The validation errors are riased using this exception as well. The exceptions are handled by the flask app or any other app using these functions. 
    """


## twitter client
class TwitterAPI:
    """
    Used to get an instance of Twitter Client.
    :param twitter_user: Optional parameter, useful if only one twitter handle is used and can be set.
    :type twitter_user: str

    :raises: :class:`TwitterApiException`: API keys are not valid.
    """

    def __init__(self, twitter_user=None):
        try:
            self.twitter_authenticator = (
                TwitterAuthenticator().authenticate_twitter_app()
            )
            self.twitter_client = API(self.twitter_authenticator)
            self.twitter_user = twitter_user
        except TwitterApiException as identifier:
            LOGGER.fatal("Constructor in TwitterAPI failed.")
            LOGGER.fatal(identifier)
            raise TwitterApiException(identifier)

    def get_twitter_client_api(self):
        """
        Gets an instance of twitter api client. * It can be used as a static Singleton later. 
        """
        return self.twitter_client


class TwitterAuthenticator:
    """
    Loads the keys from the environment. 
    """

    def authenticate_twitter_app(self):
        """
        Loads the keys from environment to create an Authenticator Object required for Twitter API to create client. 

        :returns: auth
        :rtype: OAuthHandler

        :raises: :class:`TwitterApiException`: API keys are not valid.
        """
        env = Env()
        env.read_env()
        consumer_key = os.getenv("CONSUMER_KEY")
        consumer_secret = os.getenv("CONSUMER_SECRET")
        access_token = os.getenv("ACCESS_TOKEN")
        access_token_secret = os.getenv("ACCESS_TOKEN_SECRET")

        if (
            consumer_key == None
            or consumer_secret == None
            or access_token == None
            or access_token_secret == None
        ):
            raise TwitterApiException("API keys not valid!")

        auth = OAuthHandler(consumer_key, consumer_secret)
        auth.set_access_token(access_token, access_token_secret)
        return auth


class TwitterUtility:
    """
    function for analysing and categorizing contents from tweets
    The following regex just strips of an URL (not just http), any punctuations, User Names or Any non alphanumeric characters. It also separates the word with a single space. 
    """

    def tweet_remove_special_char_and_hyperlink(self, tweet):
        """
        Strips charaters from a tweet or any string.

        :param tweet: a string of words.
        :type tweet: str
        """
        return " ".join(
            re.sub(
                "(@[A-Za-z0-9]+)|([^0-9A-Za-z \t])|(\w+:\/\/\S+)", " ", tweet
            ).split()
        )

    def analyse_sentiment(self, tweet):
        """
        Analysing the sentiment of a tweet. Polarity is used to measure sentiment. The values are between

        :param tweet: a string of words.
        :type tweet: str
        :returns: sentiment
        :rtype: float
        """
        analysis = TextBlob(self.tweet_remove_special_char_and_hyperlink(tweet))
        return analysis.sentiment.polarity

    def tweets_to_data_frame(self, tweets):
        """
        Converts tweets to tabular structure with rows and columns. Most of the data is returned from the API. The only additional column added is sentiment.

        :param tweets: a collection of tweets
        :type tweets: list
        :returns: df
        :rtype: DataFrame
        """
        df = pd.DataFrame(data=[tweet.text for tweet in tweets], columns=["tweets"])
        df["id"] = numpy.array([tweet.id for tweet in tweets])
        df["len"] = numpy.array([len(tweet.text) for tweet in tweets])
        df["date"] = numpy.array([tweet.created_at for tweet in tweets])
        df["source"] = numpy.array([tweet.source for tweet in tweets])
        df["likes"] = numpy.array([tweet.favorite_count for tweet in tweets])
        df["sentiment"] = numpy.array(
            [self.analyse_sentiment(tweet) for tweet in df["tweets"]]
        )
        return df

    def generate_data(self, user):
        """
        Collects tweets for a twitter handle or user and stores it as a file. To avoid too many connections to the external API, the files are cached locally on the server. They are refreshed after twelve hours. The file is only refreshed if there is request for the data in file belonging to a twitter handle. The files should be deleted frequently as it is unnecessary to store it other than using for caching purpose.

        :param user: twitter handle
        :type user: str

        """
        path = "data/"
        file = path + user + ".csv"

        file_exists = os.path.isfile(file)

        if file_exists:
            utc_time = datetime.utcfromtimestamp(os.path.getmtime(file))

            today_time = datetime.utcnow()
            diff_day_delta = today_time - utc_time
            # if the file has been there for more than 12 hours, create it again.
            if diff_day_delta.total_seconds() / 60 / 60 > 12:
                LOGGER.debug(
                    "File exists but it is more than an 12 hours old -> Fetching the file again to get latest data. "
                )
                self.save_data_to_file(user, file)
            else:
                LOGGER.debug(
                    "Files exists and is less than an 12 hours, not fetching it for now."
                )
        else:
            LOGGER.debug("File does not exist. It has to be fetched.")
            self.save_data_to_file(user, file)

    def save_data_to_file(self, user, file):
        """
        A method to fetch data and write to a csv file.

        :param user: twitter handle
        :type user: str
        :param file: name of the file
        :type file: str
        """
        try:
            twitter_api = TwitterAPI()
            api = twitter_api.get_twitter_client_api()
            tweets = api.user_timeline(screen_name=user, count=50)
            df = self.tweets_to_data_frame(tweets)
            df.to_csv(file)
        except TweepError as identifier:
            LOGGER.error(identifier)
        except TwitterApiException as identifier:
            LOGGER.error("generate data failed due to API.")
            LOGGER.error(identifier)

    def validate_twitter_user(self, user):
        """
        Checks if the twitter user is valid. Some of the twitter user names are stored locally to avoid checking it frequently. The issue with caching user handles locally is that, the change of status of user will not be recognised. It is better to check everytime to get the latest status and the data has to be deleted frequently.

        :param user: twitter handle
        :type user: str
        :returns: user_valid
        :rtype: bool

        :raises: :class:`TwitterApiException`: Connection to API fails.
        """
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

        try:
            twitter_api = TwitterAPI()
            api = twitter_api.get_twitter_client_api()
            u = api.get_user(user)
            LOGGER.debug(f"Twitter user id - {u.id_str}")
            LOGGER.debug(f"Twitter user screen name - {u.screen_name}")
            user_valid = True
            with open("data/users_valid.csv", "a") as f:
                f.writelines(u.screen_name + "\n")
        except TweepError as identifier:
            LOGGER.error(identifier.reason)
            LOGGER.error(f"Twitter returned error while user validation - {identifier}")
            # if the connection to twitter api fails
            if "Failed to send request:" in identifier.reason:
                raise TwitterApiException(identifier)

            user_valid = False
            with open("data/users_invalid.csv", "a") as f:
                f.writelines(user + "\n")
        except TwitterApiException as identifier:
            LOGGER.fatal("User could not be verified.")
            LOGGER.fatal(identifier)
            raise TwitterApiException(identifier)

        return user_valid
