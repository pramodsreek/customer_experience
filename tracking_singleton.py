class TrackingSingleton:
   '''
   A class to keep track of the number of calls for data, to avoid too many requests when tested on a public server. 
   '''
   __instance = None
   @staticmethod 
   def get_instance():
      """ Static access method. """
      if TrackingSingleton.__instance == None:
         TrackingSingleton()
      return TrackingSingleton.__instance
   def __init__(self):
      """ Virtually private constructor. """
      if TrackingSingleton.__instance != None:
         raise Exception("This class is a singleton for tracking, use getInstance()!")
      else:
         self.user_search_count = 0
         self.data_search_count = 0
         TrackingSingleton.__instance = self
   def get_user_search_count(self):
      return self.user_search_count
   def get_data_search_count(self):
      return self.data_search_count
   def set_user_search_count(self):
      self.user_search_count += 1
   def set_data_search_count(self):
      self.data_search_count += 1
