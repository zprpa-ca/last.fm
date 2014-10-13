
Sample showcase project of the complex data structure analytics using the
Python environment, SQL and database, HDF5 binary files, REST API and JSON,
Javascript (Highcharts, JQuery).



=================
Task description:
=================

Goal:
Construct a data set that relates Last.fm tags to each other, revealing
which genres (and other tags) are most associated.

Details:
Using the Last.fm API, collect the top tags among a large set of
popular artists (1000 or more). This data should be structured and stored in
whatever format is deemed most efficient. From this raw data, create a metric
that compares how strongly associated the tags are to each other.
Additionally, include any weighting or balancing in the metric, as long as it
can be explained.

Resources:
API documentation can be found at <http://www.last.fm/api>.

Deliverables:
- Code.
- Data sets, both intermediate steps and the final output.
- Short explanation of process and outcomes.

Extra credit ideas:
Use tags data to compute the similarity between artists.
Compare our tags data to the "similar tags" data in the API and highlight what
is the same and what is different.



=====================
Solution description:
=====================

Technical requirements:
-----------------------
- Python 2.7.6
- Numpy 1.8.1
- h5py 2.3.0
Linux distribution recommended.


Environment structure and description:
--------------------------------------
HOME_DIR:
- 01.load-source-data.py
- 02.tag-correlation.py
- 03.artist-correlation.py
- 04.compare-similar.py
- utils.py
- README.txt
- create-tables.sql
- tag-correlation-heatmap.htm
- tag-correlation-heatmap.template
- data/
    |- lastfm.sql3
    |- tag-correlation-datasets.h5
    |- artist-correlation-datasets.h5
- logs/
    |- 01.load-source-data.py.log
    |- 02.tag-correlation.py.log
    |- 03.artist-correlation.py.log
    |- 04.compare-similar.py.log
- docs/
    |- lastfm-top-tags-correlation-heatmap.png
    |- similar-artists-comparison.txt
    |- similar-tags-comparison.txt

Home directory contains the 4 main python scripts and small utility library.
For clarity, the task is divided into those separate four scripts.
One SQL script contains the necessary DDL statements to create the database and
tables, which is done inside the script #1. The execution of that script takes
about an hour, due the pace of the API. Scripts #2, #3 and #4 execute very
quickly, only the second one takes several minutes.
All python scripts have fair amount of comments related to the specific points,
as well as general comment of the specific step performed in the script.
One html template file is used in the #2 script to generate the final html file
with heatmap chart of the tags correlation.

"data" directory is the location where data is saved during the execution, one
SQLite3 database with final datasets, and two HDF5 files with the intermediate
datasets.

"logs" directory will have all execution logs. In the repo, there are samples
from development runs.

In the "docs" folder, there are sample output files from the previous
development runs. Two text files are the final output of the comparison between
the API provided "similar" tags/artists and our datasets. The analysis of those
output files can be found in the corresponding scripts. There is also a
screenshot of the tag correlation heatmap chart, which can be also viewed by
loading the "tag-correlation-heatmap.htm" in the home dir.
