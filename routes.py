from config import application, db
from flask import send_file, render_template, url_for, flash, redirect, request, abort, render_template_string, session, \
    make_response
from forms import BasicQueryForm
import json

from utils.db_functions import connect_db, get_column_names, query_database, list_to_json
from utils.database import QueryParser,QueryFilter
from utils.utils import truncate
import pandas as pd




# @application.route('/')
# def main():
#     """
#     This function redirects the root page to the home route.
#     :return: redirect to home
#     """
#     return redirect(url_for("home"))

# TODO may want to seperate this out and make the querying part into an api
@application.route('/', methods=["GET", "POST"])
def base():
    """
    - look at google sheet for core/advance fields
    - may have to choose use judgement for core fields; choose some that are obvious

    - lazy loading of js functions (load when need them)

    - if we are limiting the amount of data we can query, then you may be able to simply save it and send it through the csv route
    """

    basic_form = BasicQueryForm()
    if request.method == "POST":

        raw_data = request.json["data"]
        raw_data['where'] = QueryFilter(raw_data['where']).reformat_date(date_column='speech_date', from_format='%b %d, %Y')
        query, columns = QueryParser(raw_data, "advance_data_view", 500).parse()
        # print('query is:')
        # print(query)
        results = db.query(query, connect_and_close=True)
        # print('results are:')
        # print(results)

        if len(results) < 1:
            return json.dumps({"data": "no records found", "length": 0, "query": query})
        results_list = db.query_results_to_json(results, columns)

        if "speech_text" in results_list[0].keys():
            for item in results_list:
                item["speech_text_truncated"] = truncate(item["speech_text"])

        session["current_query"] = query
        session['current_columns'] = columns

        return json.dumps({"data": results_list, "length": len(results_list), "query": query})
    else:
        return render_template("home.html", basic_form=basic_form)


#
@application.route("/api/v1/database/csv", methods=["GET"])
def csv():
    # def pandas_csv_to_csv_string(df: pd.DataFrame):
    print('in here')
    try:
        query = session['current_query']
        columns = session['current_columns']
    except KeyError:
        return {'data': 'no query found'}

    results = db.query(query, connect_and_close=True)
    results_list = db.query_results_to_json(results, columns)

    df = pd.DataFrame(data=results_list)

    response = make_response(df.to_csv())
    cd = 'attachment; filename=query_result.csv'
    response.headers['Content-Disposition'] = cd
    response.mimetype = 'text/csv'

    return response


#

@application.route('/api/v1/database/names', methods=["GET"])
def names():
    query = "SELECT full_name FROM person_list"
    results = db.query(query, connect_and_close=True)

    return json.dumps({name[0]: None for name in results})
