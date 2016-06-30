# -*- coding: utf-8 -*-

import pandas as pd
import numpy as np
import os
import re

from ddf_utils.str import to_concept_id
from ddf_utils.index import create_index_file


# configuration of file path
source = '../source/kilm15.xlsx'
out_dir = '../../'


def extract_entities_country(data):
    country = data[['Country (code)', 'Country']].drop_duplicates().copy()
    country.columns = ['country', 'name']

    country['country'] = country['country'].map(to_concept_id)

    return country


# def extract_entities_age_group(data):
#     age = data[['Age group (code)', 'Age group']].drop_duplicates().copy()
#     age.columns = ['age_group', 'name']
#     age['name'] = 'Age ' + age['name']
#     age['age_group'] = age['age_group'].map(to_concept_id)

#     return age


# def extract_entities_sex(data):
#     sex = data[['Sex (code)', 'Sex']].drop_duplicates().copy()
#     sex.columns = ['sex', 'name']
#     sex['sex'] = sex['sex'].map(to_concept_id)

#     return sex


def _rename_concept(s):
    if '000' in s:
        s = s.replace('000', 'thousands')
    if '%' in s:
        s = s.replace('%', 'percentage')

    # remove (1), (1 + 2), (1 + 2 + 3) etc
    s = re.sub(r'\(\d\)', '', s, count=1)
    s = re.sub(r'\(\d* ?\+ ?\d*[\d +]+\)', '', s, count=1)

    return s


def extract_concepts(data):
    discs = ['Name', 'Year', 'Country']

    conc = data.columns[8:16]

    cdf = pd.DataFrame([], columns=['concept', 'name', 'concept_type'])

    cdf['name'] = [*discs, *conc]
    cdf['concept'] = cdf['name'].map(lambda x: to_concept_id(_rename_concept(x)))

    cdf.loc[3:, 'concept_type'] = 'measure'
    cdf.loc[0, 'concept_type'] = 'string'
    cdf.loc[1, 'concept_type'] = 'time'
    cdf.loc[2, 'concept_type'] = 'entity_domain'

    return cdf


def extract_datapoints(data):

    conc = data.columns[8:16]

    dps = data[['Country (code)', 'Year', *conc]].copy()
    dps.columns = ['country', 'year',
                   *[to_concept_id(_rename_concept(x)) for x in conc]]

    dps['country'] = dps['country'].map(to_concept_id)

    dps = dps.set_index(['country', 'year'])

    for k, df in dps.items():
        df_ = df.reset_index().dropna()

        yield k, df_


if __name__ == '__main__':
    print('reading source files...')
    data = pd.read_excel(source, skiprows=2, sheetname='KILM 15b')

    print('creating concept file...')
    cdf = extract_concepts(data)
    path = os.path.join(out_dir, 'ddf--concepts.csv')
    cdf.to_csv(path, index=False)

    print('creating entities files...')
    country = extract_entities_country(data)
    path = os.path.join(out_dir, 'ddf--entities--country.csv')
    country.to_csv(path, index=False)

    print('creating datapoints...')
    for k, df in extract_datapoints(data):
        path = os.path.join(out_dir,
                            'ddf--datapoints--{}--by--country--year.csv'.format(k))
        df.to_csv(path, index=False)

    print('creating index file...')
    create_index_file(out_dir)

    print('Done.')
