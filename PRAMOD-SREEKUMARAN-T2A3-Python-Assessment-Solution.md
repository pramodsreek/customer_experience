

### Overview and Application Structure

The Customer Experience (CX) App uses an algorithm that allows two-way communication to occur between both the application and the Twitter API and a web browser and the application. The CX App provides a web page with a form to enter the twitter handle of the business, twitter handle of the businesses competitor and a button to request for the most recent tweets on the timeline. The application fetches the tweets from Twitter API, processes and classifies tweets based on the customers sentiment.  The application loops over the tweets, generates tweets as html and renders on the page for the contact centre to contact customer to resolve their issue and create a positive sentiment for the brand. The tweets are also plotted on an interactive visual display showing a comparison with the competing brand to understand competing brands customers for competitive advantage. 

### Algorithm

The algorithm takes the data in JSON from the Twitter API and parses the tweets to extract necessary fields and stores in a tabular format as rows and columns in a DataFrame. DataFrame is a data structure in pandas python library used for data manipulation and analysis. The algorithm performs sentiment analysis on each tweet using TextBlob, which is a simple natural language processing library in Python. The algorithm groups the tweets based on the positive and negative sentiments. The polarity of a sentiment is a float between -1 and 1. Frustrated customers write tweets are of negative polarity. Negative tweets are listed separately for contact centre to handle and create a positive image for a brand.
The algorithm extracts the dates and sentiments of the business and its competitor and plots it on an interactive visual display using bokeh python package. 

### Inputs and Outputs

Flask forms handle inputs from the user using fields to enter data and submit. Flask renders output to user on html pages. 
HTTP Get and Post methods are used. Flask passes on the input to application using method calls on classes, that communicates with Twitter Rest API using Tweepy. Tweepy is a Python library for accessing the Twitter API.

### Structure

CX App has two main Python programs. One program is Flask app with all the route to main form to get input and route to display output to user in html. Flask app uses templates.  

The core program manages the interaction with the Twitter API using Tweepy. It is a collection of classes and methods to fetch tweets, process and store them. Tweets linked to twitter handle are stored in csv files to avoid calling the api multiple times for a single twitter handle.  This is an alternative to caching. The cache is only valid for 12 hours. 

### Dependencies

The application's core dependency is Python 3.7 and its standard libraries. These are other Python packages used and they are listed below.

logging - It is part of Python standard library and is used output log statement to file
re - It is part of Python standard library and is used for stripping special charaters from tweets to produce accurate or closer to accurate sentiment polarity
os - To read and write files with twitter user and tweet data
flask - Web framework used by the application
Flask-WTF - Provides flexible flask forms which can easily include form components provided by other packages
tweepy - Python library used for accessing Twitter API
pandas - For manipulation of tweets and analysis
environs - To get the API keys from .env file
DateTime - To calculate the age of the file in hours
textblob - For sentiment analysis of tweets
bokeh - Interactive visual plotting of sentiments 
wtforms - Validation of fields on forms