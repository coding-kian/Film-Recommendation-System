from time import time, sleep

# imports from my project
from core_algos.formulas import selects_info_from_database, mean_and_sd, groupings, inserts_info_to_database, deletes_from_database


def gathers_top_films_from_database_on_request(chategory: str, language_criteria: list, genre_criteria: list, year_criteria: list):
    """
    When the user requests to see a leaderboard this function will be called, it will, return the top 100 film ids which relate to it
    and which have the criteria specified on it applied.
    It will be in order of priority and relevance
    There are 5 options the user can enterm Budget and Revenue, which are already stored in the database
    Profit which is the Budget Subtracted from the revenue
    Then finally top rated and funniest, which have been calculated using the user's ratings

    :param: chategory: str

    :param: langauge_criteria: list

    :param: genre_criteria: list

    :param: year_criteria: list

    :return: TYPE: list - a list of film ids if there are any
    """
    start_time = time()

    if chategory == "Profit":
        data = selects_info_from_database("FilmID", "Economy", f"Budget NOT IN (-1, 0) AND GrossRevenue <> -1 ORDER BY (GrossRevenue-Budget) DESC")
        # Orders the films by the highest profit aslong as the budget and the revenue are both known
    elif chategory in ("Comedy", "Overall"):
        chategory_number = {"Overall": 1, "Comedy": 2}[chategory]
        data = selects_info_from_database("FilmID", "TopRated", f"Chategory = '{chategory_number}' ORDER BY Priority DESC")
    else:
        data = selects_info_from_database("FilmID", "Economy", f"1 ORDER BY {chategory} DESC")
        # since there is no where statement it checks to see if 1 is equal to 1, and since it is true it ignores it

    # gathered all of the film ids now need to filter them down depending the criteria
    print(f"CONSOLE OUTPUT ONLY: Time to get film ids for leaderboard is--- {time()-start_time}. Amount is {len(data)}")

    if not data:
        # there are no films in the chategory which the user wanted
        return []

    all_film_ids = [i[0] for i in data][:100]
    # looks at the first 100 films because only want to try and filter down the most relevent films to what the uesr has requested,
    # so only looking at the top 100
    # since the database returned a list of tuples, neatening it up so it is just an integer not a tuple with 1 element

    if not language_criteria and not genre_criteria and not year_criteria:
        # no criteria havs been specified
        return all_film_ids[:50]
    
    where_statement = f"Films.FilmID IN {'('+str(all_film_ids)[1:-1]+')'}"
    # the film ids for the criteria specified must be in top 100 gathered earlier from the database
    join_statement = ""
    if language_criteria:
            where_statement += f" AND LanguageID IN {'('+str(language_criteria)[1:-1]+')'} AND LanguageToFilm.FilmID = Films.FilmID" 
            join_statement += " JOIN LanguageToFilm"
            # since the langauges are in a seperate table to all the other information about the films they have to be
            # fetched and joined from the "LanguageToFilm" table
    
    if genre_criteria:
            where_statement += f" AND GenreID IN {'('+str(genre_criteria)[1:-1]+')'} AND GenreToFilm.FilmID = Films.FilmID"
            join_statement += " JOIN GenreToFilm"

    if year_criteria:
        where_statement += f" AND ReleaseDate > {year_criteria[0]} AND ReleaseDate < {year_criteria[1]+1}"
        # lowerbound and upperbound of the release date which they user has requested the film to be between
    
    start_time = time()
    film_ids_wanted_to_display = [j[0] for j in selects_info_from_database("Films.FilmID", "Films"+join_statement, where_statement)]
    # instead of being a list of tupels with 1 element it is now a list of integers 

    ordered_film_ids = [k for k in all_film_ids if k in film_ids_wanted_to_display]
    # puts the film_ids orders of what they were gathered in from the database

    print(f"CONSOLE OUTPUT ONLY: Time to filter film ids for leaderboard is--- {time()-start_time}. Amount is {len(ordered_film_ids)}")

    return ordered_film_ids[:50]


def updates_database_with_top_rated_films(chategory: str):
    """
    The function is called when the website is loaded up, and is run periodically, updating the top rated and funniest films in the database,
    so that when the user requests to see the leaderboard for them it is the most up to date it can be without causing performance issues

    The chategory of "Overall" which is the top ratings has the value of 1
    and the chategory of "Comedy" has the value of 2

    :param: chategory: str
    """

    FIELD = "(FilmID, AverageRating, Chategory, Priority)"
    TABLE = "TopRated"
    chategory_number = {"Overall": 1, "Comedy": 2}[chategory]

    deletes_from_database(TABLE, f"Chategory = '{chategory_number}'")
    # deletes all of the current top rated or funniest films from the database, so new ones can be added without duplication

    gathered_films = selects_info_from_database(f"FilmID, {chategory}", "Ratings", f"{chategory} <> -1")
    # all of the film ids and ratings in the specified chategory which the user has rated where the rating is not unknown
    if not gathered_films:
        # there are none rated in this chategory so, the function does not need to run any longer
        return

    rating_values = [i[1] for i in gathered_films] # all of the ratings without the film ids
    grouped_films_with_ratings = groupings(gathered_films)
    mean, sd = mean_and_sd(rating_values) # the mean rating of this chategory and standard deviation

    above_2sd = []
    above_1sd = []
    above_mean = []

    for film_id, rating in grouped_films_with_ratings.items():
        mean_rating_for_film = sum(rating)/len(rating)
        if mean_rating_for_film >= mean + 2*sd:
            above_2sd += [[film_id, mean_rating_for_film]]
        elif mean_rating_for_film >= mean + sd:
            above_1sd += [[film_id, mean_rating_for_film]]
        elif mean_rating_for_film >= mean:
            above_mean += [[film_id, mean_rating_for_film]]
        # else it does not matter, and is not important to the algorithm
    
    count = 0 # limits it so that there is not more than 100 films in the database for that chategory
    if above_2sd:   
        extra_info_2sd = list(map(lambda x: tuple(x+[chategory_number, 2]), above_2sd))
        inserts_info_to_database(FIELD, TABLE, extra_info_2sd) # needs to be a list of tuples when added to the database
        count += len(above_2sd)
    
    if above_1sd and count <= 100:
        extra_info_1sd = list(map(lambda x: tuple(x+[chategory_number, 1]), above_1sd))
        inserts_info_to_database(FIELD, TABLE, extra_info_1sd)
        count += len(above_1sd)

    if above_mean and count <= 100:
        extra_info_above = list(map(lambda x: tuple(x+[chategory_number, 0]), above_mean))
        inserts_info_to_database(FIELD, TABLE, extra_info_above)


def creating_and_updating_top_ratings_for_leaderboards():
    """
    Runs when the webiste loads up, then every 30 minuets after that until it shuts down
    this function will be in a thread so it will be running in the background
    """
    while True:
        updates_database_with_top_rated_films("Overall")
        sleep(5) # incase the database is already too busy
        updates_database_with_top_rated_films("Comedy")
        sleep(60*30) # 30 minutes since 60 seconds in a minute then multipled by 30


if __name__ == "__main__":
    pass