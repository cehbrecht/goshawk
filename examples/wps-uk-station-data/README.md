# What is all this?

Some code, example data and utilities to subset weather observation
records in CSV files.

## The data

...looks like:

```
$ ls data/ -1
nonsense-data_tempdrnl_201701-201712.txt
nonsense-data_tempdrnl_201801-201812.txt
nonsense-data_tempdrnl_201901-201912.txt
```

It has many lines of data, one record per row, no header:

```
$ head -2 data/nonsense-data_tempdrnl_201701-201712.txt
2017-01-01 09:00, CLBD, 4835, 12, 1, AWSDLY, 57254, 1011, 7.6, 1.9, , , 1, 1, , , 2017-01-01 09:46, 4, , , ,
2017-01-01 09:00, CLBD, 9885, 12, 1, AWSDLY, 61937, 1011, 7.7, 8.8, , , 1, 1, , , 2017-01-01 09:48, 2, , , ,
```

## The data-processing code

...is here:

```
$ ls -1 midas/
bbox_utils.py
getStations.py
__init__.py
midasSubsetter.py
rewrite-random.py
```

It reads the data files and processes them to generate output.


### Utility 1: getStations.py

`getStations.py` - finds weather stations based on user inputs:

```
Examples:
=========

    python getStations.py -c cornwall,devon,wiltshire
    python getStations.py  -x 0,3 -y 52,54
    python getStations.py  -x 0,3 -y 52,54 -n
    python getStations.py  -x 0,0.4 -y 52,52.2
    python getStations.py  -x 0.2,0.4 -y 52,52.2 -s 200301010000
    python getStations.py  -x 0.3,0.4 -y 52,52.2 -s 200301010000 -d rain
    python getStations.py  -x 0.3,0.4 -y 52.05,52.1 -s 199901010000 -e 200501010000 -d rain
    python getStations.py  -c DEVON -s 199901010000 -e 200501010000 -d rain
    python getStations.py  -c DEVON  -e 200501010000 -d rain


Example with output of station IDs: 

$ python midas/getStations.py -x 0.3,0.4 -y 52,52.2 -s 200301010000 -d rain

Searching within a box of (N - S) 52 - 52.2 and (W - E) 0.3 - 0.4...
Filtering on data types: ['rain']
From: 200301010000
Original list length: 14
Selected after SRCC filtering: 4
Number of stations found: 4

SRC IDs follow:
==================
5186
5187
4499
30128
```

### Utility 2: midasSubsetter.py

`midasSubsetter.py` - filters weather records and returns a subset.

```
Examples:
=========

  
  python midas/midasSubsetter.py -t TD -s 201701010000 -e 201701011000

  python midas/midasSubsetter.py -t TD -s 201701010000 -e 201701011000 outputfile.dat

  python midas/midasSubsetter.py -t TD -s 201701010000 -e 201701011000 -g testlist.txt outputfile.dat

  python midas/midasSubsetter.py -t TD -s 201701010000 -e 201701011000 -i 61737,926 -d tab


Example with output:

$ python midas/midasSubsetter.py -t TD -s 201701250000 -e 201702011000 -i 61737

NOTE: Multiple table search not yet implemented.
Got row headers...
Got partition files...
Getting file list...

Extracting all rows: TD
From files:     /vagrant-share/wps-uk-station-data/data/nonsense-data_tempdrnl_201701-201712.txt
Between: 201701250000 and 201702011000

/vagrant-share/wps-uk-station-data/.temporary
Now extracting station ids provided...

Filtering file '/vagrant-share/wps-uk-station-data/data/nonsense-data_tempdrnl_201701-201712.txt' containing 259924 /vagrant-share/wps-uk-station-data/data/nonsense-data_tempdrnl_201701-201712.txt lines.
Breaking out of read loop because time past end time!
Lines to filter =  16 /vagrant-share/wps-uk-station-data/.temporary/temp_20190324.124231

Data extracted to temporary file(s)...
Getting size of temporary output file.
Can sort and filter since file is small.
Output data follows:

ob_end_time, id_type, id, ob_hour_count, version_num, met_domain_name, src_id, rec_st_ind, max_air_temp, min_air_temp, min_grss_temp, min_conc_temp, max_air_temp_q, min_air_temp_q, min_grss_temp_q, min_conc_temp_q, meto_stmp_time, midas_stmp_etime, max_air_temp_j, min_air_temp_j, min_grss_temp_j, min_conc_temp_j
2017-01-25 09:00, DCNN, 0579, 12, 1, NCM, 61737, 1011, 5.8, 8.3, , , 1, 1, , , 2017-01-25 08:54, 0, , , ,
2017-01-25 21:00, DCNN, 4714, 12, 1, NCM, 61737, 1011, 10.1, 18.1, , , 1, 1, , , 2017-01-25 20:56, 0, , , ,
2017-01-26 09:00, DCNN, 9551, 12, 1, NCM, 61737, 1011, 17.7, 15.8, , , 1, 1, , , 2017-01-26 08:54, 0, , , ,
2017-01-26 21:00, DCNN, 7418, 12, 1, NCM, 61737, 1011, 12.6, 9.9, , , 1, 1, , , 2017-01-26 20:56, 0, , , ,
2017-01-27 09:00, DCNN, 7098, 12, 1, NCM, 61737, 1011, 13, 16.3, , , 1, 1, , , 2017-01-27 08:54, 0, , , ,
2017-01-27 21:00, DCNN, 2337, 12, 1, NCM, 61737, 1011, 14.1, 6, , , 1, 1, , , 2017-01-27 21:52, 0, , , ,
2017-01-28 09:00, DCNN, 0423, 12, 0, NCM, 61737, 1012, 11.8, 12.6, , , 151, 1, , , 2017-01-28 08:55, 0, , , ,
2017-01-28 09:00, DCNN, 1012, 12, 1, NCM, 61737, 1011, 10.1, 16.5, , , 1501, 1, , , 2017-01-28 08:55, 0, , , ,
2017-01-28 21:00, DCNN, 7114, 12, 1, NCM, 61737, 1011, 9, 3.3, , , 1, 1, , , 2017-01-29 00:12, 0, , , ,
2017-01-29 09:00, DCNN, 9054, 12, 1, NCM, 61737, 1011, 8.4, 3.1, , , 1, 1, , , 2017-01-29 08:54, 0, , , ,
2017-01-29 21:00, DCNN, 5425, 12, 1, NCM, 61737, 1011, 2.6, 6, , , 1, 1, , , 2017-01-29 20:54, 0, , , ,
2017-01-30 09:00, DCNN, 1633, 12, 1, NCM, 61737, 1011, 11.7, 2.1, , , 1, 1, , , 2017-01-30 09:40, 10, , , ,
2017-01-30 21:00, DCNN, 1303, 12, 1, NCM, 61737, 1011, 10.6, 13.4, , , 1, 1, , , 2017-01-30 20:54, 0, , , ,
2017-01-31 09:00, DCNN, 2359, 12, 1, NCM, 61737, 1011, 16.6, 19.3, , , 1, 1, , , 2017-01-31 10:36, 0, , , ,
2017-01-31 21:00, DCNN, 8927, 12, 1, NCM, 61737, 1011, 12.3, 6.7, , , 1, 1, , , 2017-01-31 23:42, 0, , , ,
2017-02-01 09:00, DCNN, 0585, 12, 1, NCM, 61737, 1011, 9.2, 2.2, , , 1, 1, , , 2017-02-01 08:54, 0, , , ,

```

## The WPS code

There are two COWS WPS processes, they are defined in:

```
$ ls -1 wps/*
wps/ExtractUKStationData:
ExtractUKStationData.ini
ExtractUKStationData.py
__init__.py
lib.py

wps/GetWeatherStations:
GetWeatherStations.ini
GetWeatherStations.py
__init__.py
lib.py

```

The `ini` files define the process inputs and name.

The `.py` files represent the code that interacts with the COWS WPS and
then calls the processing code under: `midas/`

## Our objective

Our objective is to rewrite the two processes as a Birdhouse WPS. :-) 

