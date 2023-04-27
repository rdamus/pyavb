from __future__ import (
    unicode_literals,
    absolute_import,
    print_function,
    division,
)
import avb
import sys
import csv
from datetime import datetime

if bytes is not str:
    unicode = str


def pretty_value(value):
    if isinstance(value, bytearray):
        return "bytearray(%d)" % len(value)
        # return ''.join(format(x, '02x') for x in value)
    return value


def write_csv(fieldnames, data):
    print(f"fieldnames:{fieldnames}")
    fname = "{}{}{}".format('data-', datetime.now().strftime("%Y%m%dT%I%M%S"), '.csv')
    with open(fname, 'w') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        print(f"writer:{writer}")
        writer.writeheader()
        for row in data:
            writer.writerow(row)


def parse(mob):
    print(f"parse mob.name:{mob.name}")
    user_attr = mob.attributes.get('_USER')
    attr = user_attr.items()
    data = dict(attr)
    if not data:
        return None
    data['C_Start'] = mob.attributes.get('_START')
    data['C_End'] = mob.attributes.get('_END')
    data['C_Length'] = mob.length
    data['C_Edit_Rate'] = mob.edit_rate
    data['C_Name'] = mob.name
    data['C_Seconds'] = 0
    oktocalc = all(v is not None for v in [data['C_End'], data['C_Start'], data['C_Edit_Rate']])
    if oktocalc:
        data['C_Seconds'] = (data['C_End'] - data['C_Start']) / data['C_Edit_Rate']
    return data


def make_data(mob):
    fields = set()
    data = {}
    rows = []
    # iterate
    property_data = mob.property_data
    for k in property_data.keys():
        if k == 'attributes':
            # print(f"listing attributes:{k}")
            add_attr(rows, fields, mob, property_data.get(k))
        else:
            row = {'mob.name': mob.name,
                   'mob': mob,
                   'field': k,
                   'value': property_data.get(k)}
            fields |= set(row.keys())
            rows.append(row)

    data['fields'] = fields
    data['rows'] = rows
    return data


def add_binvals(rows, fields, mob, vals):
    d = dict(vals)
    # print(f"Bin Type:{type(vals)}")
    for akey in d.keys():
        row = {'mob.name': mob.name,
               'mob': mob,
               'field': akey,
               'value': d.get(akey)}
        # collect the rows
        fields |= set(row.keys())
        rows.append(row)


def add_attr(rows, fields, mob, attr):
    for key in attr.keys():
        row = {'mob.name': mob.name, 'mob': mob}
        # print(f"attr.key:{key}")
        vals = attr.get(key)
        # handle the Attributes and flatten into row
        if isinstance(vals, avb.attributes.Attributes) \
                or isinstance(vals, avb.trackgroups.TrackGroup)\
                or isinstance(vals, avb.essence.MediaDescriptor)\
                or isinstance(vals, avb.essence.MediaFileDescriptor):
            add_binvals(rows, fields, mob, vals)
        else:
            row = {'mob.name': mob.name,
                   'mob': mob,
                   'field': key,
                   'value': vals}
        # collect the rows
        fields |= set(row.keys())
        rows.append(row)

'''
Entry point.  
Set the comp_only to True to just walk the compositionmobs, which will produce the same number of lines as in the 
bins from the avb file
Set the comp_only to False to walk the entire avb.  Note this will generate large csv files
'''
def main(path):
    data = []
    comp_only = True
    fields = set()

    if comp_only:
        with avb.open(path) as f:
            for mob in f.content.compositionmobs():
                d = parse(mob)
                if d:
                    fields |= set(d.keys())
                    data.append(d)
        # print(fields)
        write_csv(sorted(fields), data)
    else:
        with avb.open(path) as f:
            for mob in f.content.mobs:
                d = make_data(mob)
                if d:
                    fields |= set(d['fields'])
                    for row in d['rows']:
                        data.append(row)
                    # print(f"data:{data}")
            # print(fields)
            # print(flatten(data))
            write_csv(sorted(fields), data)


def flatten(l):
    return [item for sublist in l for item in sublist]


# def main(path):
#     data = []
#     keys = set()
#     with avb.open(path) as f:
#         for mob in f.content.compositionmobs():
#             user_attr = mob.attributes.get('_USER')
#             start = mob.attributes.get('_START')
#             print(f"mob.name:{mob.name}")
#             attr = user_attr.items()
#             print("-------")
#             d = dict(attr)
#             if d:
#                 #add the name
#                 d['Name'] = mob.name
#                 keys |= set(d.keys())
#                 data.append(d)
#     print(keys)
#     write_csv(keys, data)

if __name__ == "__main__":
    main(sys.argv[1])
