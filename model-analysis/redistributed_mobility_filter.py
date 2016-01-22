__author__ = 'Marcelo Ferreira da Costa Gomes'
from argparse import RawDescriptionHelpFormatter
import pandas as pd
import numpy as np
import sys
import argparse


def readfile(fname='data/all_FUs-redistributed_mobility_matrix.csv', colsrc='Origin FU', valsrc=None,
             coltgt='Destination FU', valtgt=None, sep=','):
    """
    Reads input file located in path fname using sep as separator.
    Applies filters provided, if any.

    :param fname: Path to input data
    :param colsrc: Source column to be used
    :param valsrc: Value in source column to be used
    :param coltgt: Target column to be used
    :param valtgt: Value in target column to be used
    :param sep: Column separator in input file
    :return:
    :rtype : pd.DataFrame
    """

    print(fname, colsrc, valsrc, coltgt, valtgt, sep)
    df = pd.read_csv(fname, sep=sep)

    if valsrc is None:
        if valtgt is not None:
            if type(valtgt) is str:
                valtgt = [valtgt]
            elif type(valtgt) is not list:
                exit('Bad type for argument valtgt in function readfile')

            df = df[df[coltgt].isin(valtgt)].copy()
    else:
        if type(valsrc) is str:
            valsrc = [valsrc]
        elif type(valsrc) is not list:
            exit('Bad type for argument valtgt in function readfile')

        if valtgt is not None:
            if type(valtgt) is str:
                valtgt = [valtgt]
            elif type(valtgt) is not list:
                exit('Bad type for argument valtgt in function readfile')

            df = df[(df[colsrc].isin(valsrc)) | (df[coltgt].isin(valtgt))].copy()
        else:
            df = df[df[colsrc].isin(valsrc)].copy()

    return df


def inoutotal(df=pd.DataFrame(), colsrc='Origin FU', valsrc=None, coltgt='Destination FU', valtgt=None):
    """
    Calculate aggregate in(out)flow to(from) valsrc in colsrc 

    :param df: Pandas Data Frame containing in/out flow
    :param colsrc: Column to use as filter
    :param valsrc: Value in column to filter by
    
    :return:
    ttinoutflow
    :rtype : pd.DataFrame
    """

    # Outflow
    if valsrc is not None:
        if type(valsrc) is str:
            valsrc = [valsrc]

        grpbyout = df.loc[df[colsrc].isin(valsrc), ['Origin FU', 'Origin Municipality', 'Origin geocode', 'Total']]. \
            groupby(['Origin FU', 'Origin Municipality', 'Origin geocode'], as_index=False).agg(np.sum)
    else:
        grpbyout = df[['Origin FU', 'Origin Municipality', 'Origin geocode', 'Total']].groupby(['Origin FU',
                                                                                                'Origin Municipality',
                                                                                                'Origin geocode'],
                                                                                               as_index=False). \
            agg(np.sum)

    # Inflow
    if valtgt is not None:
        if type(valtgt) is str:
            valtgt = [valtgt]
        grpbyin = df.loc[df[coltgt].isin(valtgt), ['Destination FU', 'Destination Municipality', 'Destination geocode',
                                                   'Total']].groupby(['Destination FU', 'Destination Municipality',
                                                                      'Destination geocode'], as_index=False).agg(np.sum)
    else:
        grpbyin = df[['Destination FU', 'Destination Municipality', 'Destination geocode', 'Total']]. \
            groupby(['Destination FU', 'Destination Municipality', 'Destination geocode'], as_index=False).agg(np.sum)

    grpbyin.rename(columns={'Destination FU': 'FU', 'Destination Municipality': 'Municipality',
                            'Destination geocode': 'geocode', 'Total': 'Total in'}, inplace=True)
    grpbyout.rename(columns={'Origin FU': 'FU', 'Origin Municipality': 'Municipality', 'Origin geocode': 'geocode',
                             'Total': 'Total in'}, inplace=True)
    print(grpbyout.head())
    print(grpbyin.head())
    ttinoutflow = grpbyout.merge(grpbyin, how='outer', on=['FU', 'Municipality', 'geocode'])
    print(ttinoutflow.head())
    del grpbyin
    del grpbyout

    ttinoutflow.fillna(0, inplace=True)
    return ttinoutflow


def main(fname='data/all_FUs-redistributed_mobility_matrix.csv', colsrc='Origin FU', valsrc=None,
         coltgt='Destination FU', valtgt=None, sep=','):
    df = readfile(fname, colsrc, valsrc, coltgt, valtgt, sep)
    dftotalflow = inoutotal(df, colsrc, valsrc, coltgt, valtgt)

    if valsrc is not None:
        if type(valsrc) is str:
            valsrc = [valsrc]
        elif type(valsrc) is not list:
            exit('Bad type for argument valtgt in function readfile')

        if valtgt is not None:
            if type(valtgt) is str:
                valtgt = [valtgt]
            elif type(valtgt) is not list:
                exit('Bad type for argument valtgt in function readfile')

            df = df[(df[colsrc].isin(valsrc)) & (df[coltgt].isin(valtgt))].copy()

    df.to_csv('flowmatrix.csv', index=False)
    dftotalflow.to_csv('totalinoutflow.csv', index=False)
    exit()


if __name__ == '__main__':

    parser = argparse.ArgumentParser(description='Calculate mobility matrix between origin and destination filters.\n' +
                                                 'Returns mobility matrix and total in(out) flow regardless of ' +
                                                 'origin(destination)', formatter_class=RawDescriptionHelpFormatter)
    parser.add_argument('--colsrc', '-colsrc',
                        help='Source column of interest for filter. Default: \'Origin FU\'',
                        default='Origin FU')
    parser.add_argument('--valsrc', '-valsrc', nargs='*', action='append',
                        help='Source values of interest for filter. Default: \'None\'',
                        default=None)
    parser.add_argument('--coltgt', '-coltgt',
                        help='Target column of interest for filter. Default: \'Destination FU\'',
                        default='Destination FU')
    parser.add_argument('--valtgt', '-valtgt', nargs='*', action='append',
                        help='Target values of interest for filter. Default: \'None\'',
                        default=None)
    parser.add_argument('--path', help='Path to mobility matrix file',
                        default='../data/all_FUs-redistributed_mobility_matrix.csv')
    parser.add_argument('--sep', help='Column separator. Default: \',\'', default=',')
    args = parser.parse_args()
    if args.valsrc is None:
        args.valsrc = [None]
    if args.valtgt is None:
        args.valtgt = [None]

    print(args)
    main(fname=args.path, colsrc=args.colsrc, valsrc=args.valsrc[0], coltgt=args.coltgt, valtgt=args.valtgt[0],
         sep=args.sep)
