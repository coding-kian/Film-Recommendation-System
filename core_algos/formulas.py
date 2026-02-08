from math import sqrt
from sqlite3 import connect


def mean_and_sd(list_of_values: list):
    """
    Calculates the variance using the formula
    SUM(X*X)/n - mean*mean, where X is each individual element in the array of data
    Once varience is found square roots it for the standard deviation (sd)
    
    :param: list_of_values: list
    
    :return: mean: float
    
    :return: sd: float
    """
    total = sum(list_of_values)
    amount = len(list_of_values) 
    mean = total/amount
    values = map(lambda x : x**2, list_of_values)
    variance = (sum(values)/amount) - (mean)**2
    sd = sqrt(variance)
    return mean, sd


def factorial(val: int):
    """
    Calculates the factorial of the paramater
    
    :param: val: int
    
    :return: factorial: int
    """
    factorial = 1
    for i in range(1,val+1):
        factorial*=i
    return factorial


def combination_formula(total: int, position: int):
    """
    nCr, combination formula, used to calculate permutation, the different combinations which can occure.
    n is the number of items (total)
    r is the number of items being chosen (position)
    this uses the pascal triangle, and n would be the line number and r would be the positon along that line
    
    :param: total: int
    
    :param: position: int
    
    :return: events: int
    """
    factorial_total = factorial(total) # the amount of ways the even can occur
    factorial_difference = factorial(total-position)
    factorial_position = factorial(position) # use to delete duplications of events
    events = factorial_total/(factorial_difference*factorial_position)
    return events


def binomial_distribution(lower: int, upper: int, trial: int, probability: float):
    """
    Calculates the probability of getting a value between the lower and upper value based on the amount of trials
    if lower is the same as upper then it will work out the proability of getting 1 value.
    the lower and upper bounds are inclusive
    Additional info, trial * probability, is the mean value, the probability is worked out around this value.
    
    :param: lower: int
    
    :param: upper: int
    
    :param: trial: int
    
    :param: probability: float
    
    :return: value: float
    """
    if lower == upper:
        value = ((1-probability)**(trial-lower)) * (probability**lower)*combination_formula(trial,lower)
    elif lower > upper:
        value = None
    else:
        value = 0
        for i in range(lower, upper+1): # This adds together all the probabilities
            value += ((1-probability)**(trial-i)) * (probability**i)*combination_formula(trial,i)
    return value


def binary_search(values: list, target: str, startpoint: int =0, endpoint: int =None):
    """
    Rular binary search OLog(n), justing using a recursive algorithm, just using recursion.
    
    :param: values: list
    
    :param: target: str
    
    :param: startpoint: int
    
    :param: endpoint: int
    
    :returns: False, if the target is not in the values list, but otherwise it will return itself,
    and go through the algorithm again, once the target has been located then it will return the position
    """
    if endpoint is None: endpoint = len(values) - 1
    if startpoint > endpoint: return False # An error has occured

    midpoint = (startpoint + endpoint) // 2
    if target == values[midpoint]: return midpoint # Has found the position in the list where the target is
    elif target < values[midpoint]: return binary_search(values, target, startpoint, midpoint - 1)
    elif target > values[midpoint]: return binary_search(values, target, midpoint + 1, endpoint)


def selects_info_from_database(fields: str, table: str, where_statement: str):
    """
    Gets the information from the database for the fields entered based on the where condition specified.
    
    :param: fields: str
    
    :param: table: str
    
    :param: where_statement: str
    
    :return: information: list
    """    
    with connect("database/MainDB.db", timeout= 300) as db:
        pointer = db.cursor()
        pointer.execute(f"SELECT {fields} FROM {table} WHERE {where_statement}")
        information =  pointer.fetchall() # all of the information requested about information and condition given
    return information


def inserts_info_to_database(fields: str, table: str, data: list):
    """
    Inserts all of the data specified into the database
    
    :param: field: str
    
    :param: table: str
    
    :param: data: list - 2d list of tuples
    """
    question_marks = ",?"*fields.count(",")
    with connect("database/MainDB.db", timeout= 300) as db:
        pointer = db.cursor()
        pointer.executemany(f"INSERT INTO {table} {fields} VALUES (?{question_marks})", data)
        # executemany allows data to be a list of multiple values instead of just 1
        db.commit()


def deletes_from_database(table: str, where_statement: str):
    """
    Deletes data from table where it meets the where condition
    
    :param: table: str
    
    :param: where_statement: str
    """
    with connect("database/MainDB.db", timeout= 300) as db:
        pointer = db.cursor()
        pointer.execute(f"DELETE FROM {table} WHERE {where_statement}")
        db.commit()


def updates_database(fields: str, table: str, where_statement: str, data: tuple):
    """
    Updates the fields specified where it meets the where criteria.
    The where statement will look like "Field=? AND Field2=?", and data with all all the items to add to the database

    :param: field: str
    
    :param: table: str

    :param: where_statement: str

    :param: data: tuple
    """
    fields_formatted = fields.replace(",", "=?,")+"=?"
    with connect("database/MainDB.db", timeout= 300) as db:
        pointer = db.cursor()
        pointer.execute(f"UPDATE {table} SET {fields_formatted} WHERE {where_statement}", data)
        db.commit()


def groupings(data_to_group: list):
    """
    Groups together all of the information which is given as a paramater, where data_to_group is a 2d list of tuples with each tuple having 2 values,
    the first value in the tuple is the film id and may occur more than once so this will group them together in a dictionary
    
    :param: data_to_group: list

    :return: grouped_data: dict
    """
    grouped_data = dict() # the result will look like :- {filmID: [1,2,3,4]} where: 1,2,3,4 are all ids of the data which have been grouped
    for film_id, data_id in data_to_group: # where data_id is the id of the information which is wanted to be grouped
        if film_id in grouped_data.keys():
            grouped_data[film_id] += [data_id]
        else:
            grouped_data[film_id] = [data_id]
    return grouped_data


if __name__ == "__main__":
    pass