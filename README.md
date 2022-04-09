# gadwall - Command Line Client to duckdb

[gadwall](https://en.wikipedia.org/wiki/Gadwall) is a pure Python based command line to [duckdb](https://duckdb.org/).

It is forked from [gadwall](https://github.com/tebeka/gadwall/tree/d5b0e30c52ee5a844aa553976bbec53272bb7ab6), which is available on [PyPi](https://pypi.org/project/gadwall/) - this project is *not* listed there.

This fork is mainly amended in three ways:
* the output is somewhat tabular
* it can dump its results to an HTML file
* "special" commands, which are not immedialtely passed to duckdb, are prefixed "."

| gadwall can: | gadwall can not: |
|--|--|
| connect to an existing, file based duckdb database | use an in-memory-database |
| run queries against that database                  | be installed from PyPi / using pip |
| create an HTML output of the query results         | create a database |
| | deal with every datatype supported by duckdb (try explicitely casting the results to varchar if you have issues; this is basically no limitation of gadwall but of the Python API of duckdb) |
| | deal with every error from duckdb |
| | run scripts |

![](https://upload.wikimedia.org/wikipedia/commons/thumb/1/1a/Gadwall_%28Anas_strepera%29_female_and_male_dabbling.jpg/640px-Gadwall_%28Anas_strepera%29_female_and_male_dabbling.jpg)

image from [wikimedia](https://en.wikipedia.org/wiki/Gadwall#/media/File:Gadwall_(Anas_strepera)_female_and_male_dabbling.jpg)

## Example Usage

```
C:\temp>python gadwall.py sample.db
Welcome to the gadwall, a duckdb shell. Type help or ? to list commands.

duckdb> .html duckdb.html
writing following commands to: "duckdb.html"
duckdb> .db
database: sample.db
duckdb> .schema
+--------+
|name    |
+--------+
|weekdays|
+--------+
duckdb> .schema weekdays
+---+--------+-------+-------+----------+-----+
|cid|name    |type   |notnull|dflt_value|pk   |
+---+--------+-------+-------+----------+-----+
|  0|no      |INTEGER|False  |(NULL)    |False|
|  1|language|VARCHAR|False  |(NULL)    |False|
|  2|label   |VARCHAR|False  |(NULL)    |False|
+---+--------+-------+-------+----------+-----+
duckdb> select * from weekdays
+--+--------+----------+
|no|language|label     |
+--+--------+----------+
| 0|en      |Monday    |
| 1|en      |Tuesday   |
| 2|en      |Wednesday |
| 3|en      |Thursday  |
| 4|en      |Friday    |
| 5|en      |Saturday  |
| 6|en      |Sunday    |
| 0|de      |Montag    |
| 1|de      |Dienstag  |
| 2|de      |Mittwoch  |
| 3|de      |Donnerstag|
| 4|de      |Freitag   |
| 5|de      |Samstag   |
| 6|de      |Sonntag   |
+--+--------+----------+
duckdb> .html off
html file "duckdb.html" closed
duckdb> quit
```
