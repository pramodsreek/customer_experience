#!/usr/bin/python3
"""
All the calls to twitter API are managed here.
"""
import os
import logging

from tweepy import OAuthHandler
from tweepy import API
from tweepy import TweepError
from environs import Env
from cx_utility import CustomerExperienceException
from cx_utility import TwitterUtility



## twitter client
class TwitterAPI:
    """
    Used to get an instance of Twitter Client.
    :param twitter_user: Optional parameter, useful
    if only one twitter handle is used and can be set.
    :type twitter_user: str

    :raises: :class:`CustomerExperienceException`: API keys are not valid.
    """

    def __init__(self):
        try:
            # A logger is used to avoid writing everything to screen and
            # it is easier to identify issues.
            logging.basicConfig(
                filename="data/customer_xp.log",
                filemode="a",
                format="%(asctime)s,%(msecs)d %(name)s %(levelname)s %(message)s",
                datefmt="%H:%M:%S",
                level=logging.DEBUG,
                )

            logging.info("POC - Twitter API")

            self.logger = logging.getLogger("TwitterAPI")
            self.authenticate_twitter_app()
            self.twitter_client = API(self.twitter_authenticator)
            self.twitter_utility = TwitterUtility.get_instance()
        except CustomerExperienceException as identifier:
            self.logger.fatal("Constructor in TwitterAPI failed.")
            self.logger.fatal(identifier)
            raise CustomerExperienceException(identifier)

    def get_twitter_client_api(self):
        """
        Gets an instance of twitter api client.
        * It can be used as a static Singleton later.
        """
        return self.twitter_client

    def get_tweets(self, user):
        """
        A method to fetch data and write to a csv file.

        :param user: twitter handle
        :type user: str
        :param file: name of the file
        :type file: str
        """
        try:
            api = self.get_twitter_client_api()
            # twitter user should be checked for null
            tweets = api.user_timeline(screen_name=user, count=50)
            self.twitter_utility.save_data(user, tweets)
        except TweepError as identifier:
            self.logger.error(identifier)

    def is_user_valid(self, user):
        """
        A method to check the validity of twitter handle using API.

        :param user: twitter handle
        :type user: str
        :returns: valid
        :rtype: bool
        """
        valid = False
        try:
            api = self.get_twitter_client_api()
            twitter_u = api.get_user(user)
            self.logger.debug("Twitter user id - %s", twitter_u.id_str)
            self.logger.debug("Twitter user screen name - %s", twitter_u.screen_name)
            valid = True
            self.twitter_utility.write_to_user_list(user, valid)
        except TweepError as identifier:
            self.logger.error(identifier.reason)
            self.logger.error("Twitter returned error while user validation - %s", identifier)
            # if the connection to twitter api fails
            if "Failed to send request:" in identifier.reason:
                raise CustomerExperienceException(identifier)
            self.twitter_utility.write_to_user_list(user, valid)

        return valid

    def authenticate_twitter_app(self):
        """
        Loads the keys from environment to create an
        Authenticator Object required for Twitter API to create client.

        :returns: auth
        :rtype: OAuthHandler

        :raises: :class:`CustomerExperienceException`: API keys are not valid.
        """
        env = Env()
        env.read_env()
        consumer_key = os.getenv("CONSUMER_KEY")
        consumer_secret = os.getenv("CONSUMER_SECRET")
        access_token = os.getenv("ACCESS_TOKEN")
        access_token_secret = os.getenv("ACCESS_TOKEN_SECRET")

        if (consumer_key is None or consumer_secret is None
                or access_token is None or access_token_secret is None):
            raise CustomerExperienceException("API keys not valid!")

        self.twitter_authenticator = OAuthHandler(consumer_key, consumer_secret)
        self.twitter_authenticator.set_access_token(access_token, access_token_secret)
