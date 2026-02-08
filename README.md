# Film Recommendation System (Historical Project)
> Project build between March 2019 to January 2020, Published February 2026. It was created through independent research and experimentation by reviewing documentation on stack-overflow and github and YouTube tutorials, during the time, there was no modern AI/LLM coding assistance.

**Full redacted report** See PDF report `publish1.pdf` 200 pages, 45,000 words, contains full system A-Z breakdown for reproducibility.
**Sliced & Sped-up Video** Initially 1 hour testing video now 14 minutes of system walk through. `https://www.youtube.com/watch?v=mgqsi3ZWcYA`

core_algos and other are unedited files from the original project, the main part of the project is the custom search and recommendation algorithm. 
The HTML template is used to show how python (app.py) is connected using jinja2, google ajax is now depreciation so it has been removed, so has the bootstrap CCS, but the dynamic JavaScript is shown on the website.
# Files
core_algos/ **Primary Focus**
- `calc_recommendations.py`
- `formulas.py`
- `gathering_types.py`
- `searching_algorithm.py`
other/
- `app.py` (trimmed)
- `display_film_information.html`
- `format_film_dict.py`
- `leaderboards.py`

**Database: sql.pdf**

---

# Overview of project
> As a historic repo, it has been cleaned-up to highlight the most salient parts - the search and recommendation algorithms. The messy ingestion/scraping, database storage, email information and encryption algorithms has been removed. 
The primary focus is to showcase how I started off, with a curated snapshot, the PDF provides full reproducibility of the code and the video shows the full system working. Since the creation of this project my knowledge and skills have drastically expanded, however my core interest for background effiency optimisation and probability remain unchanged. 


- Built in python, with flask as the core package, with a SQLite database for storing major information supported with json files. 
- Users can login and register, on an encrypted system which is connected to their email (email notifications sent)
- Users can search for films, actors, and directors, with filters like genre, language and release date. 
- Additional option to view leaderboards eg. most rated movies and highest revenues.
- Custom search algorithm is used with binary search to find actors, directors and films.
- Once found all related actors and directors are linked to the film and visa-versa
- Option to favourite and rate films, to for the system to learn their most probable recommendation using binomial distrbution
- Recommendations generated with the above custom algorithm, weighted using genre, language, actors, directions, release date and more. 

---

# What is showcases
- Backend deicision making: Custom scoring, ranking and probabilistic thinking, traditional likelihood moddelling
- Search and recommendation - performance aware filtering and result quantification
- Data moddeling with complex non-linear relationships

---

# Author note (then vs now).
Overall the 45,000 words with over 200 pages was not needed for the specification of the task.
However considering my experience at the time and and machine learning being less developed compared to mordern times, overall my heuristic approach to the recommendation and search algorithm is impressive. Backend probability optimisation is my forte focussed in Python (now also solidity).  
My writeup is holistic and extremely detail oriented, looking back at that now, I could use a single example as a proxy example for similar methods, making it more functional to read. Assumed naivety can save drastic amount of workflow, which is my core principal of efficiency and optimisation.
This project is my origin story and I am proud of it as it shows my persistent and dedication to delivering what I promise.
