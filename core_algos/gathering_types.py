from collections import Counter # sums up all the elements with the occurence

# imports from my project
from core_algos.formulas import selects_info_from_database, mean_and_sd, combination_formula, binomial_distribution, groupings 



def language(films: list):
    """
    Gathers all the users favourited and rated films, and determines which language they are most likely going to want the films to be in
    
    :param: films: list - all the films which the user has favourited
    
    :return: TYPE: list - the language ids which the user may like
    """
    FIELD = "LanguageID"
    TABLE = "LanguageToFilm"
    UNKNOWN_ID = 75 # the id of a language if the language is unknown
    all_language_ids = selects_info_from_database(f"FilmID, {FIELD}", TABLE, f"FilmID IN {tuple(films)}") # gets the ids of the languages of the users films   

    language_ids_without_unknowns =  selects_info_from_database(f"FilmID, {FIELD}", TABLE, f"FilmID IN {tuple(films)} AND {FIELD} <> {UNKNOWN_ID}")
    # can select all the ones from the database which do not have an unknown language, allowing me to ignore the films with an unknown language

    if not len(language_ids_without_unknowns): # All languages are unknown
        return [] # There are no languages to be found, so returns an empty list
        
    amount_of_unknowns = len(all_language_ids) - len(language_ids_without_unknowns)
    languages_without_ids = [i[1] for i in language_ids_without_unknowns] # all of the language IDs without the film ID (ignores the unknown ones)
    films_with_language = tuple(dict(Counter(languages_without_ids)).items())
    #  How many films have that language (occurence), automatically in descending order, converted into a dict then tuple as the function Counter does not apple instant tuple conversion

    if films_with_language[0][1] == len(films) - amount_of_unknowns: # does the occurence of that language equal the length of all the films (ignoring unknowns)
        return [films_with_language[0][0]] # returns the id of that language
    else:
        grouped_languages = groupings(language_ids_without_unknowns)
        films_with_1language = {film_id2: languages_ids[0] for film_id2, languages_ids in grouped_languages.items() if len(languages_ids) == 1}
        # used to get all the films with only 1 language

        amount_of_singles = dict(Counter(list(films_with_1language.values()))) # {languageID: value} where value is the amount of films with 1 language that language has been in 

        amount_of_films_with_1language = len(films_with_1language)
        percentage_occurence = [(language_id3, amount/amount_of_films_with_1language) for language_id3, amount in amount_of_singles.items()]
        # finds the percentage of films which this language is in, never will be 100% since the condition above for that language being in all films

        percentages_only = sorted(set([percentage for language_id4, percentage in percentage_occurence]), reverse = True)
        # this is needed to see if more than 1 language has the same percentage occurence.
        # This is just the percentages of the films as a set (only want 1 of each percentage) to find the first, second and third most common languages, sorted in Descending order
        # the length of the percentages_only will be atleast 2 long automatically

        language_ids_to_get_most_common = [] # all of the language ids have the highest percentage occurence
        language_ids_to_get_second = [] 
        for language_id4, percentage2 in percentage_occurence:
            if percentage2 == percentages_only[0]: # for most common language
                language_ids_to_get_most_common += [language_id4]
            elif percentage2 == percentages_only[1]: # for second most common language
                language_ids_to_get_second += [language_id4]

        if len(language_ids_to_get_most_common) > 1:
            return language_ids_to_get_most_common

        elif len(percentages_only) > 1: # has more than 1 language with that percentage or second most common language above 25%
            if percentages_only[1] > 0.25:
                return language_ids_to_get_most_common + language_ids_to_get_second # the most common language, and all the languages with the second highest occurence

        return language_ids_to_get_most_common # not significant evidence to suggest that the user would like a different language


def colour(films: list):
    """ 
    Gathers all the users favourited and rated films, and determines which colour type the user is most likely going to want the film to be in
    
    :param: films: list - all the films which the user has favourited
    
    :return: TYPE: float - the ID of the type of colour, or the percentage of films which should be monochrome
    """
    FIELD = "Colour"
    TABLE = "Films"
    UNKNOWN_ID = -1 # if the films colour is unkown 
    MONO_ID = 1 # if the film is in monochrome
    COLOUR_ID = 2 # if the film is in full colour

    # THESE VALUES WILL NEED TO CHANGE IF THE PROJECT IS UPDATED TO ALLOW THE USER TO ADD THEIR OWN FILMS OR IF IT AUTOMATICALLY ADDS NEW FILMS
    COL = 221937  
    MONO = 16319 # Amount of films which are monochrome
    UNKNOWN = 21700
    TOTAL = COL + MONO + UNKNOWN

    all_colours = selects_info_from_database(f"FilmID, {FIELD}", TABLE, f"FilmID IN {tuple(films)}") 
    colour_ids_only = list(dict(all_colours).values()) # used to find how many of the users favourited films are a certain colour
    # since the user will only have 1 colour this method of using the dictionary is fine as there will never be more than 1 element with the same key (film id)
    amount_of_mono = colour_ids_only.count(MONO_ID) # the amount of films which are in mono
    amount_of_colour = colour_ids_only.count(COLOUR_ID)
    amount_of_unknown = colour_ids_only.count(UNKNOWN_ID)
    amount_of_films = len(films)
    amount_without_unknowns = amount_of_films- amount_of_unknown

    if amount_of_films == amount_of_unknown: # is the colour of all films unknown
        return UNKNOWN_ID # will return as an integer but will be used as a float; therefor return type is a float
    elif amount_of_films == amount_of_mono-amount_of_unknown: # this is so that it ignores the unknown films
        return MONO_ID
    elif amount_of_films == amount_of_colour-amount_of_unknown:
        return COLOUR_ID
    else:
        PROBABILITY_OF_MONO = MONO/(TOTAL-UNKNOWN) # float
        # amount of films for the trials should not include the unknowns
        probability = binomial_distribution(amount_of_mono, amount_without_unknowns, amount_without_unknowns, PROBABILITY_OF_MONO) # float
        # returns a probability, which will be tested at the 20% significance level, to see if it is likely to be correct
        if probability < 0.2: # 20%
            # this lower probability falls within the alternative hypothesis, meaning that it is likely the user prefers monochrome films
            # so will try and represent the amount of films which have mono in them
            return amount_of_mono/amount_without_unknowns
        else:
            # the probability fell within the null hypothesis therefor will only accept films in full colour
            return COLOUR_ID


def runtime(films: list):
    """ 
    Gathers all the users favourited and rated films, and determines the length of the film the user is most likely going to prefer
    
    :param: films: list - all the films which the user has favourited
    
    :return: lower bound: int
    
    :return: upper bound: int
    """
    FIELD = "Length"
    TABLE = "Films"
    UNKNOWN_ID = -1 # the value of the runtime if it is unknown
    all_runtimes = selects_info_from_database(FIELD, TABLE, f"FilmID IN {tuple(films)}")  # gets the runtimes from the database for the users films
    runtimes_as_list = [i[0] for i in all_runtimes]
    amount_of_unknown = runtimes_as_list.count(UNKNOWN_ID)

    if amount_of_unknown == len(films):
        return [0, 0] # all of the films have an unknown runtime

    mean, sd = mean_and_sd(runtimes_as_list) # sd: standard deviation
    lower = mean - 2*sd
    upper = mean + 2*sd
    return round(lower), round(upper) # so that it returns an integer to the nearest whole number


def release_date(films: list):
    """ 
    Gathers all the users favourited and rated films, and determines which range of years the user is most likely going to want a film from
    
    :param: films: list - all the films which the user has favourited
    
    :return: lower bound: int
    
    :return: upper bound: int
    """
    FIELD = "ReleaseDate"
    TABLE = "Films"
    all_dates = selects_info_from_database(FIELD, TABLE, f"FilmID IN {tuple(films)}")  # gets the ids of the languages of the users films   
    release_years_as_list = [int(date[0][:4] )for date in all_dates]
    # date[0][:4], so that it is only working with the year, and all values in the table are ready integer, so converting back

    mean, sd = mean_and_sd(release_years_as_list) # sd: standard deviation
    lower = mean - 2*sd
    upper = mean + 2*sd

    return round(lower), round(upper)   


def statistics_for_actors_directors_genres(films: list, field: str, table: str, rating_chategory: str, UNKNOWN_ID: int = 888888888888):
    """
    The directors, actors and genres algorithm are very similar, so can use the same function for a large part of it.
    Quality rating is for the directors, Actors rating is for the actors and Overall rating is for the genres.
    The quality is determined by how well the film is produced and that is based on the director.
    Takes in all the users favourited films, and information for the sql query as paramaters. Then returns data which can be used in either the actors, directors or genre
    function to determine which actors, directors or genres the user is likely going to want.
    
    :param: films: list - all the films which the user has favourited
    
    :param: field: str
    
    :param: table: str
    
    :param: rating_chategory: str
    
    :param: UNKNOWN_ID: int - if not specified then unknown id for actor or director as they are the same. When specified it will be the unknown id for genre
    
    :return: mean_rating: float
    
    :return: sd_of_rating: float
    
    :return: mean_occurence: float
    
    :return: sd_of_occurence: float
    
    :return: one_of_each_rating: list
    
    :return: average_ratings: dict
    
    :return: director_actor_occurence: dict
    
    :return: without_unknowns: list
    """
    all_ids = selects_info_from_database(f"FilmID, {field}", table, f"FilmID IN {tuple(films)}")   # gets all the ids from the database
    just_ids = [i[1] for i in all_ids]
    # if this was made into a dictionary instead and used the .values method. it would remove some the film,
    # as the keys can't have the same value, as films may have multiple actors or directors or genres
    amount_of_unknown = just_ids.count(UNKNOWN_ID)

    if amount_of_unknown == len(films):
        return [[] for i in range(8)]
        # if all actors, directors or genres are unknown, needs to return an empty list which is the same length as the one returned by the main function so that it does not crash

    without_unknowns =  selects_info_from_database(f"FilmID, {field}", table, f"FilmID IN {tuple(films)} AND {field} <> {UNKNOWN_ID}")
    # so that it can ignore the unknown actors, directors or genres
    ratings = selects_info_from_database(f"FilmID, {rating_chategory}", "Ratings", f"FilmID IN {tuple(films)}")

    just_director_actor_genre_ids = [i[1] for i in without_unknowns]
    films_with_ratings = []
    rating_frequency = [] # all of the ratings from each film, multiplied by each element of that film; where the elements are a list of the ids of the actors, directors or genres
    for film_id, rating in ratings:
        # This may not run depending on if the user has given the films a quality, actor or overall ratings
        films_with_ratings +=[film_id]
        if rating == -1:
            rating = 5 # if the user hasn't given the film a quality, actor or overall rating

        for film_id2, actors_directors_genres_id in without_unknowns:
                if film_id == film_id2:
                    rating_frequency += [actors_directors_genres_id]*rating
        # if the film ids are the same then multiply the director, actor, genre by its quality, actor or overall rating respectively

    if len(ratings) == (len(films) - amount_of_unknown): # all films have a quality, actor or overall rating
        pass
    else:
        for film_id3, actors_directors_genres_id2 in without_unknowns:
            # Does the same loop as above, needs to be done at a different time as not all values are in films_with_ratings yet
            if film_id3 not in films_with_ratings: # that film has no quality, actor or overall rating
                rating_frequency += [actors_directors_genres_id2]*5
                # the user has not given the film any ratings at all in any chategory

    tallied_ratings = dict(Counter(rating_frequency)) # each actors, directors or genres multiplied by its rating of the film, then summed together
    actors_directors_genres_occurence = dict(Counter(just_director_actor_genre_ids)) # The amount of films which that actors, directors or genres has been in, in the form (id, occurence)
    average_ratings = {actors_directors_genres_id3: total_rating/actors_directors_genres_occurence[actors_directors_genres_id3]
        for actors_directors_genres_id3, total_rating in tallied_ratings.items()}
    # creates a dictionary, with the key being the quality, actor or overall id and the value being the mean rating of the quality, actor or overall rating
    
    rating_frequency2 = list(average_ratings.values())
    only_occurences = list(actors_directors_genres_occurence.values()) # occurence is a value, of how many films they have been in
    one_of_each_rating  = sorted(list(set(rating_frequency2)), reverse = True)
    # this is so that the algorithm can select all the quality, actor or overall with the top *{invert a number}* highest mean rating. 
    # In descending order so that the highesting rating is as index [0]

    mean_rating, sd_of_rating = mean_and_sd(rating_frequency2)
    mean_occurence, sd_of_occurence = mean_and_sd(only_occurences)

    return mean_rating, sd_of_rating, mean_occurence, sd_of_occurence, one_of_each_rating, average_ratings, actors_directors_genres_occurence, without_unknowns


def directors(films: list):
    """
    Gathers all the users rated and favourited and rated films, and determines which directors they are likely going to want,
    and the ones which they are likely not to want, calling the "statistics_for_actors_directors_genres" function
    
    :param: films: list - all the films which the user has favourited
    
    :return: TYPE: list - 2d list, containing 2 elements; the first list are the ids of the directors which films are
    wanted for and the second list are the ids of the directors which are not wanted
    """
    mean_rating, sd_of_rating, mean_occurence, sd_of_occurence, one_of_each_rating, average_ratings, director_occurence, _ = statistics_for_actors_directors_genres(
        films,"DirectorID", "DirectorIntegrator", "Quality") # only indented and on a seperate line because it extended to far

    # gets all the information which is needed to calculate
    if not mean_rating:
        return [[],[]] # no films with known directors

    directors_likely_wanted = [] # director ids which are above 1 sd of mean occurence and not below 1 sd of mean rating
    directors_not_allowed = [] # this will be a list of director ids which are below 1 sd of the mean rating and above 1 sd of mean occurence
    for director_id4, occurence in director_occurence.items():
        if occurence >= (mean_occurence + sd_of_occurence):
            if average_ratings[director_id4] <= mean_rating - sd_of_rating:
                directors_not_allowed += [director_id4]
            else:
                # these are the directors which are above 1 sd of mean occurence and not below 1 sd of mean rating
                if len(one_of_each_rating) >= 3: # making sure that there are atleast 3 different ratings
                    if average_ratings[director_id4] >= one_of_each_rating[2]: # directors which have the top 3 highest ratings
                        directors_likely_wanted += [director_id4]
                else: # there is not enough ratings for the top 3
                    print
                    directors_likely_wanted += [director_id4]

    if not (len(directors_likely_wanted) + len(directors_not_allowed)):
        return [[],[]] # no directors with significant impact
    else:
        return [directors_likely_wanted, directors_not_allowed]


def actors(films: list):

    """ 
    Gathers all the users rated and favourited and rated films, and determines which actors they are likely going to want,
    and the ones which they are likely not to want, calling the "statistics_for_actors_directors_genres" function
    It calculates the most popular actors, aswell as the actors which should not be in the recommended films.
    
    :param: films: list - all the films which the user has favourited
    
    :return: TYPE: list - 2d list, containing 2 elements. 1st - Singular actors to gather. 2nd - Actors which should not be in the films gathered.
    """
    mean_rating, sd_of_rating, mean_occurence, sd_of_occurence, _, average_ratings, actor_occurence, _ = statistics_for_actors_directors_genres(
            films, "ActorID", "ActorIntegrator", "Actors")
    if not mean_rating: # if all of the actors in the films are unknown
        return [[],[]]

    actors_wanted_1sd = []
    actors_wanted_2sd = []
    actors_not_wanted = []
    for actor_id3, occurence in actor_occurence.items(): # where occurence is an integer of the amount of films that actor has been in
        if occurence >= mean_occurence + sd_of_occurence:
            if average_ratings[actor_id3] <= mean_rating - sd_of_rating:
                # if the amount of films which the actor is in is less than 1 sd below the mean rating then I will not want films with that actor
                actors_not_wanted +=[actor_id3]
            else:
                actors_wanted_1sd += [actor_id3]

        elif occurence >= mean_occurence + 2*sd_of_occurence: # similar to the one above but for 2 sd
            if average_ratings[actor_id3] <= mean_rating - sd_of_rating:
                actors_not_wanted +=[actor_id3]
            else:
                actors_wanted_2sd += [actor_id3]

    actors_to_return = actors_wanted_1sd[:4]+actors_wanted_2sd[:8]
    # Will join together the lists for actors which are wanted for both sd, at most 4 actors for 1sd and at most 8 actors for 2sd
    # the loop continues because it will need to find all of the actors which are not wanted still.
    return [actors_to_return, actors_not_wanted]


def genres(films: list):
    """ 
    Gathers all the users rated and favourited films and determines which genres they are likely going to want,
    and the ones which they are likely not to want, calling the "statistics_for_actors_directors_genres" function
    It calculates the most common combinations of genres in films which have the highest rating. Aswell as the most popular genres,
    if there are not more than 3 combinations, aswell as returning the genres which should not be in the recommended films
    Combinations and singular genres have weightings, where if a film has that combination of genres or singular genre it will be added to a different weighting class,
    Where 3 is the highest weighting which will be favoured, followed by 2 then 1. If the weighting is 0 then that genre or combination is not wanted
    
    :param: films: list - all the films which the user has favourited
    
    :return: TYPE: list - 2d list, containing 2 elements. 1st - Combinations of genres to gather, 2nd - List of genres to gather, with the weighing order to present in the recommended films.
    """
    mean_rating, sd_of_rating, mean_occurence, sd_of_occurence, _, average_ratings, genre_occurence, without_unknown_genres = statistics_for_actors_directors_genres(
        films, "GenreID", "GenreToFilm", "Overall", UNKNOWN_ID= 1) # where 1 is the id of the unknown id of a genre

    if not mean_rating: # if all of the genres in the films are unknown
        return [[],[]]
    
    grouped_data = groupings(without_unknown_genres)
    itemised_grouped_data = list(grouped_data.items())
    combinations = [] # all of the different combinations of genres
    for index, film_data in enumerate(itemised_grouped_data): # film_data: is a tuple of the film id and all of the genres for that film
        for _, all_genres in itemised_grouped_data[index+1:]:  # _ is the film_id but is not used
            # allows the program to run faster as it is not looking looking at all of the items in the list again, as that comparison has already been made, or will be made in the future
            # when "index+1" > len(itemised_grouped_data) then itemised_grouped_data[index+1:] will be an empty list and will not crash the program
            in_common = set(film_data[1]) & set(all_genres) # looks to see if there are any common elements in the lists
            if len(in_common) > 1: # if there is more than 1 genre which is in common
                combinations += [tuple(sorted(in_common))]
                # so that if there are combos which are the same but are in a different order, the sorted function allows them to be matched
                # some functions only work with a list of tuples, as it requires immutability, since lists are unhashable, i have to convert all the combos to tuples.

    combos_wanted = [] # will look like [[[genre_id1, genre_id2], 0], [[genre_id2, genre_id3], .83]]
    # a 2d list, with each element being identifying with a number which is used to indicate the percentage proportion of
    # how many of that combo should be in the films which are being recommended
    # if "0" then do not allow films with that combo. else it will be a float value, on the percentage of films which should have this combo
    if combinations: # there are any combinations, does more than 1 film have 2 or more actors in common
        amount_of_each_combination = Counter(combinations)
        ordered_combinations = amount_of_each_combination.most_common() # orders the combinations from the most occuring combination to the least
        top_combo = ordered_combinations[0] # the combo with the highest occurence
        top_possible_combo_amount = combination_formula(len(films),2) # this will be the top possible amount of combinations, the position is 2 since each comparison is between 2 lists
        if top_combo[0] == top_possible_combo_amount:
            return [(top_combo[0],3),[]]

        for list_of_genres, occurence in ordered_combinations:
            #  goes through all of the combinations from the most occuring to the least occuring one, where occurence is the amount of times that combo has appeared
            if occurence <= top_possible_combo_amount*.1:
                # will continue to the next combination in the list (loop) if the occurence of this combination is less than 10% of the possible amount of combinations of genres it could have
                continue

            total_ratings = 0
            for genre_id in list_of_genres:
                total_ratings += average_ratings[genre_id] # adds together all of the average ratings of each genre

            combo_mean_rating = total_ratings/len(list_of_genres)
            if combo_mean_rating <= mean_rating - sd_of_rating: # below 1 sd of mean rating
                combos_wanted += [(list_of_genres, 0)] # do not want this combination in the recommended films so returning a 0

            elif combo_mean_rating >= mean_rating + sd_of_rating: # above 1 sd of mean rating
                combos_wanted += [(list_of_genres, 3)] # since it is above average I will give it a higher weighting

            else: # between 1 sd of mean rating
                combos_wanted += [(list_of_genres, 2)] # this will be for the majority of the values (68%) so will give a medium weighting

    if len(combos_wanted) >= 3: # If there is already a significant amount of comboinations of genres to work with then will stop the algorithm, this includes combinations which are not wanted
        return [combos_wanted,[]]

    genres_wanted = [] # will look like [[genre_id1, 0], [genre_id2, .32], [genre_id3, .83]]
    # where the value in the list with the genre id is the percentage to represent; if 0 then do not want this genre in the recommended films
    above_1sd_mean_occurence = mean_occurence + (sd_of_occurence/2)
    below_1sd_mean_occurence =  mean_occurence - (sd_of_occurence/2)

    for genre_id2, occurence2 in genre_occurence.items(): # where occurence is the amount of films which this genre is in
        if occurence2 >= above_1sd_mean_occurence and average_ratings[genre_id2] >= mean_rating - sd_of_rating:
            # above 0.5 sd of the mean occurence and above 1 sd of the mean rating, or between 1 sd of the mean rating. which the operation "above mean - 1sd" respesents
            genres_wanted += [(genre_id2, 2)]
            # since the user has alot of these films with this genre, I will give a greater weighting to this genre. Of 2, since the "3" weighting is only the most common/rated combinations

        elif occurence2 <= below_1sd_mean_occurence and average_ratings[genre_id2] >= mean_rating - sd_of_rating:
            # below 0.5 sd of the mean occurence and above or between 1 sd of the mean rating
            genres_wanted += [(genre_id2, 1)]

        elif below_1sd_mean_occurence <= occurence2 <= above_1sd_mean_occurence and average_ratings[genre_id2] >= mean_rating - sd_of_rating:
            # between .5 sd of the mean occurence and above or between 1 sd of the mean rating
            # these genres will not significant effect the users recommendation, so nothing special is going to be done with them, and will just be ignored
            pass

        elif occurence2 >= below_1sd_mean_occurence and average_ratings[genre_id2] <= mean_rating - sd_of_rating:
            if occurence2 >= mean_occurence + sd_of_occurence:
                # Occurence of genre above 1 sd of mean occurence and rating below 1 sd of mean rating
                # Do not want this genre in the recommended, the user does not like it probably
                genres_wanted += [(genre_id2, 0)]

        
        else:
            # below 0.5 sd of mean occurence and below 1 sd of mean rating
            # Do not want this genre in the recommended, the user does not like it probably
            genres_wanted += [(genre_id2, 0)]

    return [combos_wanted,genres_wanted]


if __name__ == "__main__":
    pass