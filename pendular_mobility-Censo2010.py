#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Script for extraction of mobility matrix from Brazilian
2010 Census microdata

Necessary files:
./data/migration_and_movement_municipalities-2010.csv
./data/migration_and_movement_federation_units-2010.csv
./data/migration_and_movement_foreign_countries-2010.csv
./data/Layout_microdados_Amosra-pessoa.csv
./data/Brazil-municipalities-2010.csv
./data/Fractions.csv

Usage:
python mobilidade_pendular-Censo2010.py <path to microdata file>

Input:
Path to file with microdata related to people.

Ex.:
python pendular_mobility-Censo2010.py data/Amostra_Pessoas_33.txt

Output:
./data/tab3605-microdata.csv  - SIDRA-like table
./data/tab3599-microdata.csv  - SIDRA-like table
./data/mobility-matrix-microdata.csv  - Mobility matrix

Code developed by:
Marcelo F C Gomes
marfcg <at> gmail <dot> com
"""

from collections import defaultdict
import numpy as np
import sys
import csv
import zipfile

def read_dictionary(var):
    """
    Read variables position dictionary
    :param fname:
    :param var:
    :return:
    """

    fin = open('data/Layout_microdados_Amostra-pessoa.csv', 'r')
    fin.next()
    frows = csv.DictReader(fin, delimiter=',')

    marker = {key: {} for key in var}
    for row in frows:
        if row['VAR'] in var:
            # Positions reduced by 1, for python compatibility
            pi = int(row['POSIÇÃO INICIAL']) - 1
            sint = slice(pi, pi + int(row['INT']))
            if row['DEC'] == '':
                sdec = ''
            else:
                pf = int(row['POSIÇÃO FINAL'])
                sdec = slice(pf - int(row['DEC']), pf)

            marker[row['VAR']] = {'NAME': row['NOME'],
                                     'SLICE': sint,
                                     'SLICEDEC': sdec}

    fin.close()
    return marker


##########################################################

def read_municipality():
    """
    Reads tables of municipalities and movement code
    :return:
    """

    fin = open('data/migration_and_movement_municipalities-2010.csv', 'r')
    fin.next()
    fin.next()

    frows = csv.DictReader(fin, delimiter=',')

    codmun = {}
    for row in frows:
        if not row['Código']: continue  # Ignore uninformative rows
        codmun[row['Código']] = row['Municípios']

    fin.close()

    fin = open('data/Brazil-municipalities-2010.csv', 'r')

    frows = csv.DictReader(fin, delimiter=',')

    geocodm = {}
    for row in frows:
        if not any(row.values()): continue  # Ignore empty rows
        geocodm[row['CD_GEOCODM']] = {'Municipality': row['NM_MUNICIP'],
                                      'FU': row['SIGLA_ESTADO'], 
                                      'Pop': int(row['POPULATION'])}

    fin.close()

    fin = open('data/Fractions.csv', 'r')

    frows = csv.DictReader(fin, delimiter=',')

    for row in frows:
        if row['Código'] in geocodm:
            geocodm[row['Código']]['Fraction'] = .01*float(row['Fração_efetiva'])

    fin.close()

    return codmun, geocodm


##########################################################

def read_cntry():
    """
    Reads table of countries movement code
    :return:
    """
    fin = open('data/migration_and_movement_foreign_countries-2010.csv')
    fin.next()
    fin.next()

    frows = csv.DictReader(fin, delimiter=',')

    codcntry = {}
    for row in frows:
        codcntry[row['CÓDIGOS']] = {'Country': row['PAÍSES ESTRANGEIROS'],
                                   'Continent': row['CONTINENTES']}

    fin.close()
    return codcntry


##########################################################

def read_fu():
    """
    Reads FU movement code
    :return:
    """

    fin = open('data/migration_and_movement_federation_units-2010.csv')
    fin.next()
    fin.next()

    frows = csv.DictReader(fin, delimiter=',')

    codfu = {}
    for row in frows:
        codfu[row['CÓDIGOS']] = row['UNIDADES DA FEDERAÇÃO']

    fin.close()
    return codfu


##########################################################

def write_tables(tab3599, tab3605, origdest, geocodm, codmun, codfu,
                     codcntry, pref):
    """
    Write relevant output tables:

    - Table tab3605: people with 10yo or more by ocupation, location of workplace,
    school attendance, location of school
    - Table tab3599: people with less than 10yo by school attendance e location of
    school
    - Movement matrix

    :param tab3599:  dict with data on mobility for education, for people 
                     below 10yo
    :param tab3605:  dict with data on mobility for education and work,
                     for people with 10yo or more
    :param origdest:  dict with aggregated mobility flow by city
    :param geocodm:  dict with codes for every municipality
    :param codmun:  dict with mobility code for municipalities
    :param codfu:  dict with mobility code for states
    :param codcntry:  dict with mobility code for countries
    :param pref:  preffix for output files
    :return:
    """

    # Write tab3605:
    fout = open('data/%s-tab3605-microdata.csv' % (pref), 'w')
    convtable = {'total':'Total',
                 'age':'Age',
                 'freq':'School attendance',
                 'munres':'School at same municipality',
                 'othermun':'School at another municipality',
                 'othercntry':'School at another country',
                 'nofreq':'Not attending school'}
    fieldnames = ['Municipality',
                  'Employment status',
                  'Total',
                  'School attendance',
                  'School at same municipality',
                  'School at another municipality',
                  'School at another country',
                  'Not attending school']
    workstat = ['Total',
                'Worker',
                'Work at same municipality',
                'Work at other municipality',
                'Work at other country',
                'Work at several municipalities',
                'Non-worker']
    csvwriter = csv.DictWriter(fout, delimiter=',', fieldnames=fieldnames)
    csvwriter.writeheader()
    d = {fn: '' for fn in fieldnames}

    for mun in sorted(tab3605.keys()):
        d['Municipality'] = geocodm[mun]['Municipality']
        for trabfn in workstat:
            d['Employment status'] = trabfn
            d.update((convtable[k], int(round(v)))
                     for k, v in tab3605[mun][trabfn].items())
            csvwriter.writerow(d)
    fout.close()

    # Write tab3599:
    fout = open('data/%s-tab3599-microdata.csv' % (pref), 'w')
    fieldnames = ['Municipality',
                  'Age',
                  'Total',
                  'School attendance',
                  'School at same municipality',
                  'School at another municipality',
                  'School at another country',
                  'Not attending school']
    csvwriter = csv.DictWriter(fout, delimiter=',', fieldnames=fieldnames)
    csvwriter.writeheader()
    d = {fn: '' for fn in fieldnames}

    for mun in sorted(tab3599.keys()):
        d['Municipality'] = geocodm[mun]['Municipality']
        for idade in sorted(tab3599[mun].keys()):
            d['Age'] = idade
            d.update((convtable[k], int(round(v)))
                     for k, v in tab3599[mun][idade].items())
            csvwriter.writerow(d)
    fout.close()

    # Write origin-destinatio matrix
    fout = open('data/%s-mobility-matrix-microdata.csv' % (pref), 'w')
    fieldnames = ['Origin',
                  'Destination Country',
                  'Destination FU',
                  'Destination Municipality',
                  'Total',
                  'Std error']
    csvwriter = csv.DictWriter(fout, delimiter=',', fieldnames=fieldnames)
    csvwriter.writeheader()
    d = {fn: '' for fn in fieldnames}
    for mun in sorted(origdest.keys()):
        d['Origin'] = geocodm[mun]['Municipality']

        for dest, peso in sorted(origdest[mun].items()):
            dest_cntry = dest[0:7]
            dest_fu = dest[7:14]
            dest_mun = dest[14:21]

            if dest_cntry not in codcntry:
                d['Destination Country'] = 'NA'
            else:
                d['Destination Country'] = codcntry[dest_cntry]['Country']
            if dest_fu not in codfu:
                d['Destination FU'] = 'NA'
            else:
                d['Destination FU'] = codfu[dest_fu]
                
            # codmun table from IBGE does not have all municipalities
            # but have special descriptors for missing data
            # If the code does represent a municipality, it matches
            # the entry in geocodm.
            if dest_mun not in geocodm:
                if dest_mun in codmun: 
                    d['Destination Municipality'] = codmun[dest_mun]
                else:
                    d['Destination Municipality'] = 'NA'
            else:
                d['Destination Municipality'] = geocodm[dest_mun]['Municipality']
                d['Destination Country'] = 'Brasil'

            d['Total'] = int(round(peso))

            frac = geocodm[mun]['Fraction']
            pop = geocodm[mun]['Pop']
            d['Std error'] = int(round(np.sqrt((1-frac) * peso * (pop-peso) / 
                                              (pop*frac-1))))

            csvwriter.writerow(d)
    fout.close()

    return


def main(fdata):
    """
    Read microdata file and extracts mobility data.

    Input:
    :param fdata:  # Path to microdata file related to people
                   # Amostra_Pessoas_<#FU>.txt
    :return:
    """
    varlist = {'V0001': 'res.fu',  # FU code
               'V0002': 'res.mun',  # Municipality code
               'V0010': 'weight',  # Sample weight
               'V6036': 'age',  # Age, in years
               'V0628': 'school',  # Attends school
               'V0636': 'school.loc',  # School's location
               'V6362': 'school.fu',  # School's FU
               'V6364': 'school.mun',  # School's Municipality
               'V6366': 'school.cntry',  # School's Country
               'V0660': 'work.loc',  # Work's location
               'V6602': 'work.fu',  # Work's FU
               'V6604': 'work.mun',  # Work's Municipality
               'V6606': 'work.cntry',  # Work's Country
               'V0661': 'work.daily',  # Daily return from work
               'V0662': 'work.desloc',  # Usual time in traffic to work
               'V6920': 'work.occ'  # Employment status
               }

    # Reads positional information regarding target variables:
    marker = read_dictionary(varlist.keys())

    # Simplify key's name:
    for key, value in varlist.iteritems():
        marker[value] = marker.pop(key)

    # Reads dictionaries for location codes:
    codmun, geocodm = read_municipality()
    codfu = read_fu()
    codcntry = read_cntry()

    # Prepare target dictionaries:
    pop_mun = {}
    origdest = {}
    tab3605 = {}
    tab3599 = {}

    if fdata.split('.')[-1] == 'zip':
        pref = fdata.split('/')[-1].split('.')[0]
    else:
        pref = fdata.split('/')[-1].split('.')[0].split('Amostra_Pessoas_')[-1]

    for cod in geocodm:
        if geocodm[cod]['FU'] != pref[0:2] and cod[0:2] != pref:
            continue
            
        pop_mun[cod] = {'total': 0,
                        'fixed': 0,
                        'mobile': 0}

        origdest[cod] = defaultdict(int)

        tab3605[cod] = {'Total': {},
                        'Worker': {},
                        'Work at same municipality': {},
                        'Work at other municipality': {},
                        'Work at other country': {},
                        'Work at several municipalities': {},
                        'Non-worker': {}}

        for key in tab3605[cod]:
            tab3605[cod][key] = {'total': 0,
                                 'freq': 0,
                                 'munres': 0,
                                 'othermun': 0,
                                 'othercntry': 0,
                                 'nofreq': 0}

        tab3599[cod] = {'Total': {},
                        '0-4': {},
                        '5-9': {}}

        for key in tab3599[cod]:
            tab3599[cod][key] = {'total': 0,
                                 'freq': 0,
                                 'munres': 0,
                                 'othermun': 0,
                                 'othercntry': 0,
                                 'nofreq': 0}

    tagschool = {'1': 'munres',
                 '2': 'othermun',
                 '3': 'othercntry'}
    tagwork = {'1': 'Work at same municipality',
               '2': 'Work at same municipality',
               '3': 'Work at other municipality',
               '4': 'Work at other country',
               '5': 'Work at several municipalities'}

    
    # Check wether the input is a zip file.
    # If so, assumes that it is the regular state microdata from IBGE
    # and crawls to the necessary file inside it
    
    if fdata.split('.')[-1] == "zip":
        fzip = zipfile.ZipFile(fdata, 'r')
        for fname in fzip.namelist():
            if pref+"/Pessoas/Amostra_Pessoas_" in fname:
                fin = fzip.open(fname)
                break
    else:
        fin = open(fdata, 'r')

    for line in fin:

        freqschool = False
        school_res = True
        school_fu = ''
        school_mun = ''
        school_cntry = ''

        freqwork = False
        work_res = True
        work_fu = ''
        work_mun = ''
        work_cntry = ''

        # Age (in years):
        age = int(line[marker['age']['SLICE']])

        # Municipality of residence's code:
        mun = (line[marker['res.fu']['SLICE']] +
               line[marker['res.mun']['SLICE']])

        # Individual weight:
        peso = np.double(line[marker['weight']['SLICE']] +
                         '.' +
                         line[marker['weight']['SLICEDEC']])

        # Add to municipality population:
        pop_mun[mun]['total'] += peso

        if age < 5:
            tab3599[mun]['Total']['total'] += peso
            tab3599[mun]['0-4']['total'] += peso
            underage = True
            agelabel = '0-4'
        elif age < 10:
            tab3599[mun]['Total']['total'] += peso
            tab3599[mun]['5-9']['total'] += peso
            underage = True
            agelabel = '5-9'
        else:
            tab3605[mun]['Total']['total'] += peso
            underage = False

        # Check school attendance:
        if int(line[marker['school']['SLICE']]) < 3:
            freqschool = True

        school = line[marker['school.loc']['SLICE']].strip()
        if school != '':  # If not attending school, this variable is blank
            schoollabel = tagschool[school]
            school = int(school)

            if school >= 2:  # Outside municipality of residence
                school_res = False
                school_fu = line[marker['school.fu']['SLICE']]
                school_mun = line[marker['school.mun']['SLICE']]
                school_cntry = line[marker['school.cntry']['SLICE']]
                school_dest = school_cntry + school_fu + school_mun

        # Check if worker:
        if line[marker['work.occ']['SLICE']] == '1':
            freqwork = True

        work = line[marker['work.loc']['SLICE']].strip()

        if work != '':
            worklabel = tagwork[work]
            work = int(work)

            if work > 2:  # Outside municipality of residence
                work_res = False
                work_fu = line[marker['work.fu']['SLICE']]
                work_mun = line[marker['work.mun']['SLICE']]
                work_cntry = line[marker['work.cntry']['SLICE']]
                work_dest = work_cntry + work_fu + work_mun

        # Update table values:

        # Destination:
        if work_res and school_res:
            pop_mun[mun]['fixed'] += peso
        else:
            pop_mun[mun]['mobile'] += peso

            if not work_res:
                origdest[mun][work_dest] += peso
            else:
                origdest[mun][school_dest] += peso

        # Mobility for work/study:
        if underage:
            if freqschool:
                tab3599[mun]['Total']['freq'] += peso
                tab3599[mun][agelabel]['freq'] += peso
                tab3599[mun]['Total'][schoollabel] += peso
                tab3599[mun][agelabel][schoollabel] += peso
            else:
                tab3599[mun]['Total']['nofreq'] += peso
                tab3599[mun][agelabel]['nofreq'] += peso
        else:
            if freqschool:
                tab3605[mun]['Total']['freq'] += peso
            else:
                tab3605[mun]['Total']['nofreq'] += peso

            if freqwork:
                tab3605[mun]['Worker']['total'] += peso
                tab3605[mun][worklabel]['total'] += peso
                if freqschool:
                    tab3605[mun]['Total'][schoollabel] += peso
                    tab3605[mun]['Worker']['freq'] += peso
                    tab3605[mun]['Worker'][schoollabel] += peso
                    tab3605[mun][worklabel]['freq'] += peso
                    tab3605[mun][worklabel][schoollabel] += peso
                else:
                    tab3605[mun]['Worker']['nofreq'] += peso
                    tab3605[mun][worklabel]['nofreq'] += peso
            else:
                tab3605[mun]['Non-worker']['total'] += peso
                if freqschool:
                    tab3605[mun]['Total'][schoollabel] += peso
                    tab3605[mun]['Non-worker']['freq'] += peso
                    tab3605[mun]['Non-worker'][schoollabel] += peso
                else:
                    tab3605[mun]['Non-worker']['nofreq'] += peso

    write_tables(tab3599, tab3605, origdest, geocodm, codmun, codfu,
                     codcntry, pref)


if __name__ == '__main__':
    main(sys.argv[1])
