# !/usr/bin/env python3
# -*- coding: utf-8 -*-
__author__ = 'Marcelo Ferreira da Costa Gomes'
import pandas as pd
import numpy as np
import argparse
from argparse import RawDescriptionHelpFormatter

"""
Compare flow obtained from Brazilian 2010 Census Microdata with Radiation and Gravitation models
Assume path of necessary files with distance and population to be
../data/Brazil-municipalities-2010.csv
../data/Brazil-municipalities-2010-centroids-distance.csv
"""


def readmunicipality(listfu):
    """
    Reads tables of municipalities code.

    :param listfu: list of Federal Units of interest
    :return dfgeocode: Data frame with geocode, name, FU and population of each Municipality
    """

    dfgeocode = pd.read_csv('../data/Brazil-municipalities-2010.csv')
    dfgeocode.rename(columns={'CD_GEOCODM': 'geocode', 'NM_MUNICIP': 'name', 'SIGLA_ESTADO': 'fu', 'POPULATION': 'pop'},
                     inplace=True)

    if 'all' not in listfu and 'ALL' not in listfu:
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

    # Create bi-directional distance matrix
    pd.concat([dfdist, dfdist.rename(columns={'srcgeocode': 'tgtgeocode', 'tgtgeocode': 'srcgeocode'})])

    # Keep requested pairs only
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
    dfflow.rename(columns={'Origin Municipality': 'srcname', 'Origin geocode': 'srcgeocode', 'Origin FU': 'srcfu',
                           'Destination Municipality': 'tgtname', 'Destination geocode': 'tgtgeocode',
                           'Destination FU': 'tgtfu', 'Population': 'srcpop', 'Total': 'flow', 'Std error': 'error'},
                  inplace=True)
    # Keep only Brazilian destinations
    dfflow = dfflow[dfflow['Destination Country'] == 'BRASIL']
    dfflow = dfflow[['srcname', 'srcgeocode', 'srcfu', 'tgtname', 'tgtgeocode', 'tgtfu', 'srcpop', 'flow', 'error']]
    dfflow.tgtgeocode = dfflow.tgtgeocode.astype(int)
    dfflow = dfflow[(dfflow.srcgeocode.isin(srcgeocodes)) & (dfflow.tgtgeocode.isin(tgtgeocodes))]

    return dfflow


def gravmodel(dfin, beta=1, gamma=2):
    """
    Estimate flow $F_{ij}$ based on the Gravitational model, based on distance between nodes,
    resident and traveling populations:
    $$ F_{ij} = A_i \frac{ m_{i}^{\alpha} m_{j}^{\beta} }{ r_{ij}^{\gamma} }.$$
    Uses normalizing factor $A_i$ as:
    $$ A_i = T_i * \sum_{j} \frac{ m_{i}^{\alpha} m_{j}^{\beta} }{ r_{ij}^{\gamma} },$$
    where $T_i$ is the total number of traveling agents from i.
    In this case, the power alpha becomes irrelevant, since it is incorporated by the normalizing factor.

    :param dfin: pd.DataFrame with (at least) source geocode (src), target geocode (tgt), source population (srcpop),
                 target population (tgtpop), total amount of traveling agents by source (Ti)
    :param beta: power of the target population for gravitational formula
    :param gamma: power of the distance for the gravitational model

    :return dfgrav: pd.DataFrame with non-null flow for every pair of nodes
    """

    dfgrav = dfin.copy()
    # Create column with estimated flow
    dfgrav['grav'] = dfgrav.tgtpop.pow(beta) / dfgrav.dist.pow(gamma)
    for src in dfgrav.src.unique():
        norm = np.float64(dfgrav.grav[dfgrav.src == src].sum())
        dfgrav.loc[dfgrav.src == src, 'grav'] *= dfgrav.Ti[dfgrav.src == src] / norm

    return dfgrav


def radmodel(dfin):
    """
    Estimate flow $F_{ij}$ based on the Radiation model, based on distance between nodes,
    resident and traveling populations:
    $$ F_{ij} = T_i \frac{ m_i m_j }{ (m_i + s_{ij})(m_i + m_j + s_{ij}) },$$
    where $T_i$ is the total number of traveling agents from i, and s_{ij} is the total
    population contained in a circle of radius r_{ij}, m_i and m_j aside.

    :param dfin: pd.DataFrame with (at least) source geocode (src), target geocode (tgt), source population (srcpop),
                 target population (tgtpop), total amount of traveling agents by source (Ti)

    :return dfgrav: pd.DataFrame with non-null flow for every pair of nodes
    """

    dfrad = dfin.copy()
    # Create column with estimated flow
    dfrad['rad'] = dfrad.Ti * dfrad.srcpop * dfrad.tgtpop
    for src in dfrad.src.unique():
        tgtlist = list(dfrad.tgt[dfrad.src == src])
        mi = np.float64(dfrad.srcpop[dfrad.src == src].unique())
        for tgt in tgtlist:
            rij = np.float64(dfrad.dist[(dfrad.src == src) & (dfrad.tgt == tgt)])
            sij = np.float64(dfrad.tgtpop[(dfrad.src == src) & (dfrad.dist < rij)].sum())
            if np.isnan(sij):
                sij = 0
            mj = np.float64(dfrad.tgtpop[dfrad.tgt == tgt].unique())
            norm = (mi + sij) * (mi + mj + sij)
            #print(rij,mi,mj,sij,norm)
            dfrad.loc[(dfrad.src == src) & (dfrad.tgt == tgt), 'rad'] *= np.float64(1) / norm

    return dfrad


def main(srcfu, tgtfu, fname=None):

    # Grab geocode of source and target Municipalities:
    listfu = srcfu.copy()
    listfu.extend(tgtfu)
    dfgeocode = readmunicipality(listfu)
    if srcfu[0].lower() == 'all':
        srcgeocodes = list(dfgeocode.geocode)
    else:
        srcgeocodes = list(dfgeocode.geocode[dfgeocode.fu.isin(srcfu)])
    if tgtfu[0].lower() == 'all':
        tgtgeocodes = list(dfgeocode.geocode)
    else:
        tgtgeocodes = list(dfgeocode.geocode[dfgeocode.fu.isin(tgtfu)])

    # Read distance matrix:
    print('Reading distance matrix')
    dfdist = readdistance(srcgeocodes, tgtgeocodes)

    # Read flow matrix:
    print('Reading flow matrix')
    dfflow = readflow(srcgeocodes, tgtgeocodes, fname)

    # Obtain total number of agents traveling from each Municipality
    dftravel = dfflow[['srcgeocode', 'flow']].groupby(['srcgeocode'], as_index=False).agg(np.sum).\
        rename(columns={'flow': 'Ti'})

    # Create temporary data frame with all necessary columns for flow estimates
    print('Starting merges')
    dftmp = dfdist.copy()
    del dfdist

    # Add column with data-based flow
    dftmp = pd.merge(dftmp, dfflow.drop(['srcpop', 'srcname', 'tgtname'], axis=1), on=['srcgeocode', 'tgtgeocode'],
                     how='left')

    # Add column for source population
    dftmp = pd.merge(dftmp, dfgeocode[['geocode', 'pop']].rename(columns={'geocode': 'srcgeocode', 'pop': 'srcpop'}),
                     on='srcgeocode', how='left')

    # Add column for target population
    dftmp = pd.merge(dftmp, dfgeocode[['geocode', 'pop']].rename(columns={'geocode': 'tgtgeocode', 'pop': 'tgtpop'}),
                     on='tgtgeocode', how='left')
    del dfflow

    # Update Origin and Destination corresponding FU and Country:
    for tgt in dftmp.tgtgeocode.unique():
        dftmp.loc[dftmp.tgtgeocode == tgt, 'tgtfu'] = dfgeocode.fu[dfgeocode.geocode == tgt].values
    for src in dftmp.srcgeocode.unique():
        dftmp.loc[dftmp.srcgeocode == src, 'srcfu'] = dfgeocode.fu[dfgeocode.geocode == src].values

    del dfgeocode

    # Add total number of traveling agents by source:
    dftmp = pd.merge(dftmp, dftravel, on='srcgeocode', how='left')
    del dftravel

    # Sort by origin-destination and reset index
    dftmp.sort(['srcgeocode', 'tgtgeocode']).reset_index().drop('index', axis=1)

    # Fill na with 0
    dftmp.fillna(0, inplace=True)

    # Print matrix with original data
    dftmp.to_csv('../data/src_%s-tgt_%s-extended-mobility_matrix.csv' % ('-'.join(srcfu), '-'.join(tgtfu)), index=False)

    # Rename source and target geocode columns for simplicity
    dftmp.rename(columns={'srcgeocode': 'src', 'tgtgeocode': 'tgt', 'distance': 'dist'}, inplace=True)

    # Calculate corresponding Gravitational model flow:
    print('Calculating gravitational model')
    dftmp = gravmodel(dftmp)

    # Calculate corresponding Radiation model flow:
    print('Calculating radiation model')
    dftmp = radmodel(dftmp)

    # Print matrix with original data plus model estimations
    dftmp.to_csv('../data/src_%s-tgt_%s-mobility_grav_rad_matrix-.csv' % ('-'.join(srcfu), '-'.join(tgtfu)),
                 index=False)
    exit()


if __name__ == '__main__':

    parser = argparse.ArgumentParser(description='Calculate Gravitational and Radiation Models flow estimate' +
                                     ' and compare to real flow given.\n' +
                                     "Assume input file format as generated by model-analysis.py\n" +
                                     "Assume path of necessary files with distance and population to be\n" +
                                     "../data/Brazil-municipalities-2010.csv\n" +
                                     "../data/Brazil-municipalities-2010-centroids-distance.csv",
                                     formatter_class=RawDescriptionHelpFormatter)
    parser.add_argument('--srcfu', '-srcfu', nargs='*', action='append',
                        help='Two letter name of source FU of interest. Accept multiple entries',
                        default=None)
    parser.add_argument('--tgtfu', '-tgtfu', nargs='*', action='append',
                        help='Two letter name of destination FU of interest. Accept multiple entries',
                        default=None)
    parser.add_argument('--path', help='Path to mobility matrix file',
                        default='../data/all_FUs-redistributed_mobility_matrix.csv')
    args = parser.parse_args()
    if args.srcfu is None:
        args.srcfu = [['all']]
    if args.tgtfu is None:
        args.tgtfu = args.srcfu

    print(args)
    main(args.srcfu[0], args.tgtfu[0], args.path)
