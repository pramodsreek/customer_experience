from flask import Flask, render_template, url_for, redirect

import numpy as np
import pandas as pd
import tweepy_streamer

from bokeh.embed import components
from bokeh.plotting import figure
from bokeh.resources import INLINE
from bokeh.util.string import encode_utf8
from bokeh.models import ColumnDataSource
from bokeh.models.tools import HoverTool

from forms import TwitterHandleForm

import os
import re
from tracking_singleton import TrackingSingleton

import logging

# A logger is used to avoid writing everything to screen and it is easier to identify issues.
logging.basicConfig(filename='data/customer_xp.log',
                            filemode='a',
                            format='%(asctime)s,%(msecs)d %(name)s %(levelname)s %(message)s',
                            datefmt='%H:%M:%S',
                            level=logging.DEBUG)

logging.info("POC - Twitter API - Main")

LOGGER = logging.getLogger('CustomerXP')

app = Flask(__name__)
app.config['SECRET_KEY'] = 'customerxp'

@app.route('/', methods=['GET','POST'])
@app.route('/customerxp', methods=['GET','POST'])
def customerxp():
    form = TwitterHandleForm()
    LOGGER.debug(f"Parameters passed to customer xp (home) Twitter Handle {form.twitter_handle.data} Competitor Handle {form.competitors_twitter_handle.data} Errors {form.twitter_handle_error.data}")
    form.twitter_handle_error.data = " "
    
    tracking_singleton = TrackingSingleton.get_instance()
    if form.is_submitted():
        if form.validate():
            tracking_singleton.set_user_search_count()
            LOGGER.debug(f"User search count : {tracking_singleton.get_user_search_count()}")
            if (tracking_singleton.get_user_search_count() < 51):
                user_handle = ' '.join(re.sub("(@[A-Za-z0-9]+)|([^0-9A-Za-z \t])|(\w+:\/\/\S+)", " ", str(form.twitter_handle.data)).split())
                competitor_handle = ' '.join(re.sub("(@[A-Za-z0-9]+)|([^0-9A-Za-z \t])|(\w+:\/\/\S+)", " ", str(form.competitors_twitter_handle.data)).split())
                twitter_utility = tweepy_streamer.TwitterUtility()
                
                if (twitter_utility.validate_twitter_user(user_handle)):
                    twitter_utility.generate_data(user_handle)
                else:
                    form.twitter_handle_error.data = f"Twitter handle {user_handle} is not valid!"
                    return render_template('customerxp.html', form=form)
                
                if (twitter_utility.validate_twitter_user(competitor_handle)):
                    twitter_utility.generate_data(competitor_handle)
                else: 
                    form.twitter_handle_error.data = f"Twitter handle {competitor_handle} is not valid!"
                    return render_template('customerxp.html', form=form)
                
                return redirect(url_for('display', user_handle=user_handle, competitor_handle=competitor_handle))
            else:
                form.twitter_handle_error.data = f"Too many user searches - {tracking_singleton.get_user_search_count()}"
        else:
            form.twitter_handle_error.data = f"Form Valiadation Failed - Please check data. Twitter handle should be between 5 and 10 characters without any unnecessary characters."
    
    return render_template('customerxp.html', form=form)

@app.route('/display/<user_handle>/<competitor_handle>')
def display(user_handle, competitor_handle):
    LOGGER.debug(f"In display method user handle {user_handle} competitor handle {competitor_handle}")
    error = " "
    path = 'data/'
    file_extension = '.csv'

    file_user = path + user_handle + file_extension
    file_competitor = path + competitor_handle + file_extension

    file_user_exists = os.path.isfile(file_user)
    file_competitor_exists = os.path.isfile(file_competitor)

    tracking_singleton = TrackingSingleton.get_instance()
    tracking_singleton.set_data_search_count()

    if (tracking_singleton.get_data_search_count() > 50):
        error = f"Too many data fetches - {tracking_singleton.get_data_search_count()}"
        return render_template('error.html',error=error)
    elif (file_user_exists and file_competitor_exists):

        df_user = pd.read_csv(file_user,index_col=4, parse_dates=['date'])
        df_competitor = pd.read_csv(file_competitor,index_col=4, parse_dates=['date'])

        df_user_contact_centre = df_user[(df_user['sentiment'] < 0)]
        
        df_user_bot = df_user[(df_user['sentiment'] >= 0)]
        
        tweets_bot = [df_user.columns.values.tolist()] + df_user_bot.values.tolist()
        tweets_contact_centre = [df_user.columns.values.tolist()] + df_user_contact_centre.values.tolist()

        sample_user = df_user.sample(25)
        source_user = ColumnDataSource(sample_user)

        sample_competitor = df_competitor.sample(25)
        source_competitor = ColumnDataSource(sample_competitor)

        fig = figure(plot_width=700, plot_height=400, x_axis_type='datetime')

        fig.circle(x='date', y='sentiment',
            source=source_user,
            size=10, color='green', legend=user_handle)

        fig.circle(x='date', y='sentiment',
            source=source_competitor,
            size=10, color='red', legend=competitor_handle)
        
        fig.title.text = 'Customer Experience'
        fig.xaxis.axis_label = 'Date - Month/Day or Month/Year based on data sample'
        fig.yaxis.axis_label = 'Sentiment'

        fig.legend.location = "top_left"
        fig.legend.click_policy="hide"

        hover = HoverTool()
        hover.point_policy='snap_to_data'
        hover.line_policy='none'

        hover.tooltips = """
        <div>
            <div width: 100px word-wrap: break-word>
                <span style="font-size: 10px;">@tweets</span>
            </div>
        </div>
        """

        

        fig.add_tools(hover)

        # grab the static resources
        js_resources = INLINE.render_js()
        css_resources = INLINE.render_css()

        # render template
        script, div = components(fig)
        html = render_template(
            'cust_support_competition.html',
            plot_script=script,
            plot_div=div,
            js_resources=js_resources,
            css_resources=css_resources,
            tweets_bot=tweets_bot,
            tweets_contact_centre=tweets_contact_centre,
            user_handle=user_handle,
            competitor_handle=competitor_handle
        )
        return encode_utf8(html)
    else:
        error = "There is no data available for one of the twitter handles. Please visit home page and try again."
        return render_template('error.html',error=error)


if __name__ == "__main__":
    app.run(debug=True)