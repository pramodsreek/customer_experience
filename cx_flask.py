#!/usr/bin/python3
"""
Flask app with two routes. The first route is home page
to enter data and the second route displays the processed
data. The first route collects twitter handles for the
user and the competitor and the second route displays
the positive + neutral sentiment tweets and negative
sentiment tweets. It also displays the comparison of
sentiment with a competitor using interactive
visualisation library. This is a POC. Tweets can be
filtered and categorised further.
"""
import os
import re

import logging
from environs import Env


from flask import Flask, render_template, url_for, redirect


import pandas as pd


from bokeh.embed import components
from bokeh.plotting import figure
from bokeh.resources import INLINE
from bokeh.util.string import encode_utf8
from bokeh.models import ColumnDataSource
from bokeh.models.tools import HoverTool

from cx_form_handler import TwitterAPI

from cx_utility import TwitterUtility
from cx_utility import CustomerExperienceException



from cx_flask_form import TwitterHandleForm



# A logger is used to avoid writing everything to screen and it is easier to identify issues.
logging.basicConfig(
    filename="data/customer_xp.log",
    filemode="a",
    format="%(asctime)s,%(msecs)d %(name)s %(levelname)s %(message)s",
    datefmt="%H:%M:%S",
    level=logging.DEBUG,
)

logging.info("POC - Twitter API - Flask App")

LOGGER = logging.getLogger("CustomerXP")

app = Flask(__name__)
app.config["SECRET_KEY"] = "customerxp"


@app.route("/", methods=["GET", "POST"])
@app.route("/customerxp", methods=["GET", "POST"])
def customerxp():
    """
    Returns a form to enter twitter handle and competitors
    twitter handle. After the form is submitted, this
    functions validates the twitter handles and fetches
    data for presentation from twitter. If there is an
    error, the error is added to form object and the form
    is displayed again with the error message for the user
    to correct and resubmit.
    """
    form = TwitterHandleForm()
    LOGGER.debug(
        f"Parameters passed to customer xp (home) Twitter\
            Handle {form.twitter_handle.data} Competitor\
                Handle {form.competitors_twitter_handle.data}\
                    Errors {form.twitter_handle_error.data}"
    )
    form.twitter_handle_error.data = " "

    cx_utility = TwitterUtility.get_instance()
    api = TwitterAPI()

    env = Env()
    env.read_env()

    

    if form.is_submitted():

        if form.validate() is False:
            form.twitter_handle_error.data = f"Form Validation\
                Failed - Please check data. Twitter handle should\
                be between 5 and 10 characters without any\
                unnecessary characters."
            return render_template("customerxp.html", form=form)

        cx_utility.set_user_search_count()
        LOGGER.debug(
            f"User search count : {cx_utility.get_user_search_count()}"
            )
        # Keep track of count of user searches.
        # A low count as it is just a POC and not
        # expecting a large number of calls. It can
        # be combined with time window, if the exact
        # rate limit of API is known.
        if cx_utility.get_user_search_count() > 50:
            form.twitter_handle_error.data = f"Too many user searches\
                - {cx_utility.get_user_search_count()}"
            return render_template("customerxp.html", form=form)    

        user_handle = " ".join(
            re.sub(os.getenv("USER_CLEAN_REGEX"),
            " ", str(form.twitter_handle.data),).split()
            )
        competitor_handle = " ".join(
            re.sub(os.getenv("USER_CLEAN_REGEX"),
            " ", str(form.competitors_twitter_handle.data),).split()
            )
                
        try:
            if cx_utility.validate_user_in_list(user_handle) is False:
                if api.is_user_valid(user_handle) is False:
                    form.twitter_handle_error.data = (
                        f"Twitter handle {user_handle} is not valid!"
                        )
                    return render_template("customerxp.html", form=form)

            if cx_utility.validate_user_in_list(competitor_handle) is False:
                if api.is_user_valid(competitor_handle) is False:
                    form.twitter_handle_error.data = (
                                f"Twitter handle {competitor_handle} is not valid!"
                            )
                    return render_template("customerxp.html", form=form)

            if cx_utility.is_data_in_cache(user_handle) is False:
                api.get_tweets(user_handle)

            if cx_utility.is_data_in_cache(competitor_handle) is False:
                api.get_tweets(competitor_handle)

            return redirect(
                url_for(
                        "display",
                        user_handle=user_handle,
                        competitor_handle=competitor_handle,
                    )
            )

        except CustomerExperienceException as identifier:
            form.twitter_handle_error.data = f"Fatal Error -\
                Please contact System Administrator - {identifier}"

    return render_template("customerxp.html", form=form)


@app.route("/display/<user_handle>/<competitor_handle>")
def display(user_handle, competitor_handle):
    """
    A function used to display data. If the twitter
    handles don't have data on the server or someone
    tries to call the method/page directly with invalid
    twitter handles, an error will be displayed.
    """
    LOGGER.debug(
        "In display method user handle %s competitor handle %s",
            user_handle, competitor_handle
    )
    error = " "
    path = "data/"
    file_extension = ".csv"
    # Modification and validation required
    file_user = path + user_handle + file_extension
    file_competitor = path + competitor_handle + file_extension

    file_user_exists = os.path.isfile(file_user)
    file_competitor_exists = os.path.isfile(file_competitor)

    cx_utility = TwitterUtility.get_instance()
    cx_utility.set_data_search_count()

    # Keep track of count of user searches. A low count as it
    # is just a POC and not expecting a large number of calls.
    # It can be combined with time window, if the exact rate
    # limit of API is known.
    if cx_utility.get_data_search_count() > 50:
        error = f"Too many data fetches - {cx_utility.get_data_search_count()}"
        return render_template("error.html", error=error)

    if file_user_exists and file_competitor_exists:
        try:
            df_user = pd.read_csv(file_user, index_col=4, parse_dates=["date"])
            df_competitor = pd.read_csv(file_competitor, index_col=4, parse_dates=["date"])

            df_user_contact_centre = df_user[(df_user["sentiment"] < 0)]

            df_user_bot = df_user[(df_user["sentiment"] >= 0)]

            tweets_bot = [df_user.columns.values.tolist()] + df_user_bot.values.tolist()
            tweets_contact_centre = [
                df_user.columns.values.tolist()
            ] + df_user_contact_centre.values.tolist()

            sample_user = df_user.sample(25)
            source_user = ColumnDataSource(sample_user)

            sample_competitor = df_competitor.sample(25)
            source_competitor = ColumnDataSource(sample_competitor)

            fig = figure(plot_width=700, plot_height=400, x_axis_type="datetime")

            fig.circle(
                x="date",
                y="sentiment",
                source=source_user,
                size=10,
                color="green",
                legend=user_handle,
            )

            fig.circle(
                x="date",
                y="sentiment",
                source=source_competitor,
                size=10,
                color="red",
                legend=competitor_handle,
            )

            fig.title.text = "Customer Experience"
            fig.xaxis.axis_label = "Time Window"
            fig.yaxis.axis_label = "Sentiment"

            fig.legend.location = "top_left"
            fig.legend.click_policy = "hide"

            hover = HoverTool()
            hover.point_policy = "snap_to_data"
            hover.line_policy = "none"

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
                "cust_support_competition.html",
                plot_script=script,
                plot_div=div,
                js_resources=js_resources,
                css_resources=css_resources,
                tweets_bot=tweets_bot,
                tweets_contact_centre=tweets_contact_centre,
                user_handle=user_handle,
                competitor_handle=competitor_handle,
            )
            return encode_utf8(html)

        except ValueError as error:
            error = "There is no data available for one of the twitter handles. Please check data and try again."
            return render_template("error.html", error=error)

    else:
        error = "There is no data available for one of the twitter\
        handles. Please visit home page and try again."
        return render_template("error.html", error=error)


# Helps to run in debug more as an application while development to avoid frequent restarts.
if __name__ == "__main__":
    app.run(debug=True)
