from flask import Flask, render_template, url_for, flash, redirect, jsonify, session, request
from datetime import datetime, timedelta
from math import ceil
from threading import Thread
import json

# imports from my project
from core_algos.formulas import selects_info_from_database, deletes_from_database, inserts_info_to_database
from core_algos.searching_algorithm import searching_algorithm_gathers_film_ids_to_display
from searching.leaderboards import gathers_top_films_from_database_on_request, creating_and_updating_top_ratings_for_leaderboards
from core_algos.calc_recommendations import RecommendedFilms

from searching.format_film_dict import turning_film_information_into_dictionary


rating_questions = json.loads("sorted_genrating_questionsres.json", "r")
sorted_genre = json.loads("sorted_genres.json", "r")
sorted_language = json.loads("sorted_language.json", "r")
user_login = json.loads("user_login.json", "r")




app = Flask(__name__)
app.permanent_session_lifetime = timedelta(hours = 4.0) # logs user out after 4 hours

@app.route("/") # blank route will be redirected to this page
@app.route("/home") # the main route to this page
def home_page():
    """
    :return: html-document: flask.render_template
    """
    return render_template("home.html", title= "Home Page")


@app.route("/search-for-film")
def search_for_specific_film():
    """
    Page where the can user search for a film

    :return: html-document: flask.render_template
    """
    try:  # to protect against the user making an error
        if "user_id" not in session.keys():
            # if the user is not logged in, then they will be redirected to the login page to login
            # and the variable "next_page" will be assigned into the session so that after they login
            # the system knows to redirect the user back to this page
            session["next_page"] = "search_for_specific_film"
            flash(["Login before entering: Search For Films", "unsuccessful"]) # to tell the user they must login first
            return redirect(url_for("login"))
        return render_template("search/films/search_for_films.html" , title= "Search For Films",
            genres = sorted_genre, languages = sorted_language, year = list(range(1965, datetime.now().year+1)))
    except:
        flash(["An error has occured, please try again.", "unsuccessful"]) # unsuccessful will determine the colour "red"
    return redirect(url_for("home_page"))



@app.route("/placeholder-2")
def gathering_film_search_query_information():
    """
    This function is called from a javascript function, once the user has clicked on the spell checked
    query, it will gather the criteria, and format it, then will set the values equal to the user's session
    so that it can be accessed in the "films_gathered" route.
    If there is no corrected query then it will instantly go to this function without the user needing to click anything,
    Here it will edit and check the user's query to make sure it does not contain unwanted characters,
    which could cause trouble looking up the query in the database, it will also check the length aswell

    :return: javascript-response: flask.jsonify - no information in it
    """
    try:
        symbols_not_wanted = ["'", '"', "%", "(", ")", "=", "`", "/", "\\", ";", ":", "*"]
        session["user_input"] = request.args.get("user_query").replace("-", " ").strip()

        if len(session["user_input"]) < 2:
            # Lots of films with likely have these 2 characters, so the lookup will take too long
            session["user_input"] = "NONE"
        else:
            for symbol in symbols_not_wanted:
                if symbol in session["user_input"]:
                    session["user_input"] = "SYMBOL"
                    break
        session["language_gathered"] = request.args.get("language").strip().split(" ")
        session["genre_gathered"] = request.args.get("genre").strip().split(" ")
        session["year_lower"] = int(request.args.get("year_lower"))
        session["year_upper"] = int(request.args.get("year_upper"))
        return jsonify()

    except:
        flash(["An error has occured, please try again.", "unsuccessful"])   
    return redirect(url_for("home_page"))


@app.route("/films-gathered-1")
def films_gathered():
    """
    Gathers all of the top 50 film ids for the query the user has entered, with the filters applied.
    for the top 10 films from the algorithm, it will fetch the information about those and display
    it on the website for the user to view.
    This page can only be accessed through the route "search_for_specific_film" by entering a valid query
    if it is invalid then the user will be redirected to the home page telling them an error has occured.

    :return: html-document: flask.render_template
    """
    try:
        if "user_input" not in session.keys():
            # the data has already been deleted so the user cannot refresh the page
            # since the data doesn't excist anymore the user must enter it again
            flash(["Please do not refresh page, enter information again.", "unsuccessful"])
            return redirect(url_for("home_page"))

        # Sets all the variables required by the function from the user's session
        user_input = session["user_input"] 
        language_gathered = session["language_gathered"]
        genre_gathered = session["genre_gathered"]
        year_lower = session["year_lower"]
        year_upper = session["year_upper"]

        # deletes all of the information from the session as they have been used and served their purpose
        del session["user_input"]
        del session["language_gathered"]
        del session["genre_gathered"]
        del session["year_lower"]
        del session["year_upper"]

        if user_input == "NONE":
            # the user did not enter a valid query
            # the query is too long or too short
            flash(["Query is either too long or too short, please try again", "unsuccessful"])   
            return redirect(url_for("home_page"))
        elif user_input == "SYMBOL":
            # contains a symbol which could effect the database
            # will prevent the query being run
            flash(["Query contains an unauthorized symbol, please try again", "unsuccessful"])   
            return redirect(url_for("home_page"))

        else:
            current_favourites = [i[0] for i in selects_info_from_database("FilmID", "Favourites", f"UserID ={session['user_id']}")]
            # These are all of the films which the user has favourited
            rated_films = [i[0] for i in selects_info_from_database("FilmID", "Ratings", f"UserID ={session['user_id']}")]
            # used to tell the user which films they have rated

            year_criteria = []
            genre_criteria = []
            language_criteria = []
            if year_lower > year_upper:
                # the lower year is greater than the upper year so swaps them
                year_criteria = [year_upper, year_lower]
            else:
                year_criteria = [year_lower, year_upper]
            if year_criteria[0] == 1965 and year_criteria[1] == datetime.now().year: # 1965 lowest yera in db
                year_criteria = [] # they want all films anyway (did not select anything specific)

            if genre_gathered[0] != "": # the user entered a specific criteria
                genre_criteria = list(map(int, genre_gathered))
            else: 
                genre_criteria = []

            if language_gathered[0] != "":
                language_criteria = list(map(int, language_gathered))
            else: 
                language_criteria = []
        
            film_ids, amount_of_films_filtered_through = searching_algorithm_gathers_film_ids_to_display(
                    user_input, year_criteria, genre_criteria, language_criteria, 0)
            # all of the film ids from the search query which the user has entered
            films, actor_dictionary, director_dictionary, genre_dictionary, language_dictionary = turning_film_information_into_dictionary(film_ids[:10], True)
            # gets information about the first 10 films, (the ones which are most likely what the user is looking for)

        return render_template("search/films/display_film_information.html", films = films, actors = actor_dictionary, directors = director_dictionary,
            genres = genre_dictionary, languages = language_dictionary, title= f"Results for {user_input}: 1",
            current_favourites = current_favourites, rated_film = rated_films, ratings = rating_questions,
            results = film_ids, amount = amount_of_films_filtered_through)
    
    except:
        flash(["An error has occured, please try again.", "unsuccessful"])   
    return redirect(url_for("home_page"))


# a form tag has been used in the html code with the POST method, the route must identify which method is used so it can get the data
@app.route("/films-gathered/<page_number>", methods = ["POST"])
def displaying_10_films(page_number: str):
    """
    Renders the template for the next 10 films for the user,
    Similar to the "films_gathered" route but the film ids have already been gathered
    so just finding the extra information about the films

    :param: page_number: str

    :return: html-document: flask.render_template
    """
    try:
        recommendation_page = False
        title, film_ids_string = request.form["next-page"].split("|||")
        # gets the title and the film ids from the html document, from a form tag "<form>"
        film_ids= json.loads(film_ids_string) # since the film ids are a string, convert them into a list

        if not page_number.isdigit():
            # makes sure that the url is a number
            flash(["Please enter a number, for the page number", "unsuccessful"])
            return redirect(url_for("home_page"))
        if int(page_number)-1 >= 0 and int(page_number)-1 > ceil(len(film_ids)/10):
            # makes sure that the url is a valid number
            flash(["Page number does not excist", "unsuccessful"])
            return redirect(url_for("home_page"))

        if "Recommendation" in title:
            # this is checked in the html document, if this is true
            # then the page will display extra information and options to the user
            recommendation_page = True
        
        current_favourites = [i[0] for i in selects_info_from_database("FilmID", "Favourites", f"UserID ={session['user_id']}")]
        rated_films = [i[0] for i in selects_info_from_database("FilmID", "Ratings", f"UserID ={session['user_id']}")]

        lower = (int(page_number)-1)*10 # the lower index of the film ids
        upper = lower +10
        films, actor_dictionary, director_dictionary, genre_dictionary, language_dictionary = turning_film_information_into_dictionary(film_ids[lower:upper], True)
        # gets the information about the 10 film ids specified

        return render_template("search/films/display_film_information.html", films = films, actors = actor_dictionary, directors = director_dictionary,
            genres = genre_dictionary, languages = language_dictionary,
            title= f"{title[:title.find(':')]}: {int(page_number)}", current_favourites = current_favourites, rated_film = rated_films,
            ratings = rating_questions, results = film_ids, recommendation_page = recommendation_page)

    except:
        flash(["An error has occured, please try again.", "unsuccessful"])   
    return redirect(url_for("home_page"))


@app.route("/films-gathered-ordered", methods = ["POST"])
def order_films_from_requested_attribute():
    """
    This route will sort the films by the attribute requested by the user, and returns the page reordered.
    The information is gathered from a html "form" tag

    :return: html-document: flask.render_template
    """
    try:
        recommendation_page = False
        data = request.form["order-films-data-button"].replace("'", '"').split("|||")
        # gets all the data about the films on the page to sort them by the desired attribute
        sort_attribute = request.form["sort-attribute"]

        # loads all of the data into lists and dictionary using json since they were requested as strings
        films= json.loads(data[0]) 
        actor_dictionary= json.loads(data[1])
        director_dictionary= json.loads(data[2])
        genre_dictionary= json.loads(data[3])
        language_dictionary= json.loads(data[4])
        title = data[5]
        film_ids= json.loads(data[6])

        if "Recommendation" in title:
            recommendation_page = True

        current_favourites = [i[0] for i in selects_info_from_database("FilmID", "Favourites", f"UserID ={session['user_id']}")]
        rated_films = [i[0] for i in selects_info_from_database("FilmID", "Ratings", f"UserID ={session['user_id']}")]
        
        is_reverse = {"↓": True, "↑": False}[sort_attribute[-1]]
        attr_sort_key = sort_attribute[:-1].lower()

        sort_attrs = {"release": "year", "runtime": "length", "budget": "budget"}
        if attr_sort_key in sort_attrs:
            attribute_to_sort_by = sort_attrs[attr_sort_key]
        else:
            attribute_to_sort_by = "revenue"

        sorted_films = sorted(films, key = lambda x: int(x[attribute_to_sort_by]), reverse = is_reverse)
        return render_template("search/films/display_film_information.html", films = sorted_films, actors = actor_dictionary, directors = director_dictionary,
            genres = genre_dictionary, languages = language_dictionary, title= title,
            current_favourites = current_favourites, rated_film = rated_films, ratings = rating_questions,
            results = film_ids, ordered_by = sort_attribute, recommendation_page = recommendation_page)
    
    except:
        flash(["An error has occured, please try again.", "unsuccessful"])   
    return redirect(url_for("home_page"))




@app.route("/placeholder-5")
def favourite_a_films():
    """
    Adds the film id to the database with the user id, in the Favourites table,
    this function is called from within a javascript functions

    :return: javascript-response: flask.jsonify - no information in it
    """
    try:
        film_id = request.args.get("film_id") 
        if not selects_info_from_database("FilmID","Favourites", f"FilmID = {film_id} AND UserID = {session['user_id']}"):
            inserts_info_to_database("(FilmID, UserID, DateAdded)", "Favourites", [(film_id, session["user_id"], datetime.now().strftime("%Y-%m-%d"))])
        return jsonify()

    except:
        flash(["An error has occured, please try again.", "unsuccessful"])   
    return redirect(url_for("home_page"))


@app.route("/placeholder-6")
def remove_a_favourited_films():
    """
    Removes the favourited film from the database for the user, in the Favourites table,
    this function is called from within a javascript functions

    :return: javascript-response: flask.jsonify - no information in it
    """
    try:
        film_id = request.args.get("film_id")
        deletes_from_database("Favourites", f"FilmID = {film_id} AND UserID = {session['user_id']}")
        return jsonify()

    except:
        flash(["An error has occured, please try again.", "unsuccessful"])   
    return redirect(url_for("home_page"))



@app.route("/favourite-films")
def favourite_films():
    """
    Displays the user's favourited films, only the first 10, they can select to see the next page if they wish,
    and they will be redirected to the "displaying_10_films" route

    :return: html-document: flask.render_template
    """
    try:
        if "user_id" not in session.keys():
            session["next_page"] = "favourite_films"
            flash(["Login before entering: Favourites", "unsuccessful"])   
            return redirect(url_for("login"))

        current_favourites = [i[0] for i in selects_info_from_database("FilmID", "Favourites", f"UserID ={session['user_id']}")]
        rated_films = [i[0] for i in selects_info_from_database("FilmID", "Ratings", f"UserID ={session['user_id']}")]
        
        if not current_favourites:
            flash(["No films in your favourite list", "unsuccessful"])
            return redirect(url_for("home_page"))
        
        films, actor_dictionary, director_dictionary, genre_dictionary, language_dictionary = turning_film_information_into_dictionary(current_favourites[:10]) 
        return render_template("search/films/display_film_information.html", films = films, actors = actor_dictionary,
            directors = director_dictionary, genres = genre_dictionary, languages = language_dictionary,
            title = "Favourites: 1", current_favourites = current_favourites, rated_film = rated_films,
            ratings = rating_questions, results = current_favourites)
    
    except:
        flash(["An error has occured, please try again.", "unsuccessful"])   
    return redirect(url_for("home_page"))



@app.route("/recommendations")
def recommendations():
    """
    Displays the recommendations for the user,
    it will order the film_ids for that, the highest priority films are nearer the front of the list,
    it will also make sure that if there are any black and white recommendations,
    then they are evenly distrubuted between each page of the recommendations.
    to go to the next page of the recommendation the route "displaying_10_films" will be called

    :return: html-document: flask.render_template
    """
    try:
        if "user_id" not in session.keys():
            session["next_page"] = "recommendations"
            flash(["Login before entering: Recommendations", "unsuccessful"])   
            return redirect(url_for("login"))

        film_ids = []
        film_ids_with_priority = {0: [], 7: [], 8: [], 9: [], 10: []}
        # these are the priorities, where 7 is for black and white films
        # 10 are the highest weighted films, followed by 9, 8, 0

        all_current_recommendations_from_database = selects_info_from_database("FilmID, Liked", "Recommendations", f"UserID={session['user_id']}")
        if len(all_current_recommendations_from_database) == 0:
            # the user has no recommendations, and need to rate and favourite more films
            films, actor_dictionary, director_dictionary, genre_dictionary, language_dictionary = [], [], [], [], []

        else:
            for film_id, liked_value in all_current_recommendations_from_database:
                # used so that the highest priority film is at the front of the list
                film_ids_with_priority[liked_value] += [film_id]

            amount_of_black_and_white_films = len(film_ids_with_priority[7])
            perc = amount_of_black_and_white_films/len(all_current_recommendations_from_database)
        
            for page_index in range(3):
                film_ids += film_ids_with_priority[7][round(perc*3*page_index): round(perc*3*(page_index+1))]
                # adds the proportion of black and white films to the film ids to display to the user, so that on each page the proportion is evenly distributed
                for priority_index in (10, 9, 8, 0):
                    if film_ids_with_priority[priority_index]: # there are film ids in that priority list
                        for _ in range(10-(len(film_ids)%10)):
                            # amount of films emaining to display on that page
                            if not len(film_ids_with_priority[priority_index]): # all of them have already been removed
                                break # go to the next priority
                            film_ids += [film_ids_with_priority[priority_index].pop()]
                            # adds it to the films to display removing it from the list

                        if len(film_ids) > 0 and len(film_ids)%10 == 0: break
                        
            films, actor_dictionary, director_dictionary, genre_dictionary, language_dictionary = turning_film_information_into_dictionary(film_ids[:10])
                # they are not in any order for their sets of 10

        current_favourites = [i[0] for i in selects_info_from_database("FilmID", "Favourites", f"UserID ={session['user_id']}")]
        rated_films = [i[0] for i in selects_info_from_database("FilmID", "Ratings", f"UserID ={session['user_id']}")]

        return render_template("search/films/display_film_information.html", films = films, actors = actor_dictionary,
            directors = director_dictionary, genres = genre_dictionary, languages = language_dictionary,
            title= "Recommendations: 1", current_favourites = current_favourites, rated_film = rated_films,
            ratings = rating_questions, results = film_ids, recommendation_page = True)
    
    except:
        flash(["An error has occured, please try again.", "unsuccessful"])   
    return redirect(url_for("home_page"))


@app.route("/placeholder-8")
def recommendation_liked_or_not_liked():
    """
    The user comments on if they like the recommendation or not,
    then adds the information to the database
    this function is called from within a javascript functions

    :return: javascript-response: flask.jsonify - no information in it
    """
    try:
        film_id = request.args.get("film_id")
        val = request.args.get("value")
        deletes_from_database("Ratings", f"FilmID = {film_id} AND UserID = {session['user_id']}")
        # if the user already has already rated or commented on this recommendtion of the film, it is removed from the database
        # so that the new rating can be added
        inserts_info_to_database("(Overall, Comedy, Actors, Quality, FilmID, UserID)", "Ratings",
            [(val,val,val,val, film_id, session["user_id"])])
        return jsonify()

    except:
        flash(["An error has occured, please try again.", "unsuccessful"])   
    return redirect(url_for("home_page"))


@app.route("/placeholder-9")
def saving_the_recommendations_to_database():
    """
    Creates new recommendations for the user by calling the class "RecommendedFilms",
    then it redirects back to the "recommendations" route to display all of the new recommendations

    :return: flask-redirect: flask.redirect
    """
    try:
        rec = RecommendedFilms(session["user_id"])
        # creates new recommendations for the user
        # the class "RecommendedFilms" is run, with all of its functions inside of it
        if rec.recommendation_created:
            flash(["Your recommendations have been created", "success"])
        else:
            flash(["Recommendation can't be created, there are not enough films rated and favourited", "unsuccessful"])
        return redirect(url_for("home_page"))
        # then redirect back to the recommendation page, so that the recommendations can be displayed to the user

    except:
        flash(["An error has occured, please try again.", "unsuccessful"])   
    return redirect(url_for("home_page"))



@app.route("/select-leaderboard")
def leaderboard():
    """
    The user can, select which leaderboard they want to see,
    once they select the leaderboard they want then they will be redirected
    to the "displaying_the_leaderboard_requestion" route, where the films will be displayed

    :return: html-document: flask.render_template
    """
    try:
        if "user_id" not in session.keys():
            session["next_page"] = "leaderboard"
            flash(["Login before entering: Leaderboards", "unsuccessful"])   
            return redirect(url_for("login"))

        return render_template("search/films/leaderboard.html" , title= "Leaderboards",
            genres = sorted_genre, languages = sorted_language, year = list(range(1965, datetime.now().year+1)))

    except:
        flash(["An error has occured, please try again.", "unsuccessful"])   
    return redirect(url_for("home_page"))


@app.route("/displaying-leaderboard", methods = ["POST"])
def displaying_the_leaderboard_requestion():
    """
    Displays the information about the leaderboard requested by the user,
    with all of the filters applied, it will gather all of the film ids,
    in order of the most relevent to the leaderboard.
    The user can access the "displaying_10_films" route,
    to see more of the films for the current leaderboard they are looking at

    :return: html-document: flask.render_template
    """
    try:
        board = request.form["leaderboard-button"]
        language_criteria = request.form.getlist("language")
        genre_criteria = request.form.getlist("genre")
        year_lower = int(request.form["year-lower"])
        year_upper = int(request.form["year-upper"])

        year_criteria = []
        if year_lower > year_upper:
            year_criteria = [year_upper, year_lower]
        else:
            year_criteria = [year_lower, year_upper]
        if year_criteria[0] == 1965 and year_criteria[1] == datetime.now().year:
            year_criteria = []

        film_ids = gathers_top_films_from_database_on_request(board, language_criteria, genre_criteria, year_criteria)
        current_favourites = [i[0] for i in selects_info_from_database("FilmID", "Favourites", f"UserID ={session['user_id']}")]
        rated_films = [i[0] for i in selects_info_from_database("FilmID", "Ratings", f"UserID ={session['user_id']}")]

        films, actor_dictionary, director_dictionary, genre_dictionary, language_dictionary = turning_film_information_into_dictionary(film_ids[:10], True)

        return render_template("search/films/display_film_information.html", films=films, actors=actor_dictionary,
            directors=director_dictionary, genres=genre_dictionary,
            languages=language_dictionary, title=f"{board}: 1", current_favourites = current_favourites, rated_film = rated_films,
            ratings=rating_questions, results=film_ids)

    except:
        flash(["An error has occured, please try again.", "unsuccessful"])   
    return redirect(url_for("home_page"))



@app.route("/films-gathered-which-have-been-in", methods = ["POST"])
def films_person_has_been_associated_with():
    """
    This gets all of the films which the actors and directors have been in or directed,
    Gathers all of the film ids and displays the first 10
    The user can access the "displaying_10_films" route,
    to see more of the films which the actor has been in or the director has directed

    :return: html-document: flask.render_template
    """
    try:
        person_id, person_type = request.form["person-id-type"].split("|||")
        # gets the actor or director id from the html document from the form tag,
        # along with if its an actor or a director as person_type

        current_favourites = [i[0] for i in selects_info_from_database("FilmID", "Favourites", f"UserID ={session['user_id']}")]
        rated_films = [i[0] for i in selects_info_from_database("FilmID", "Ratings", f"UserID ={session['user_id']}")]

        film_ids = [i[0] for i in selects_info_from_database("FilmID", f"{person_type}Integrator", f"{person_type}ID = {person_id} ORDER BY FilmID DESC")]

        films, actor_dictionary, director_dictionary, genre_dictionary, language_dictionary = turning_film_information_into_dictionary(film_ids[:10])
        # gets the information about the films they have been in.

        return render_template("search/films/display_film_information.html",  films = films, actors = actor_dictionary,
            directors = director_dictionary, genres = genre_dictionary,
            languages = language_dictionary, title = f"Films {person_type} Associated With: 1",
            current_favourites = current_favourites, rated_film = rated_films, ratings = rating_questions, results = film_ids)

    except:
        flash(["An error has occured, please try again.", "unsuccessful"])   
    return redirect(url_for("home_page"))


class LoginForm(): # this is for jinja2, from flask_wtf import FlaskForm, inherits from FlaskForm
    pass

@app.route("/login", methods=["GET", "POST"])
def login():
    """
    The html form page where the user can login to the website, 
    they will enter their information into a form from flask_wtf.FlaskForm,
    and that information once the submit button has been pressed, can be accessed in this route,
    once the submit button has been pressed the information can be processed to the database,
    and checked to see if it matches the current information if it does then the user can login to the website.
    If the user was on a page which is restricted to only users which are logged in and they get redirected
    here then once they login they will be redirected back to that page but will be logged in

    :return: html-document: flask.render_template
    """
    try:
        if "user_id" in session.keys():
            flash(["You're already logged in...", "unsuccessful"])
            # the user is already logged in
            return redirect(url_for("home_page"))

        form = LoginForm() # a class using flask_wtf.FlaskForm, as an instance to gather all of the attributes

        if form.validate_on_submit():
            validator_or_user_id = user_login(form)
            if validator_or_user_id == "password":
                flash(["Login Unsuccessful. Password wrong", "unsuccessful"])
                return redirect(url_for("login"))
            elif validator_or_user_id == "username":
                flash(["Login Unsuccessful. Username wrong", "unsuccessful"])
                return redirect(url_for("login"))
            else:
                session["user_id"] = validator_or_user_id 
                Thread(target = RecommendedFilms, args = [validator_or_user_id]).start() 
                # the recommendation class is called to generate the recommendations for the user
                # everytime they login to the website

                if "next_page" in session.keys():
                    new_route = session["next_page"]
                    del session["next_page"]
                    if new_route.find("/") == -1:
                        return redirect(url_for(new_route))
                    else:
                        # the user was on the page to the route of "search_for_person"
                        page, param = new_route.split("/")
                        return redirect(url_for(page, is_actor = param))
                else:
                    flash([f"Welcome {form.username.data}", "success"])             
                    return redirect(url_for("home_page"))

        return render_template("user_information/login.html", title = "Login", form = form)
    
    except:
        flash(["An error has occured, please try again.", "unsuccessful"])   
    return redirect(url_for("home_page"))




if __name__ == "__main__":
    app.run()
