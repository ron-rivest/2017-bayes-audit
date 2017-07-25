# csv_readers.py
# Ronald L. Rivest and Karim Husayn Karimi
# July 7, 2017
# python3

"""
Code to read the various files that multi.py uses from their CSV
formats, and put the results into the Election data structure.
"""

"""
All CSV files have a single header line, giving the column (field) names.
For most file formats, a data row must have length no longer than the header row,
and missing values are represented as "".
For "varlen" files (files with variable row lengths), it is a little bit 
different: the last header may correspond to 0, 1, 2, or more valuesin a data row.
So the data row may be shorter (by one), equal to, or longer than the header row.
In any case, the values for the last field are *always* compiled into a tuple
(possibly an empty tuple).
The reader returns a list of dictionaries, one per row.
Example (regular csv file):
    A,B,C
    1,2,3
    4,5
becomes:
    [ {'A':'1', 'B':'2', 'C':'3'},
      {'A':'4', 'B':'5', 'C':''} 
    ]
Example: (varlen csv file)
    A,B,C
    1,2,3
    4,5
    6,7,8,9
becomes:
    [ {'A':'1', 'B':'2', 'C':('3',)},
      {'A':'4', 'B':'5', 'C':()},
      {'A':'6', 'B':'5', 'C':(8,9)},
    ]
"""

import csv

import ids
import utils


def read_csv_file(filename, varlen=False):

    filename = utils.filename_safe(filename)
    print(filename)
    with open(filename) as file:
        reader = csv.DictReader(file)
        rows = [row for row in reader]
        # take care of case last fieldname is followed by a comma
        while len(reader.fieldnames)>0 and ids.clean_id(reader.fieldnames[-1])=='':
            reader.fieldnames.pop()
            for row in rows:
                row[None] = [row['']]+row.get(None,[])
        for row in rows:
            if None in row and not varlen:
                # raise Exception("Too many values in row:"+str(row))
                utils.mywarning("Too many values in row:"+str(row))
                del row[None]
            for fieldname in reader.fieldnames:
                clean_fieldname = ids.clean_id(fieldname)
                if clean_fieldname != fieldname:
                    if clean_fieldname in row:
                        utils.mywarning("field name given twice:", clean_fieldname)
                    row[clean_fieldname] = row[fieldname]
                    del row[fieldname]
                    fieldname = clean_fieldname
                if row[fieldname] == None:
                    row[fieldname] = ""
                if isinstance(row[fieldname], str):
                    row[fieldname] = ids.clean_id(row[fieldname])
            if varlen:
                lastfieldname = ids.clean_id(reader.fieldnames[-1])
                if row[lastfieldname] == None:
                    value = ()
                elif None not in row:
                    value = (row[lastfieldname],)
                else:
                    while len(row[None])>0 and ids.clean_id(row[None][-1])=='':
                        row[None].pop()
                    value = [row[lastfieldname]] + [ids.clean_id(id) for id in row[None]]
                    value = tuple(value)
                    # Note: the previous line does *not* sort the ids into
                    # order.  This will be needed if these ids represent selids in a
                    # vote, but the order may be important for other uses.
                    del row[None]
                if value == ("",):
                    value = ()
                row[lastfieldname] = value
        return rows


if __name__=="__main__":

    filename = "test_data/csv_readers_test_reg.csv"
    print("Regular csv file:", filename)
    for row in read_csv_file(filename):
        print([(fn, row[fn]) for fn in sorted(row)])

    filename = "test_data/csv_readers_test_varlen.csv"
    print("Varlen csv file:", filename)
    for row in read_csv_file(filename, varlen=True):
        print([(fn, row[fn]) for fn in sorted(row)])
    
