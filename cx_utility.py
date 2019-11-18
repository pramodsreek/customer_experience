#!/usr/bin/python3
"""
All the methods to write to a file, checking for data
in local file and validations is here.
"""
import re
import logging
import os
from datetime import datetime

import numpy as np
import pandas as pd

from textblob import TextBlob

from environs import Env

class CustomerExperienceException(Exception):
    """
    Defining a customised exception
    All the error with the API like the invalid API keys and
    connection errors are raised using this extended exception.
    The validation errors are riased using this exception as well.
    The exceptions are handled by the flask app or any other app
    using these functions.
    """

class TwitterUtility:

    """
    A class to keep track of the number of calls for data, to avoid
    too many requests when tested on a public server. This class uses
    Singleton pattern of object oriented programming. There is only
    one instance of the class.
    How would this count help? It helps to avoid too many requests
    for user_search or data_search for small scale application and
    the API has a rate limit. To get the right config
    values, rate limit should be known and the rate limit should be
    combined with time window.
    This class also has function for analysing and categorizing
    contents from tweets. The following regex just strips of an
    URL (not just http), any punctuations, User Names or Any
    non alphanumeric characters. It also separates the word
    with a single space.
    """

    # the single instance of class
    __instance = None

    @staticmethod
    def get_instance():
        """
        This is a static method that returns an instance of class and
        creates one if there is no instance of class exists. To get the
        instance TrackingSingleton.get_instance() method should be used.
        """
        if TwitterUtility.__instance is None:
            TwitterUtility()

        return TwitterUtility.__instance

    def __init__(self):
        """
        The constructor does not create an instance if there is
        already one created. It will throw an exception. If there
        isn't one, a new instance will be created.
        """
        if TwitterUtility.__instance is not None:
            raise Exception(
                "This class is a singleton for tracking, use getInstance()!"
            )

        self.user_search_count = 0
        self.data_search_count = 0
        # A logger is used to avoid writing everything to screen and
        # it is easier to identify issues.
        logging.basicConfig(
            filename="data/customer_xp.log",
            filemode="a",
            format="%(asctime)s,%(msecs)d %(name)s %(levelname)s %(message)s",
            datefmt="%H:%M:%S",
            level=logging.DEBUG,
        )

        logging.info("POC - Utility")

        self.logger = logging.getLogger("Utility")
        TwitterUtility.__instance = self

    def get_user_search_count(self):
        """
        A getter method to get the current user_search_count.
        """
        return self.user_search_count

    def get_data_search_count(self):
        """
        A getter method to get data search count.
        """
        return self.data_search_count

    def set_user_search_count(self):
        """
        A setter method that will increment the count of user_search.
        """
        self.user_search_count += 1

    def set_data_search_count(self):
        """
        A setter method that will increment the count of data_search.
        """
        self.data_search_count += 1

    def tweet_remove_special_char_and_hyperlink(self, tweet):
        """
        Strips charaters from a tweet or any string.

        :param tweet: a string of words.
        :type tweet: str
        """
        env = Env()
        env.read_env()
        cleaned_tweet = " ".join(re.sub(
            os.getenv("USER_CLEAN_REGEX"), " ", tweet).split())
        self.logger.debug("Cleaned tweet %s.", cleaned_tweet)
        return cleaned_tweet

    def analyse_sentiment(self, tweet):
        """
        Analysing the sentiment of a tweet.
        Polarity is used to measure sentiment.
        The values are between -1 and 1.

        :param tweet: a string of words.
        :type tweet: str
        :returns: sentiment
        :rtype: float
        """
        analysis = TextBlob(self.tweet_remove_special_char_and_hyperlink(tweet))
        return analysis.sentiment.polarity

    def tweets_to_data_frame(self, tweets):
        """
        Converts tweets to tabular structure with
        rows and columns. Most of the data is returned
        from the API. The only additional column added
        is sentiment.

        :param tweets: a collection of tweets
        :type tweets: list
        :returns: df_tweets
        :rtype: DataFrame
        """
        df_tweets = pd.DataFrame(data=[tweet.text for tweet in tweets], columns=["tweets"])
        df_tweets["id"] = np.array([tweet.id for tweet in tweets])
        df_tweets["len"] = np.array([len(tweet.text) for tweet in tweets])
        df_tweets["date"] = np.array([tweet.created_at for tweet in tweets])
        df_tweets["source"] = np.array([tweet.source for tweet in tweets])
        df_tweets["likes"] = np.array([tweet.favorite_count for tweet in tweets])
        df_tweets["sentiment"] = np.array(
            [self.analyse_sentiment(tweet) for tweet in df_tweets["tweets"]]
        )
        return df_tweets

    def is_data_in_cache(self, user):
        """
        Collects tweets for a twitter handle or user and
        stores it as a file. To avoid too many connections
        to the external API, the files are cached locally
        on the server. They are refreshed after twelve hours.
        The file is only refreshed if there is request for
        the data in file belonging to a twitter handle. The
        files should be deleted frequently as it is unnecessary
        to store it other than using for caching purpose.

        :param user: twitter handle
        :type user: str

        """
        path = "data/"
        file = path + user + ".csv"
        valid = False

        file_exists = os.path.isfile(file)

        if file_exists:
            utc_time = datetime.utcfromtimestamp(os.path.getmtime(file))

            today_time = datetime.utcnow()
            diff_day_delta = today_time - utc_time
            # if the file has been there for more than 12 hours, create it again.
            if diff_day_delta.total_seconds() / 60 / 60 < 12:
                self.logger.debug(
                    "File exists but it is more than an 12 hours old -> \
                    Fetching the file again to get latest data. "
                )
                valid = True
            else:
                self.logger.debug(
                    "Files exists and is less than an 12 hours, not fetching it for now."
                )
        else:
            self.logger.debug("File does not exist. It has to be fetched.")

        return valid

    def save_data(self, user, tweets):
        """
        A method to fetch data and write to a csv file.

        :param user: twitter handle
        :type user: str
        :param file: name of the file
        :type file: str
        """
        path = "data/"
        file = path + user + ".csv"

        df_tweets = self.tweets_to_data_frame(tweets)
        df_tweets.to_csv(file)

    def validate_user_in_list(self, user):
        """
        Checks if the twitter user is valid. Some of the twitter
        user names are stored locally to avoid checking it frequently.
        The issue with caching user handles locally is that,
        the change of status of user will not be recognised.
        It is better to check everytime to get the latest status
        and the data has to be deleted frequently.

        :param user: twitter handle
        :type user: str
        :returns: user_valid
        :rtype: bool

        :raises: :class:`CustomerExperienceException`: Connection to API fails.
        """
        user_valid = False

        # first check for user in local file
        with open("data/users_valid.csv", "r") as f_val_user:
            data = f_val_user.readlines()

            for line in data:
                if line.capitalize().rstrip() == user.capitalize().rstrip():
                    user_valid = True
                    self.logger.debug("user in valid list")
                    return user_valid

        with open("data/users_invalid.csv", "r") as f_inv_user:
            data = f_inv_user.readlines()

            for line in data:
                if line.capitalize().rstrip() == user.capitalize().rstrip():
                    user_valid = False
                    self.logger.debug("user in invalid list")
                    return user_valid

        return user_valid

    def write_to_user_list(self, user, valid):
        """
        A method to write users to valid and invalid list.
        Having a list locally helps to avoid calling api when
        unnecessary.

        :param user: twitter handle
        :type user: str
        :param valid: indicates the validity of user
        :type file: bool
        """
        if valid:
            with open("data/users_valid.csv", "a") as f_valid_user:
                f_valid_user.writelines(user + "\n")
            self.logger.debug("Added %s to valid list.", user)
        else:
            with open("data/users_invalid.csv", "a") as f_invalid_user:
                f_invalid_user.writelines(user + "\n")
            self.logger.debug("Added %s to invalid list.", user)
