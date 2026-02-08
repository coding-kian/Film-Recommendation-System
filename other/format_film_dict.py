from threading import Thread, active_count
from time import time

# imports from my project
from core_algos.formulas import selects_info_from_database

class AllFilmAttributes:
    def __init__(self, film_id: int, film_title: str, link: int, length: int, colour: int, release: str, img_url: str):
        self.film_id = film_id
        self.day = release[8:]
        self.month = release[5:7]
        self.year = release[:4]
        self.title = film_title.lower()
        self.link = link
        self.length = length
        self.colour = colour
        self.img = img_url
        self.genres = [] # An empty list; the values will be added in later
        self.languages = []
        self.actors = []
        self.directors = []
        self.budget = 0 # the value will be added in later, if there is one to add
        self.revenue = 0
        

class FilmAttributesForRecommendation:
    def __init__(self, film_id: int, length: int, colour: int, release: str, language_list: list, genre_list: list):
        self.film_id = film_id
        self.length = length
        self.colour = colour
        self.release = int(release[:4]) # just going to select the first 4 indexs as they are the value of the year
        self.languages = language_list
        self.genres = genre_list



NO_IMAGE = "https://i.imgur.com/pleyMQq.png"
# the link to the picture if something does not have an image (missing image picture)


def information_about_films_as_objects(film_ids: list):
    """
    Creates objects for each film

    :param: film_ids: list

    :return: all_objects_of_film_information: list
    """
    film_data = selects_info_from_database("*", "Films", f"FilmID IN {'('+str(film_ids)[1:-1]+')'}")
    all_objects_of_film_information = [AllFilmAttributes(film_id, name, link, length, colour, release_date, img_url) for
                film_id, name, link, length, colour, release_date, img_url in film_data]

    return all_objects_of_film_information


def adds_to_information_to_display_dictionary_for_films(information_about_films: dict, film_object: AllFilmAttributes,
        all_actor_ids_related_to_films: list, all_director_ids_related_to_films: list,
        all_genre_ids_related_to_films: list, all_language_ids_related_to_films: list):
    """
    Takes in the dictionary as a param which will be updated, and does not need to be returned since it is a global inside of the function,
    the function may be called in the same cpu cycle since it is being threaded and the dictionary can be updated in each thread
    seperately.  film_object is an object created from the classes.AllFilmAttributes class.

    :param: information_about_films: dict

    :param: film_object: classes.AllFilmAttributes

    :param: all_actor_ids_related_to_films: list
    
    :param: all_director_ids_related_to_films: list

    :param: all_genre_ids_related_to_films: list
    
    :param: all_language_ids_related_to_films: list
    """
    different_colours = {1: "Black and White", 2: "Colour", -1: "Unknown"}
    # ids of the colour of the film in the database, to what word they correspond to
    colour = different_colours[film_object.colour]
    if film_object.img == "U": # no image
        img = NO_IMAGE
    else:
        img= "https://m.media-amazon.com/images" + film_object.img

    economy = selects_info_from_database("Budget, GrossRevenue", "Economy", f"FilmID = {film_object.film_id}")
    # the budget and revenue of the film is not stored in the main table, so will have to gather the information from a seperate table
    # it is not stored in the same table as quite alot of films have both the budget and the revenue unknown so that field would
    # of just been filled with alot of unknown values, and this method will reduce the file size of the database
    if economy:
        if economy[0][0] <= 0:
            # if it is unknown then it is -1, so i will change it to 0
            # films may have a known budget but an unknown revenue since they may still be in cinemas
            film_object.budget = 0
        else:
            film_object.budget = economy[0][0] #  if the number is 123456789, will put it in the format:- 123,456,789
        if economy[0][1] <= 0:
            film_object.revenue = 0
        else:
            film_object.revenue = economy[0][1]

    if film_object.length <= 0:
        # runtime/length of the film is unknown
        length = 0
    else:
        length = film_object.length

    date = "" # used to put the date in a nice format
    if film_object.day != "00":
        date += film_object.day +"/"
    if film_object.month != "00":
        date += film_object.month + "/"

    # Genrs, Languags, Actors and directors
    genre = [i[0] for i in selects_info_from_database("CAST(GenreID AS VARCHAR(11))", "GenreToFilm", f"FilmID = {film_object.film_id}")]
    # If they have have the same film_id then they will match genre_link is a list, ect... for other things.  removed it so that it is not a list of tuples
    # It is converted into a string with the CAST function in SQL, so that when the films are reordered by an attribute,
    # it works, since json.loads require all elements in a dictionary to have "double quotes" around them
    language = [i[0] for i in selects_info_from_database("CAST(LanguageID AS VARCHAR(11))", "LanguageToFilm", f"FilmID = {film_object.film_id}")]
    actor = [i[0] for i in selects_info_from_database("CAST(ActorID AS VARCHAR(11))", "ActorIntegrator", f"FilmID = {film_object.film_id}")]
    director = [i[0] for i in selects_info_from_database("CAST(DirectorID AS VARCHAR(11))", "DirectorIntegrator", f"FilmID = {film_object.film_id}")]

    # adds the ids for the actors, directors, genres and languages, to the list which contains all of the ids for the page which
    # will be displayed, so that later on it can gather information specifically about each one, without passing in repeated info
    all_actor_ids_related_to_films += actor
    all_director_ids_related_to_films += director
    all_genre_ids_related_to_films += genre
    all_language_ids_related_to_films += language

    # cannot have "'" in the title or post because when you i use json.load it causes problems because, i need to replace all "'" with """ and then 
    # the title could look like "Bob"S Bag", and would crash the program
    information_about_films[film_object.film_id] = {"id": film_object.film_id, "title": film_object.title.title().replace("'", "`"), "length": length,
        "link": film_object.link, "budget": film_object.budget, "revenue": film_object.revenue,
        "date":  date, "year": str(film_object.year),
        "genres": genre, "languages": language, "actors": actor, "directors": director,
        "colour": colour, "poster": film_object.title.title().replace(" ", "").replace("'", "`"),
        "url": img}
        # updates the dictionary


def turning_film_information_into_dictionary(film_ids: list, ordered: bool = False):
    """
    Gathers all of the information about all of the films from the database.
    Puts it into a nice format which the user can read easily, and gathers all of the extra information
    about the actors and directors which will be used to display in a modal in the website.
    it then returns a list of dictionaries with all the information about the films, 
    which can be looped through on the website using jinja2 and all of the information is displayed

    :param: film_ids: list
    
    :param: ordered: bool

    :return: gathered_and_formatted_information_about_films: list

    :return: actors: dict

    :return: directors: dict

    :return: genres: dict

    :return: languages: dict
    """
    start_time = time()

    all_film_information_objects = information_about_films_as_objects(film_ids)
    # gathers all of the main information about the films from the film table in the database, and turns them into objects
    # from the classes.AllFilmAttributes class, which will have extra information added to it, including actors, directors, genres and languages
    information_about_films = {}
    running_threads = [] # used to check and make sure all of the threads have stopped before the value information is returned
    all_actor_ids_related_to_films = []
    all_director_ids_related_to_films = []
    all_genre_ids_related_to_films = []
    all_language_ids_related_to_films = []

    print(f"CONSOLE OUTPUT ONLY: Time to make object for data--- {time()-start_time}")
    start_time = time()
    for index, film_object in enumerate(all_film_information_objects):
        flag = True
        while flag:
            if active_count() <150:
                running_threads += [Thread(target = adds_to_information_to_display_dictionary_for_films, args = (information_about_films, 
                    film_object, all_actor_ids_related_to_films, all_director_ids_related_to_films, all_genre_ids_related_to_films, all_language_ids_related_to_films))]
                running_threads[index].start()
                flag = False
            else: flag = True
    [i.join() for i in running_threads] # waits for all of the threads to finish running

    if ordered == True:
        # if the film_ids are already in a particular order then they will be put back into their original order
        gathered_and_formatted_information_about_films = [information_about_films[i] for i in film_ids]
    else:
        # if they are not in a order then they will be ordered by the film with the largest revenue
        gathered_and_formatted_information_about_films = sorted(list(information_about_films.values()), key = lambda x: x["revenue"], reverse = True)

    actors = {}
    directors = {}
    genres = {}
    languages = {}
    if information_about_films:
        if all_actor_ids_related_to_films:
            # if there are any actors known then i will gather the information about them
            # only need the name and the url so that the user can see which actors were in the film
            # then if they are interested in more information then they can click on them and find the films they have been in
            actor_data = selects_info_from_database("CAST(ActorID AS VARCHAR(11)), ActorName, ImageURL",
                "Actors", f"ActorID IN {'('+str(set(all_actor_ids_related_to_films))[1:-1]+')'}")
            for actor_id, name, img_url in actor_data:
                if img_url == "U": # there is no image
                    # appends it to the dictionary
                    actors[actor_id] = [name, NO_IMAGE]
                else:
                    actors[actor_id] = [name, "https://m.media-amazon.com/images"+img_url]

        if all_director_ids_related_to_films:
            # same principal as actors
            director_data = selects_info_from_database("CAST(DirectorID AS VARCHAR(11)), DirectorName, ImageURL",
                "Directors", f"DirectorID IN {'('+str(set(all_director_ids_related_to_films))[1:-1]+')'}")
            for director_id, name, img_url in director_data:
                if img_url == "U":
                    directors[director_id] = [name, NO_IMAGE]
                else:
                    directors[director_id] = [name, "https://m.media-amazon.com/images"+img_url]

        if all_genre_ids_related_to_films:
            # if there are any genres known then will gather the name of the genre
            # then it will assign it to the dictionary
            genres = dict(selects_info_from_database("CAST(GenreID AS VARCHAR(11)), Genre", "GenreNames",
                f"GenreID IN {'('+str(set(all_genre_ids_related_to_films))[1:-1]+')'}"))

        if all_language_ids_related_to_films:
            # same principal as genres 
            languages = dict(selects_info_from_database("CAST(LanguageID AS VARCHAR(11)), Language", "Language",
                f"LanguageID IN {'('+str(set(all_language_ids_related_to_films))[1:-1]+')'}"))

    print(f"CONSOLE OUTPUT ONLY: Took this long to create dictionary--- {time()-start_time}")
    
    return gathered_and_formatted_information_about_films, actors, directors, genres, languages # Then display this on the webiste


if __name__ == "__main__":
    pass