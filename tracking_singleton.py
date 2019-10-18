class TrackingSingleton:
   '''
   A class to keep track of the number of calls for data, to avoid too many requests when tested on a public server. This class use Singleton pattern of object oriented programming. There is only one instance of the class.
   
   How would this class help? It helps to avoid too many requests for user_search or data_search for small scale application and when there is a rate limit on the API. To get the right config values, rate limit should be know and combined with time window. 
   '''
   # the single instance of class
   __instance = None

   @staticmethod 
   def get_instance():
      """ This is a static method that returns an instance of class and creates one if there is no instance of class exists. To get the instance TrackingSingleton.get_instance() method should be used."""
      if TrackingSingleton.__instance == None:
         TrackingSingleton()
      return TrackingSingleton.__instance

   def __init__(self):
      """ The constructor does not create an instance if there is already one created. It will throw an exception. If there isn't one, a new instance will be created. """
      if TrackingSingleton.__instance != None:
         raise Exception("This class is a singleton for tracking, use getInstance()!")
      else:
         self.user_search_count = 0
         self.data_search_count = 0
         TrackingSingleton.__instance = self

   def get_user_search_count(self):
      '''
      A getter method to get the current user_search_count.
      '''
      return self.user_search_count

   def get_data_search_count(self):
      '''
      A getter method to get data search count.
      '''
      return self.data_search_count

   def set_user_search_count(self):
      '''
      A setter method that will increment the count of user_search.
      '''
      self.user_search_count += 1

   def set_data_search_count(self):
      '''
      A setter method that will increment the count of data_search.
      '''
      self.data_search_count += 1
