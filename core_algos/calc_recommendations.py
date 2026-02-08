from random import choices

# imports from my project
from core_algos.formulas import inserts_info_to_database, selects_info_from_database, deletes_from_database
from core_algos.gathering_types import groupings, language, colour, runtime, release_date, directors, actors, genres
from searching.format_film_dict import FilmAttributesForRecommendation


class RecommendedFilms:
    """
    Gathers all of the users favourited and rated films from the database
    Checks to see if the user has enough films to make a good recommendation (atleast 5)
    If they do then it will gather all films which the wanted actors and directors have been in if there are atleast 20 films from these 2, then it will
    Filter down (a random set of 100 films from the actors and directors)
    all of the films from the actors and directors in the following chategories runtime, release date, language, colour of the film and the genres.
    If there are more than 10 filtered recommendations then they are added to the database.
    
    :param: user_id: int
    """
    def __init__(self, user_id: int):
        """
        Calls all the functions, and creates the attributes
        """
        self.recommendation_created = False # Sees if a recommendation is created or not and if there is enough information to make a good recommendation
        self.user_id = user_id
        self.__favourited_rated_films = []
        self.__film_attributes = []
        self.__film_ids_gathered_to_recommend = []
        self.__film_ids_from_directors = []
        self.__film_ids_from_actors = []
        self.__not_wanted = [] # from filtering down the films the ids of the films which are not wanted
        self.__mono = [] # the ids of the films which are in monochrome

        # for GENRES in "__filtering_film_ids_down" function
        self.__first_weighting = [] # films with combinations which are the most wanted
        self.__second_weighting = [] # films with combinations and singular genres which are wanted and most wanted respectively, aswell as films which share a director and actor
        self.__third_weighting = []
        # if the film id appears in more than one of these lists, then the priority order from the one which have the highest importance is
        # __first_weighting, __not_wanted, __mono, __second_weighting, __third_weighting, __favourited_rated_films

        # data to insert for each weighting
        self.__data_to_insert_for_first = []
        self.__data_to_insert_for_second = []
        self.__data_to_insert_for_third = []
        self.__data_to_insert_for_mono = []
        
        self.__gathering_films_from_database() # is run to get all of the favourited and rated films
        if len(self.__favourited_rated_films) >= 5: # the has a good amount of films rated or favourited to find a good recommendation
            self.recommendation_created = self.__gathering_and_filtering_film_ids()
        else:
            self.recommendation_created = False


    def __gathering_films_from_database(self):
        """
        Gathers all of the film ids from the database what are going to be used to create a good set recommendations
        """
        FIELD = "FilmID"
        where = f"UserID = {self.user_id}"
        favourited = selects_info_from_database(FIELD, "Favourites", where)
        rated = selects_info_from_database(FIELD, "Ratings", where)
        self.__favourited_rated_films = list({i[0] for i in favourited+rated}) # removes duplicates if the film is rated and also favourited


    def __gathering_and_filtering_film_ids(self):
        """
        Gathers all of the films which the actors wanted and directors wanted have acted in and directed.
        Checks to make sure that there are enough film ids to generate a decent recommendation, if there is not will return False, so that the user knows to favourite or rate more films
        If there are enough films, then it will use all of the film ids from the actors and the directors to create a recommendation, by first;
        gathering all attributes for each film and creating this as a list of objects. Comparing each value of each film and filtering it down. 
        Putting higher influenced films in a different chategory so that they are favoured when adding the 30 films to the database
        Once all of this has been done the information is gathered together and is added to the database.
		
		:return: True or False: bool - depends on if a recommendation is created or not
        """
        self.__film_ids_from_director_function()
        self.__film_ids_from_actor_function()

        ids_gathered  = list(set(self.__film_ids_from_directors + self.__film_ids_from_actors)) # removes duplicate films if they are in both lists
        if len(ids_gathered) >= 20: # making sure there are enough films to try and filter down
            self.__film_ids_gathered_to_recommend = ids_gathered[:100]
            # If looking at too many films in depth then the algorithm will be slow, so only allowing 100 films to try and filter down
            # The list is not in order so taking the index of the first 100 items, will mean it is not biased towards any film.
            where = f"FilmID IN {'('+str(self.__film_ids_gathered_to_recommend)[1:-1]+')'}"
            data_for_length_colour_release_date = selects_info_from_database("FilmID, Length, Colour, ReleaseDate", "Films", where)
            data_for_language = selects_info_from_database("FilmID, LanguageID", "LanguageToFilm", where) # with this it will have multiple elements for that film id, since different languages
            data_for_genres = selects_info_from_database("FilmID, GenreID", "GenreToFilm", where)
            grouped_languages = groupings(data_for_language)
            grouped_genres = groupings(data_for_genres)
            self.__film_attributes = [FilmAttributesForRecommendation(
                film_id, runtime_val, colour_val, release_date_val, grouped_languages[film_id], grouped_genres[film_id])
                for film_id, runtime_val, colour_val, release_date_val in data_for_length_colour_release_date] # creates a list of objects

            self.__second_weighting += list(set(self.__film_ids_from_directors) & set(self.__film_ids_from_actors))
            # if the films which the directors has directored is shared with the films which actors have been in then will make a list of these,
            # and then they will more likely be favoured by putting them in the second weighting list

            self.__filtering_film_ids_down()
            
            # removes all duplicates is there are any
            self.__first_weighting_set = list(set(self.__first_weighting))
            self.__second_weighting_set = list(set(self.__second_weighting))
            self.__third_weighting_set = list(set(self.__third_weighting))
            self.__not_wanted_set = list(set(self.__not_wanted))
            all_films = self.__first_weighting + self.__not_wanted + self.__mono + self.__second_weighting_set + self.__third_weighting + self.__film_ids_gathered_to_recommend 
            have_too_many_films_been_removed = len(self.__film_ids_gathered_to_recommend) - len(self.__not_wanted)
            if have_too_many_films_been_removed >= 10: # at least 10 films left after the filtering process
                if len(all_films) == len(set(all_films)):
                    # This means that there are no films with a higher weighting and any films which are not wanted, and that only the films in self.__film_ids_gathered_to_recommend  are wanted
                    # Just going to add all of the films to the data base for the "__favourited_rated_films" list  
                    self.__adding_recommendations_to_db(True)
                    # when calling the function is_singular is true

                else: # Where val is the FilmID
                    mono_data_to_add = []
                    for val in self.__first_weighting_set:
                        if val in self.__not_wanted_set:
                            self.__not_wanted_set.remove(val)
                        if val in self.__mono:
                            self.__mono.remove(val)
                        if val in self.__second_weighting_set:
                            self.__second_weighting_set.remove(val)
                        if val in self.__third_weighting_set:
                            self.__third_weighting_set.remove(val)
                        self.__film_ids_gathered_to_recommend.remove(val)
                        self.__data_to_insert_for_first +=[(val ,self.user_id , 10)]

                    for val2 in self.__not_wanted_set:
                        if val2 in self.__mono:
                            self.__mono.remove(val2)
                        if val2 in self.__second_weighting_set:
                            self.__second_weighting_set.remove(val2)
                        if val2 in self.__third_weighting_set:
                            self.__third_weighting_set.remove(val2)
                        self.__film_ids_gathered_to_recommend.remove(val2)
                    
                    for val3 in self.__mono[1:]: # Is not looking at the proporition to represent
                        if val3 in self.__second_weighting_set:
                            self.__second_weighting_set.remove(val3)
                        if val3 in self.__third_weighting_set:
                            self.__third_weighting_set.remove(val3)
                        self.__film_ids_gathered_to_recommend.remove(val3)
                        mono_data_to_add +=[(val3, self.user_id, 7)]

                    for val4 in self.__second_weighting_set:
                        if val4 in self.__third_weighting_set:
                            self.__third_weighting_set.remove(val4)
                        self.__film_ids_gathered_to_recommend.remove(val4)
                        self.__data_to_insert_for_second +=[(val4 ,self.user_id , 9)]
                    
                    for val5 in self.__third_weighting_set:
                        self.__film_ids_gathered_to_recommend.remove(val5)
                        self.__data_to_insert_for_third +=[(val5 ,self.user_id , 8)]

                    if mono_data_to_add: # there is information to add to the database
                        self.__data_to_insert_for_mono = mono_data_to_add[:round(self.__mono[0]*30)]
                        # this is used to represent the proportion, multiplied by 30 since the recommendation will have 30 films

                    # compare each list to each other, therefor 10 combinations to check, since 5 lists and groupings are in 2
                    # in order of priority, removing the film ids from other lists if they are in a higher weighted list
                    # __first_weighting_set, __not_wanted_set, __mono, __second_weighting_set, __third_weighting_set, __favourited_rated_films {PRIORITY ORDER}
                    self.__adding_recommendations_to_db(False)
            else:
                return False # Not enough information to create a good recommendation
        else:
            return False
        return True # Recommendation created


    def __adding_recommendations_to_db(self, is_singular: bool):
        """
        Adds the top 30 highest weighted films, is done randomly in the sense that the lists are not in any particular order, and is just selecting the first 30 from the lists
        If none of the films have a speicifc weighting then will just add the first 30 of the "self.__film_ids_gathered_to_recommend" list to the database
        This is the order of priority --- self.__first_weighting, self.__mono, self.__second_weighting, self.__third_weighting
        for self.__mono, it will be added to the database, but when the user is viewing the films it will try and only select a third in each segment of 10 (using integer division).
        
        :param: is_singular: bool
        """
        TABLE = "Recommendations"
        FIELDS = "(FilmID, UserID, Liked)"
        deletes_from_database(TABLE, f"UserID = {self.user_id}")
        # deletes the old recommendations, so that there are not duplicates when the new ones are added if the same film is recommended twice ones to add new ones

        if not is_singular:
            amount_added_so_far = 0 # the amount of films which have been added to the database from far from the recommended ones
            # need to make sure that it limits to the amount in the database to 30
            # after adding the first 3 weighting ones, if it isnt 30 get more to make it 30 from the __favourited_rated_films
            if self.__data_to_insert_for_first:  # there are values for this list
                inserts_info_to_database(FIELDS, TABLE, self.__data_to_insert_for_first[:30-amount_added_so_far]) # adds 30 to the database if there is 30
                amount_added_so_far += len(self.__data_to_insert_for_first)
            if self.__data_to_insert_for_mono:
                inserts_info_to_database(FIELDS, TABLE, self.__data_to_insert_for_mono)
                amount_added_so_far +=len(self.__data_to_insert_for_mono)
            if self.__data_to_insert_for_second and amount_added_so_far < 30:
                inserts_info_to_database(FIELDS, TABLE, self.__data_to_insert_for_second[:30-amount_added_so_far])
                amount_added_so_far += len(self.__data_to_insert_for_second)
            if self.__data_to_insert_for_third and amount_added_so_far < 30:
                inserts_info_to_database(FIELDS, TABLE, self.__data_to_insert_for_third[:30-amount_added_so_far])
                amount_added_so_far += len(self.__data_to_insert_for_third)

            if amount_added_so_far <30:
                remainder_to_add = []
                if len(self.__film_ids_gathered_to_recommend) >= 30-amount_added_so_far:
                    loop_size = 30-amount_added_so_far
                else:
                    loop_size = len(self.__film_ids_gathered_to_recommend)

                for i in range(loop_size):
                    # if there isn't 30 to add to the database will make it so that the remainder is made up of "self.__film_ids_gathered_to_recommend" films
                    remainder_to_add += [(self.__film_ids_gathered_to_recommend[i], self.user_id, 0)]

                inserts_info_to_database(FIELDS, TABLE, remainder_to_add)
        else: # only has films in the __film_ids_gathered_to_recommend function
            if len(self.__film_ids_gathered_to_recommend) >= 30:
                loop_size = 30-amount_added_so_far
            else:
                loop_size = len(self.__film_ids_gathered_to_recommend)

            to_add = [(self.__film_ids_gathered_to_recommend[i], self.user_id, 0) for i in range(loop_size)]
            inserts_info_to_database(FIELDS, TABLE, to_add)


    def __film_ids_from_director_function(self):
        """ 
        Gathers all of the film ids based on the director ids which were wanted and not wanted from the "directors" function
        The function is called and the film ids are assigned to the __film_ids_from_directors list,
        this is done so that threading can be used in the main class to speed up the data processing speed, so tasks can be preformed simultaneously
        """
        directors_wanted, directors_not_wanted = directors(self.__favourited_rated_films)
        
        if not directors_wanted and not directors_not_wanted:
            # no specific information given about either
            return # stops the function continuing

        wanted = "("+str(directors_wanted)[1:-1] + ")"
        not_wanted = "("+str(directors_not_wanted)[1:-1] + ")"
        # turned both the wanted and not wanted director ids into a string so that they can work in the sql statement
        where = f"DirectorID IN {wanted} AND FilmID NOT IN (SELECT FilmID FROM DirectorIntegrator WHERE DirectorID IN {not_wanted}) AND FilmID NOT IN {tuple(self.__favourited_rated_films)}"
        # doesn't select films which are already rated or favourited by the user since the user already has an opinion on them
        # only selects the films which those directors specified are in, so will not select any films where the directors are unknown.
        data = selects_info_from_database("FilmID, DirectorID", "DirectorIntegrator", where)
        self.__film_ids_from_directors = list(set([i[0] for i in data]))
        # where the first index of i is the index of the film, and turned into a set so that duplicated film ids are not in there
        # since some directors may work on the same film and appear in there twice

        # the double select statement above (where variable) is used so that the films that have directors which are not wanted are removed
        # using a singulal select statement then "AND DirectorID NOT IN (not_wanted)" would result in that film id still being in the results
        # its better to do it this way then to gather it from the database then remove the ones which are not wanted in python.
        # as doing so it will result in more memory overflow issues. since that data is not needed


    def __film_ids_from_actor_function(self):
        """
        Gathers all of the film ids based on the actor ids which were wanted and not wanted from the "actors" function,
        It groups together all of the films where it has multiple actors from the ones which are wanted
        (the only actor ids which are selected are the ones which were from the "actors" function)
        It adds all of the film ids where it has 2 or more actors (from the selected actors from the function) to the "__film_ids_from_actors" list.
        If there is not 100 films already in the list, then it will randomly select films where it only has 1 actor using the random.choice method
        Until the length of the list is equal to 100
        """
        actors_wanted, actors_not_wanted = actors(self.__favourited_rated_films)
        if not actors_wanted and not actors_not_wanted:
            return # empty list since there are none
        
        wanted = "("+str(list(set(actors_wanted)))[1:-1] + ")" # turned into a set first incase there are multiple actor ids which occure more than once
        not_wanted = "("+str(list(actors_not_wanted))[1:-1] + ")"
        films_from_db_not_wanted = selects_info_from_database("FilmID", "ActorIntegrator", f"ActorID IN {not_wanted}")
        films_not_wanted = set([i[0] for i in films_from_db_not_wanted])
        # the film ids which are not wanted because they contain an actor which is not wanted, as a set incase that more than 1 actor which is not wanted is in the same film
        where = f"ActorID IN {wanted} AND FilmID NOT IN {'('+str(self.__favourited_rated_films + list(films_not_wanted))[1:-1]+')'}"
        # does not select films which have already been rated or favourited and the films which contain an actor which is not wanted
        data = selects_info_from_database("FilmID, ActorID", "ActorIntegrator", where) # all of the film ids with the actors ids (FilmID, ActorID)

        grouped_data = groupings(data) # this is used to make sure that the film has actors in common
        grouped_data_list = list(grouped_data.items())
        for film_id2, list_of_actors in grouped_data_list:
            if len(list_of_actors) >= 2: # actors in common
                self.__film_ids_from_actors += [film_id2] # adds to a list all of the film ids which have 2 or more actors in common 
                del grouped_data[film_id2] # it is removed incase there are not atleast 100 films so that it can randomly select "x" unique film ids more to make it have 100 film ids

        if len(self.__film_ids_from_actors) < 100:
            # randomly selects film ids from the "grouped_data" dictionary, so that there are atleast 100 film ids to filter down
            # add append them to the self.__film_ids_from_actors, do not need to worry about selecting the same one twice as it has already been removed from the dictionary
            # self.__film_ids_from_actors += list(grouped_data.keys())[:100-len(self.__film_ids_from_actors)]
            self.__film_ids_from_actors += choices(list(grouped_data.keys()), k=(100-len(self.__film_ids_from_actors)))


    def __filtering_film_ids_down(self):
        """
        5 SECTIONS

        RUNTIME
        Find films which are longer or shorted than the wanted runtimes, and ignores films which have an unknown runtime

        RELEASE DATE
        Finds the films which are not in the bounds for the dates which the user will like, and adds it to the not_wanted list

        COLOUR
        Checks to see if any of the films do not have the colour which is wanted, and if they do have the colour which is not wanted then it is added to the not_wanted list.
        If a probability is given then gathers all of the monochrome films to represent later at the final stage

        LANGUAGE
        Finds films which do not have any of the languages which are wanted and adds them to the not_wanted list if they do not have any

        GENRE
        Films which have the highest desired combination are added to the "__first_weighting" list
        Films which have a desired combination will be added to the "__second_weighting" list aslong with singular genres which have the highest desirability
        Films which have desirable singular genres will be added to the "__third_weighting" list.
        Films which have combinations which are not wanted or genres which are not wanted are added to the not_wanted list
        If the genre is unknown, or does not contain one of the genres specified, then it will be just left and not added to any lists

        SUMMARY
        All of these 5 sections are done in 1 functions is since they are all done using a loop, important information is assigned and stated before the loop begins
        Each section is labled with its name
        Finds all of the unwanted film ids
        """
        runtime_lowerbound, runtime_upperbound = runtime(self.__favourited_rated_films)
        release_date_lowerbound, release_date_upperbound = release_date(self.__favourited_rated_films)
        colour_type_probability = colour(self.__favourited_rated_films)
        wanted_languages = language(self.__favourited_rated_films)
        combinations, genre_ids_and_weightings = genres(self.__favourited_rated_films)

        # for COLOUR
        UNKNOWN_ID = -1
        MONO_ID = 1 # if the film is in monochrome
        COLOUR_ID = 2
        colour_indicator_probability = colour_type_probability == UNKNOWN_ID or colour_type_probability == MONO_ID or colour_type_probability == COLOUR_ID
        # will be "True" if it is not a probability
        if not colour_indicator_probability:
            self.__mono = [colour_type_probability]
            # the first index is the proporition of monochrome films to represent, films which are monochrome are then added to this list
        # INDICATORS: used to determine if that section has information
        runtime_unknown = not runtime_lowerbound and not runtime_upperbound # Will be true if they are both unknown (returns [0,0], zeros for both values)
        colour_unkown = colour_type_probability == UNKNOWN_ID # all of the colour's of the films from the user, are unkown the value will be True
        language_unknown = not wanted_languages
        genre_unknown = not combinations and not genre_ids_and_weightings

        for film_object in self.__film_attributes: # all 5 sections use the same loop
            #RUNTIME
            if not runtime_unknown:
                if not runtime_lowerbound <= film_object.length <= runtime_upperbound and film_object.length != -1:
                    # "-1" since that is the value if the runtime is unknown so will ignore unknowns
                    self.__not_wanted += [film_object.film_id]

            # RELEASE DATE
            if not release_date_lowerbound <= film_object.release <= release_date_upperbound: # the year will never be unknown so there is no need to ignore it
                self.__not_wanted += [film_object.film_id]

            # COLOUR
            if not colour_unkown:
                if colour_indicator_probability: # it is not a probability
                    if film_object.colour != colour_type_probability and film_object.colour != -1: # ignores unknowns and checks to see if the colour of the film is not wanted
                        self.__not_wanted += [film_object.film_id] # adds it to the not_wanted list if that colour is not the colour wanted
                else: # it is a probability
                    if film_object.colour == MONO_ID: # gets all of the films which are monochrome
                        self.__mono += [film_object.film_id] # will use this later to represent the proportion of films which should to be mono out of the ones which have been recommeneded.

            # LANGUAGE
            if not language_unknown:
                # if the language id is unknown then it will be shown in the languages of the film object, with only one element in that list,
                # and in the wanted_languages the unknown language will never be in there so they will not have any in common
                if not len(set(film_object.languages) & set(wanted_languages)):
                    # if there are no common language between the languages which the user is likely to want and the languages of the films which have been recommended
                    self.__not_wanted +=[film_object.film_id]

            # GENRE
            if not genre_unknown:
                if len(film_object.genres) > 1: # it could potentially have a combo
                    had_combo = False
                    for genre_ids_in_combo, weighting in combinations:
                        if len(set(film_object.genres) & set(genre_ids_in_combo)) == len(genre_ids_in_combo): # they have that combo
                            had_combo = True
                            if weighting == 3:
                                self.__first_weighting += [film_object.film_id]
                            elif weighting == 2:
                                self.__second_weighting += [film_object.film_id]
                            else: # weighting would be equal to 0
                                self.__not_wanted += [film_object.film_id]
                            # there is not a criteria for if weighting equals 1 since for combinations it will never equal one.
                    if not had_combo: # the film did not have a combo in the list, then will look at the individual genres
                        self.__individual_genres(genre_ids_and_weightings, film_object)
                else:
                    self.__individual_genres(genre_ids_and_weightings, film_object)


    def __individual_genres(self, genre_ids_and_weightings: list, film_object: FilmAttributesForRecommendation):
        """
        Looks at all of the genres and its weightings, compares it to the data of that specific film (film_object)
        updates the variables which are stored inside of the class and is only called 2 times
        
        :param: genre_ids_and_weightings: list
        
        :param: film_object: FilmAttributesForRecommendation - which is an object
        """
        for genre_id, weighting2 in genre_ids_and_weightings:
            if genre_id in film_object.genres:
                if weighting2 == 2:
                    self.__second_weighting += [film_object.film_id]
                elif weighting2 == 1:
                    self.__third_weighting += [film_object.film_id]
                else: # weighting2 would be equal to 0
                    self.__not_wanted += [film_object.film_id]


if __name__ == "__main__":
    pass