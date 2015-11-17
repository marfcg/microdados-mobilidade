# !/usr/bin/env python3
# -*- coding: utf-8 -*-
__author__ = 'Marcelo Ferreira da Costa Gomes'
import pandas as pd
import numpy as np

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


def readflow(srcgeocodes, tgtgeocodes):
    """
    Read flow data and return clean table

    :param srcgeocodes: geocodes for requested Brazilian Municipalities source
    :param tgtgeocodes: geocodes for requested Brazilian Municipalities destinations
    :return:
    dfflow: data frame with requested flow
    """

    dfflow = pd.read_csv('../data/redistributed_mobility_matrix.csv')

    # Discard all unnecessary data:
    dfflow.rename(columns={'Origin Municipality': 'srcname', 'Origin geocode': 'srcgeocode',
                           'Destination Municipality': 'tgtname', 'Destination geocode': 'tgtgeocode',
                           'Population': 'pop', 'Total': 'total', 'Std error': 'error'})
    dfflow = dfflow[(dfflow.srcgeocode.isin(srcgeocodes)) & (dfflow.tgtgeocode.isin(tgtgeocodes))]

    return dfflow

def main(srcfu, tgtfu):

    # Grab geocode of source and target Municipalities:
    listfu = srcfu.copy()
    listfu.extend(tgtfu)
    dfgeocode = readmunicipality(listfu)
    srcgeocodes = list(dfgeocode.geocode[dfgeocode.fu.isin(srcfu)])
    tgtgeocodes = list(dfgeocode.geocode[dfgeocode.fu.isin(tgtfu)])

    # Read distance matrix:
    dfdist = readdistance(srcgeocodes, tgtgeocodes)

    # Read flow matrix:
    dfflow = readflow(srcgeocodes, tgtgeocodes)

    # Obtain total number of agents traveling from each Municipality
    dftravel = dfflow[['srcgeocode','total']].groupby(['srcgeocode']).agg(np.sum)

    # Calculate corresponding Gravitational model flow:
    dfgrav = gravmodel(dfgeocode[['geocode', 'pop']], dfdist[['srcgeocode', 'tgtgeocode', 'distance']], dftravel)

    # Calculate corresponding Radiation model flow:
    dfrad = radmodel(dfgeocode[['geocode', 'pop']], dfdist[['srcgeocode', 'tgtgeocode', 'distance']], dftravel)

