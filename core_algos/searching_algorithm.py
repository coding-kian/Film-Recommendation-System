from spellchecker import SpellChecker
from json import load
from collections import Counter

# imports from my project
from core_algos.formulas import binary_search, selects_info_from_database


def spell_checks_query(query: list):
    """
    Spell checks the query which the user has enetered, splitting it into a list at spaces and *dahses* "-", checking the spelling of these words.
    If any of these words in the query have an error then it will update the query with the corrections
    If there are no spelling errors or if there are more than 5 spelling errors,
    aswell as if the amount of words needed to check is the same amount as the words in the query (but not 1) and the original amount of words in the query is less than 7
    then it will return the original query as a 2d array of 1 element.
    else it will return a 2d array with 2 elements the first being the original query and the second being the spell checked one
    
    :param: query: list

    :return: TYPE: list - 2d array of the orginal query and potentially the possible correction if there was an error
    """
    spell_distance2 = SpellChecker(distance=2)
    if len(query) >= 7: # too long
        return [query]
    # Since all of the films in the database, have the first letter of a word capitalised, the title() string formatter puts it in that form
    # All symbols, numbers and any other non-alphabetical element is considered and not changed.
    # Replacing all *dashes* "-" with spaces, so that the user's query is split at all spaces, and each word is considered when being spell checked.
    # Later on when searching for the query it may look at the query with the *dash* in it depending on the conditions set, as the *dashes* in the films are not removed
    need_to_check = spell_distance2.unknown(query) # returns a set of all the words which have potentially been spelt incorrectly
    spell_checked_results =[]

    if len(need_to_check) == 0 or (len(need_to_check) == len(query) and len(query) != 1):
        # probably in a different language if all words are spelt incorrectly,
        # but if it is just one word in the query and it is spelt incorrectly then will use the spell checking algorithm on it
        return [query] # everything is spelt correct returns the list unchanged
    else:
        spell_distance1 = SpellChecker(distance=1) # Used on longer words, since if a distance of 2 is used then it will take too long, as that is a more thorough spell check
        # when looking at the word which has been spelt incorrectly, only returning the most likely spelling of this word,
        # as the query may have multiple words, so will create a combination,
        # of the possible results which they could of meant instead. reutning a maximum of 3 combinations
        for word in need_to_check:
            if len(word) > 4:
                corrected = spell_distance1.correction(word).title()
            else:
                corrected = spell_distance2.correction(word).title()

            if corrected != word: # a better spell has been found
                spell_checked_results += [(word.title(), corrected)] # the word which has been spelt incorrect and the correct spelling of that word
    
    # creating the results to display to the user
    if len(spell_checked_results) == 0:
        return [query] # no words have a better spelling so the list remains unchanged

    if len(spell_checked_results) >= 5: # too many spelling errors
        return [query] # unchanged
    else:
        updated_query = [query.copy(), query.copy()] # copies the list so that the original one is still the same
        # Returns the original query and then the corrected query
        # 1. Original
        # 2. Completely changed

        for i in range(len(spell_checked_results)): # replaces all of the incorrectly spelt words
            occurence_of_incorrectly_spelt_word = query.count(spell_checked_results[i][0])
            for _ in range(occurence_of_incorrectly_spelt_word):
                list_index = query.index(spell_checked_results[i][0])
                updated_query[1][list_index] = spell_checked_results[i][1]

        return updated_query # first index is the original query and the second index is the corrected one


def removing_common_words(query: list):
    """
    Takes the users spellchecked query as a list (may be changed may not be changed)
    Gathers the top 30 most common words from the "common_words.json" file which has been created by scraping the database
    Loops through the query list and removes all of the common words; but will not remove more than half of the words
    Will start by removing the most common words in the database to the least

    :param: query: list

    :return: word_to_gather: list
    """
    word_to_gather = list(set(query.copy()))
    # Since this is only going to be used in the sql query in {like '%word%'}, having the same word multiple times in the query makes no sense
    length = len(word_to_gather)

    with open("searching/common_words.json") as file:
        most_common_words = load(file) 
    most_common_words_list = list(most_common_words.keys()) # in order of occurence, without occurence top 30
    if length <=2:
        pass
    else:
        count = 0 # tells the algorithm, how many words have been removed so far
        for word in most_common_words_list: # looping through this list so that the more common words in the database are removed first
            if count == length//2: # makes sure not more than half of the words are removed
                break
            elif word in word_to_gather: # if the word is in the user's query
                count += 1
                word_to_gather.remove(word)
    
    return word_to_gather


def gathering_data(corrected_querried: list, year_criteria: list, genre_criteria: list, language_criteria: list, film_actor_or_director: int):
    """
    The user has entered a query this has been spellchecked and correct with the common words removed, if it is a film.
    The function, goes through all of the elements in the list and creates a where statement to select all of the, films, actors or directors,
    which the words in the query in. 
    Adds the criteria to the where statement if the user has entered any. 
    Excecutes the sql statement and gathers the data from the database.

    :param: corrected_querried: list
    
    :param: year_criteria: list
    
    :param: genre_criteria: list
    
    :param: language_criteria: list

    :param: film_actor_director: int

    :return: TYPE: list - list of tuples (id, name) where id and name is for the film, actor or director
    """
    if not film_actor_or_director:
        FIELD = "Film"
    elif film_actor_or_director == 1:
        FIELD = "Actor"
    else:
        FIELD = "Director"
    where_statement = "("
    join_statement = ""
    for index, element in enumerate(corrected_querried):
        where_statement += f" {FIELD}Name like '%{element}%'"
        if index+1 != len(corrected_querried):
            where_statement += " OR"
        else:
            where_statement += ")"

    if not film_actor_or_director: # the user is searching for a film
        if year_criteria:
            
            
            where_statement += f" AND ReleaseDate > {year_criteria[0]} AND ReleaseDate < {year_criteria[1]+1}" # adds it to the where statement
        if genre_criteria: # the genreid may be 0. So will need to send None if the user does not select anything
            # Menu on the website to select the genre.
            # The user select the genre name which they want to see films for, from a checklist
            # With the menu on the website the id of the item will be the genre id, so will pass the genre id into the function
            
            where_statement += f" AND GenreID IN {'('+str(genre_criteria)[1:-1]+')'} AND GenreToFilm.FilmID = Films.FilmID"
            join_statement += " JOIN GenreToFilm"
        if language_criteria:
            # same principle as the genres
            where_statement += f" AND LanguageID IN {'('+str(language_criteria)[1:-1]+')'} AND LanguageToFilm.FilmID = Films.FilmID" 
            join_statement += " JOIN LanguageToFilm"
        return selects_info_from_database("Films.FilmID, Films.FilmName", "Films"+join_statement, where_statement)
        # selects and returns all of the Film IDs and Film Names from the database for the criteria
    
    else:
        if year_criteria: # Same as for films, just different field names
            where_statement += f" AND DOB > {year_criteria[0]} AND DOB < {year_criteria[1]+1}"
        return selects_info_from_database(f"{FIELD}ID, {FIELD}Name", f"{FIELD}s", where_statement)


def data_which_have_each_word(data: list, original_query: str, query: list, film_actor_or_director: int):
    """
    Takes the ids and the names of the films, actors or directors, splits them into seperate lists (all_ids, all_names).
    The query is split into a list at each word interval so that the algorithm can find the films which have each word in
    If a film, actor or director has more than 1 of the words in the query then it's title, then it will
    be favoured over the ones which do not to find the best result.

    :param: data: list

    :param: original_query: str

    :param: query: list

    :param: film_actor_or_director: list

    :return: TYPE: Counter - from the collection module, all of the data tallied up with frequencies
    """
    all_names = []
    all_ids = []
    for i, n in data: # i = ids, n = names
        all_names += [n]
        all_ids += [i]

    have_exact_in = []
    tallied_data = []
    # creates a list with all of the ids, but the id will be appear more than once if it has more than 1 of the words in the user's query
    # So that the counter module can be used, to find the most accurate result
    for index, name in enumerate(all_names): # loops through all names
        # if the user is searching for e.g. "here" but the word is "there" since the first letters are in capitals it will not be found,
        # so casefold makes them the same, incase the user made a typo which the spell checker didn't pick up
        if original_query.casefold() in name.casefold():
            # casefold makes sure that they are exactly the same comparison
            have_exact_in += [all_ids[index]]
        for word in query:
            if word.title() in name.title(): # is part of the query, in the name of the film, actor or director.
                tallied_data += [all_ids[index]]
        if len(name.split(" ")) == 1 and len(query) == 1:
            # It is an even closer match since it only has 1 word and the user's query only has 1 word
            have_exact_in = [all_ids[index]]
    
    for _id in have_exact_in:
        tallied_data += [_id]*10
    return Counter(tallied_data)


def finding_top_data(tallied_data, original_query: str, film_actor_or_director: int , is_one: bool):
    """
    Gathers the top 50 films if the user is searching for a film or the top 30 actors or directors if the user is searching for an actor or director
    It returns a list in order of the most relevant, with the first index being the most relevant to the user's search
    If the user's query only has 1 word in it then it will perform a binary search to find the films which have only that word in it (as an exact match)
    and append it to the front of the list, then fill in the remaining amount of space with data ordered by the revenue if it is a film (highest revenue first)
    and if it isn't a film then it will just select a random id to append.
    If the revenue is unknown then it will just append a random id to fill in the space required.
    If the query has more than 1 word, then it will look at the films (if it is a film) which have the most amount of words from the query in it and
    append those to the front of the list in descending order of the revenue, and so on until the 50 films are reached.
    For actors and directors though it will just append the ids with the highest occurence of different words at the front of the list until 30 actors or directors have been added
    The data gathered from here will be displayed in sets of 10s

    :param: tallied_data: Counter or list.
    If is_one is False then tallied_data will be a Counter object (ID, OCCURENCE), where OCCURENCE is the amount of words in the user's query
    But if is_one is true then tallied_data will be a list of tuples like (ID, NAME)

    :param: original_query: str

    :param: film_actor_or_director: int

    :param: is_one: bool
    
    :return: to_display: list
    """
    to_display = []
    if is_one:
        # tallied_data:- won't be a Counter, if it isnt turned into a Counter before being entered into the function,
        # it is just a list if there is only 1 word in the user's search query
        # the query only has 1 word in it, so that all information selected from the database has the query in it, (equal occurence)
        sorted_data = sorted(tallied_data, key = lambda x: x[1]) # sorts them by the name
        all_names = []
        all_ids = []
        for i, n in sorted_data: # i = ids, n = names 
            all_names += [n]
            all_ids += [i]

        index = binary_search(all_names, original_query.title())
        if index != None:
            for amount, name in enumerate(all_names[index -6:  index +5]):
                # looking at either side (5 each side 11 possible matches) to see if there are anymore exact matches, will need to make all_names sorted though
                if name == original_query:
                    if len(all_names[index -6:  index +5]) <= 11:
                        # the film may have only exact matches and only 5 of them, if that is the case
                        # then it will just add all of the films to disply instantly
                        # also if there are less than 11 films found then they will all be on the first page anyway
                        # so if they are not exact matches it does not matter if they are not in the first slot when
                        # the user views the page, since they are on the same page
                        to_display = all_ids[index -6:  index +5]
                    else:
                        to_display += [all_ids[index+amount-6]]

            for id2 in to_display:
                all_ids.remove(id2)

        if not film_actor_or_director: # FOR FILMS
            films = [i[0] for i in selects_info_from_database("FilmID", "Economy", f"FilmID IN {'('+(str(all_ids))[1:-1]+')'} ORDER BY GrossRevenue DESC")]
            for id3 in films:
                all_ids.remove(id3) 
            # Calls the function it to just order it the films by revenue

            to_display += films[:50-len(to_display)] # first 50 films
            if len(to_display) != 50 and len(to_display) != len(all_names):
                # some do not have a revenue, (not in that table): Does not have 50 films to display yet and not all films have a revenue. 
                # Some films may be in the table but the revenue is unknown, they will be at the end of the list so does not matter
                to_display += all_ids[:50 - len(to_display)] # gets 50 to display even if the revenue is unknown
        else:
            to_display += all_ids[:30-len(to_display)]

    else:
        # GO TO CONSIDER IF IT IS AN ACTOR, DIRECTOR OR FILM
        count = 0 # the amount already added to display
        highest_ocurence = tallied_data.most_common(1)[0][1]
        grouped_occurence = {highest_ocurence-i: [] for i in range(highest_ocurence)}
        # a dictionary where the id is the occurence and the values is a list of all the ids with that occurence
        # then can select from each list from the database
        for _id, occurence in dict(tallied_data).items(): # where _id, is the id of the film, actor or director
            grouped_occurence[occurence] += [_id]

        if not film_actor_or_director:
            for film_ids in grouped_occurence.values():
                if film_ids:
                    from_db = [i[0] for i in selects_info_from_database("FilmID", "Economy", f"FilmID IN {'('+(str(film_ids))[1:-1]+')'} ORDER BY GrossRevenue DESC")]
                    to_display += from_db[:50-count]
                    count += len(from_db)
                    if count >= 50:
                        break

                    if len(from_db) < len(film_ids): # not all the films have a revenue
                        for i in from_db: # removes all of the film ids already added
                            film_ids.remove(i) 
                        to_display += film_ids[:50-count]
                        count += len(film_ids)
                        if count >= 50:
                            break

        else: # for actors or directors
            for people_id in grouped_occurence.values():
                if people_id:
                    to_display += people_id[:30-count]
                    count += len(people_id)
                    if count >= 30:
                        break
    return to_display


def gathers_potential_spellchecked_query(query: str):
    """
    When the user is searching for a film, it will spell check the query, and return the potential options
    Will return none if the user did not enter a query, the query would be "". Will return False if there are no potential
    spell checked options, and if there are options it will return more_possible_query_results, which is a list of the original query
    and the potential option

    :param: query: str

    :return: more_possible_query_results: list
    """
    if not query: # User just clicked submit without entering a query
        return None

    listed_query = query.replace("-", " ").strip().title().split(" ") 
    more_possible_query_results = spell_checks_query(listed_query)
    if len(more_possible_query_results) == 1: # no corrected result
        return False
    else: # Will have 1 corrected result, and the original one aswell
        return more_possible_query_results


def searching_algorithm_gathers_film_ids_to_display(query: str, year_criteria: list, genre_criteria: list, language_criteria: list, film_actor_or_director: int):
    """
    The main function of finding the search query which the user has entered for a film, actor or director.
    It will first remove all of the most common words if it is a film, where the most common words are the ones 
    which appear the most in the database.
    It splits the user's query into a list at all spaces " " and finds all of the individual parts to the query in from the database
    so it will select all of the films, actors or directors which have atleast 1 of the parts of the uesr's query.
    It will then create a hierarchy of the films, actors or directors which have the most words/parts in compared to the user's query
    I will then order all of the ids to be in order of the hierarchy and return the results to display on the website.
    if the param "film_actor_or_director" is equal to 0 then it is a film, equal to 1 then an actor, equal to 2 then director

    :param: query: str

    :param: year_criteria: list

    :param: genre_criteria: list

    :param: language_criteria: list

    :param: film_actor_or_director: int

    :return: film_actor_or_director_ids_to_gather_information_about_to_display: list

    :return: amount_of_films_or_people_filtered_through: int
    """
    is_one = True
    listed_query_to_find = query.replace("-", " ").strip().title().split(" ")

    if film_actor_or_director: # actor or director
        common_words_removed = listed_query_to_find
    else:
        common_words_removed = removing_common_words(listed_query_to_find)

    data = gathering_data(common_words_removed, year_criteria, genre_criteria, language_criteria, film_actor_or_director)
    # where data is all of the potential, film, actor or director ids from the database
    amount_of_films_or_people_filtered_through = len(data)
    print(f"CONSOLE OUTPUT ONLY: Amount of {film_actor_or_director} (number is type) found in database is --- {amount_of_films_or_people_filtered_through}")
    
    if not data: # no data gathered from the database
        tallied_data = []
    elif len(listed_query_to_find) > 1:
        # all results from the database would have the query in it, if it was just 1 word to find...
        tallied_data = data_which_have_each_word(data, query, common_words_removed, film_actor_or_director) # gathers a Counter object
        is_one = False
        if len(tallied_data) == 0:
            # the user has probably made a spelling error what the spell checker was not able to pick up
            # but the SQL "like" statement was still able to select the films they most likely meant
            tallied_data = data
    else:
        tallied_data = data 

    if tallied_data:
        film_actor_or_director_ids_to_gather_information_about_to_display = finding_top_data(tallied_data, query, film_actor_or_director, is_one)
        # will return the top 50 films and top 30 actors or directors if there that many
    else:
        film_actor_or_director_ids_to_gather_information_about_to_display = []
    
    return film_actor_or_director_ids_to_gather_information_about_to_display, amount_of_films_or_people_filtered_through


if __name__ == "__main__": 
    pass