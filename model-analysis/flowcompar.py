# !/usr/bin/env python3
# -*- coding: utf-8 -*-
__author__ = 'Marcelo Ferreira da Costa Gomes'
import pandas as pd
import numpy as np
import argparse

"""
Compare flow obtained from Brazilian 2010 Census Microdata with Radiation and Gravitation models
"""

def readmunicipality(listfu):
    """
    Reads tables of municipalities and movement code.

    :param listfu: list of Federal Units of interest
    :return dfgeocode: Data frame with geocode, name, FU and population of each Municipality
    """

    dfgeocode = pd.read_csv('../data/Brazil-municipalities-2010.csv')
    dfgeocode.rename(columns={'CD_GEOCODM': 'geocode', 'NM_MUNICIP': 'name', 'SIGLA_ESTADO': 'fu', 'POPULATION': 'pop'},
                     inplace=True)
    dfgeocode = dfgeocode[dfgeocode.fu.isin(listfu)]

    return dfgeocode


def readdistance(srcgeocodes, tgtgeocodes):
    """
    Read table with data corresponding to the geodesic distance between every pair of nodes

    :param srcgeocodes: geocodes for requested Brazilian Municipalities source
    :param tgtgeocodes: geocodes for requested Brazilian Municipalities destinations
    :return dfdist: Data frame with geodesic distance between every pair (undirected)
    """

    dfdist = pd.read_csv('../data/Brazil-municipalities-2010-centroids-distance.csv')
    dfdist.rename(columns={'Source geocode': 'srcgeocode', 'Source name': 'srcname',
                           'Target geocode': 'tgtgeocode', 'Target name': 'tgtname',
                           'Distance(km)': 'distance'}, inplace=True)
    dfdist = dfdist[(dfdist.srcgeocode.isin(srcgeocodes)) & (dfdist.tgtgeocode.isin(tgtgeocodes))]

    return dfdist


def readflow(srcgeocodes, tgtgeocodes, fname=None):
    """
    Read flow data and return clean table

    :param srcgeocodes: geocodes for requested Brazilian Municipalities source
    :param tgtgeocodes: geocodes for requested Brazilian Municipalities destinations
    :param fname: path to flow file. Optional.
    :return:
    dfflow: data frame with requested flow
    """

    if fname is None:
        dfflow = pd.read_csv('../data/all_FUs-redistributed_mobility_matrix.csv')
    else:
        dfflow = pd.read_csv(fname)

    # Discard all unnecessary data:
    dfflow.rename(columns={'Origin Municipality': 'srcname', 'Origin geocode': 'srcgeocode',
                           'Destination Municipality': 'tgtname', 'Destination geocode': 'tgtgeocode',
                           'Population': 'srcpop', 'Total': 'flow', 'Std error': 'error'})
    dfflow = dfflow[(dfflow.srcgeocode.isin(srcgeocodes)) & (dfflow.tgtgeocode.isin(tgtgeocodes))]

    return dfflow


def gravmodel(dfin):
    """
    Estimate flow based on the Gravitational model, based on distance between nodes,
    resident and traveling population

    :param dfin: pd.DataFrame with source geocode (src), target geocode (tgt), source population (srcpop),
                 target population (tgtpop), total amount of traveling agents by source (Ti)

    :return dfgrav: pd.DataFrame with non-null flow for every pair of nodes
    """

    dfgrav = dfin.copy()
    # Create column with estimated flow
    dfgrav['grav'] = 0


    return dfgrav


def radmodel(dfin):
    """
    Estimate flow based on the Radiation model, based on distance between nodes,
    resident and traveling population.

    :param dfin: pd.DataFrame with source geocode (src), target geocode (tgt), source population (srcpop),
                 target population (tgtpop), total amount of traveling agents by source (Ti)

    :return dfgrav: pd.DataFrame with non-null flow for every pair of nodes
    """

    dfrad = dfin.copy()
    # Create column with estimated flow
    dfrad['rad'] = 0

    return dfrad


def main(srcfu, tgtfu, fname=None):

    # Grab geocode of source and target Municipalities:
    listfu = srcfu.copy()
    listfu.extend(tgtfu)
    dfgeocode = readmunicipality(listfu)
    srcgeocodes = list(dfgeocode.geocode[dfgeocode.fu.isin(srcfu)])
    tgtgeocodes = list(dfgeocode.geocode[dfgeocode.fu.isin(tgtfu)])

    # Read distance matrix:
    dfdist = readdistance(srcgeocodes, tgtgeocodes)

    # Read flow matrix:
    dfflow = readflow(srcgeocodes, tgtgeocodes, fname)

    # Obtain total number of agents traveling from each Municipality
    dftravel = dfflow[['srcgeocode','total']].groupby(['srcgeocode']).agg(np.sum)

    # Create temporary data frame with all necessary columns for flow estimates
    ## Create bi-directional distance matrix
    dftmp = pd.concat(dfdist, dfdist.rename(columns={'srcgeocode': 'tgtgeocode', 'tgtgeocode': 'srcgeocode'}))
    del(dfdist)
    ## Add column with source and target population
    dftmp = pd.merge(dftmp, dfflow, on=['srcgeocode', 'tgtgeocode'],
                      how='left')
    del(dfpop)
    ## Add total number of traveling agents by source:
    dftmp = pd.merge(dftmp, dftravel, on='srcgeocode', how='left').rename(columns={'total': 'Ti'})
    del(dftravel)
    ## Sort by origin-destination and reset index
    dftmp.sort(['srcgeocode', 'tgtgeocode']).reset_index().drop('index', axis=1)
    ## Print matrix
    dftmp.to_csv('../data/src_%s-tgt_%s-mobility_matrix.csv' % ('-'.join(srcfu), '-'.join(tgtfu)))
    ## Rename source and target geocode columns for simplicity
    dftmp.rename(columns={'srcgeocode': 'src', 'tgtgeocode': 'tgt'})

    # Calculate corresponding Gravitational model flow:
    dfgrav = gravmodel(dftmp)

    # Calculate corresponding Radiation model flow:
    dfrad = radmodel(dftmp)


if __name__ == '__main__':

    parser = argparse.ArgumentParser(description='Calculate Gravitational and Radiation Models flow estimate'+
                                     ' and compare to real flow given.\n'+
                                     'Assumes input file format as generated by model-analysis.py')
    parser.add_argument('srcfu', nargs='*', action='append')
    parser.add_argument('--srcfu', '-srcfu', nargs='*', action='append',
                        help='Two letter name of source FU of interest. Accept multiple entries',
                        default=['all'])
    parser.add_argument('--tgtfu', '-tgtfu', nargs='*', action='append',
                        help='Two letter name of destination FU of interest. Accept multiple entries',
                        default=args.srcfu)
    parser.add_argument('--path', nargs='1', help='Path to mobility matrix file',
                        default='../data/all_FUs-redistributed_mobility_matrix.csv')
    main(args.srcfu, args.tgtfu, args.path)