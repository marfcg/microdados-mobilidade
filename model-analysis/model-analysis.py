# !/usr/bin/env python3
# -*- coding: utf-8 -*-
__author__ = 'Marcelo Ferreira da Costa Gomes'

"""
Script to compare microdata information and model prediction for pendular
mobility in Brazilian municipalities.

Reads original mobility matrix constructed by pendular_mobility-Censo2010.py
Generate new output, redistributing flow to unknown destinations based on known ones.
Recalculate the error accordingly.

Usage:
python3 model-analysis.py [all|FU1] [FU2] [FU3] ...

Options:
all: select all FUs. Default option.
FU: two letter code for the corresponding subdivision of pendular_mobility-Censo2010.py output.

Expect input files to be of the form
../data/[FU]-mobility-matrix-microdata.csv
File names and structure are expected to be the same as the output from pendular_mobility-Censo2010.py script.
"""

from pandas import read_csv, DataFrame
import numpy as np
import sys

ufacron2name = {'RO': 'RONDÔNIA', 'AC': 'ACRE', 'AM': 'AMAZONAS', 'RR': 'RORAIMA', 'PA': 'PARÁ', 'AP': 'AMAPÁ',
                'TO': 'TOCANTINS', 'MA': 'MARANHÃO', 'PI': 'PIAUÍ', 'CE': 'CEARÁ', 'RN': 'RIO GRANDE DO NORTE',
                'PB': 'PARAÍBA', 'PE': 'PERNAMBUCO', 'AL': 'ALAGOAS', 'SE': 'SERGIPE', 'BA': 'BAHIA',
                'MG': 'MINAS GERAIS', 'ES': 'ESPÍRITO SANTO', 'RJ': 'RIO DE JANEIRO', 'SP': 'SÃO PAULO',
                'PR': 'PARANÁ', 'SC': 'SANTA CATARINA', 'RS': 'RIO GRANDE DO SUL', 'MS': 'MATO GROSSO DO SUL',
                'MT': 'MATO GROSSO', 'GO': 'GOIÁS', 'DF': 'DISTRITO FEDERAL'}
ufname2acron = {v: k for k, v in ufacron2name.items()}


def readtable(uflist):
    """
    Read input files and return mobility data frame

    Input
    :list uflist: list of FU of origin to build redistributed mobility matrix

    Output:
    :pd.DataFrame dfmobility: mobility matrix data frame
    :pd.DataFrame dfpop: municipalities population data frame
    """
    dfmobility = DataFrame()
    dfpop = DataFrame()
    for uf in sorted(uflist):
        dftmp = read_csv('../data/%s-mobility-matrix-microdata.csv' % uf)
        dftmppop = dftmp[['Origin Municipality', 'Origin FU', 'Population']].drop_duplicates().reset_index()
        for name, acron in ufname2acron.items():
            dftmp.loc[dftmp['Destination FU'] == name, 'Destination FU'] = acron

        dftmp.loc[(dftmp['Destination Country'] != 'BRASIL') & (-dftmp['Destination Country'].isnull()),
                  'Destination FU'] = dftmp.loc[(dftmp['Destination Country'] != 'BRASIL') &
                                                (-dftmp['Destination Country'].isnull()),
                                                'Destination Country']

        dftmp.loc[(dftmp['Destination Country'] != 'BRASIL') & (-dftmp['Destination Country'].isnull()),
                  'Destination Municipality'] = dftmp.loc[(dftmp['Destination Country'] != 'BRASIL') &
                                                          (-dftmp['Destination Country'].isnull()),
                                                          'Destination Country']

        dfmobility = dfmobility.append(dftmp, ignore_index=True)
        dfpop = dfpop.append(dftmppop, ignore_index=True)

    return dfmobility, dfpop


def cleantable(dfmobilityin):
    """
    Performs proportional redistribution of flow to unknown destination based on ratios of the known ones.
    Respects FU and Country of destination when possible.
    Recalculate standard error correspondingly.

    Input
    :pd.DataFrame dfmobilityin: pandas DataFrame with loaded mobility matrix with unknowns.

    Output
    :pd.DataFrame dfmobility: updated mobility data frame, with unknowns distributed to known destinations.
    """
    dfmobility = dfmobilityin.copy()
    dfmobility.rename(columns={'Total': 'Total orig', 'Std error': 'Std error orig', 'Density': 'Density orig'},
                      inplace=True)
    dfmobility['Total'] = dfmobility['Total orig'].copy()
    dfmobility['Std error'] = dfmobility['Std error orig'].copy()
    dfmobility['Std error conserv'] = dfmobility['Std error'].copy()
    # Create list of unknowns
    ufdestlist = dfmobility['Destination FU'].unique()
    unknown_list = ["%s NÃO SABE MUNICÍPIO" % uf for uf in ufdestlist]  # Knows FU, does not know Municipality
    unknown_list.append("IGNORADO")  # No info
    unknown_list.append(np.nan)  # In Brazil, unknown destination if Destination geocode=9999999 or anywhere otherwise.
    unknown_list.append("MULTIPLE DESTINATIONS")  # Multiple destinations
    unknown_list.append('9999999') # In Brazil, unknown destination

    dfmobility.loc[dfmobility['Destination geocode'] == '9999999', 'Destination Municipality'] = '9999999'

    # Redistribute unkowns by known frequencies, respecting FU when known.
    # Keep "multiple destinations" as a separate entity since it's an unknown of different nature.
    for orig in dfmobility['Origin FU'].unique():
        print(orig)
        dfmobility_fu = dfmobility[dfmobility['Origin FU'] == orig].copy()

        # Square the error column to facilitate its calculation over the redistribution:
        dfmobility_fu['Std error'] *= dfmobility_fu['Std error']
        dfmobility_fu['Std error conserv'] *= dfmobility_fu['Std error conserv']

        originmunlist = dfmobility_fu['Origin Municipality'].unique()
        for origmun in originmunlist:

            # "FU NÃO SABE MUNICÍPIO", can be any destination in the specific FU, in Brazil:
            for ufdest in ufacron2name:
                charval = "%s NÃO SABE MUNICÍPIO" % ufdest
                val = dfmobility_fu.loc[dfmobility_fu['Origin Municipality'] == origmun, 'Total']. \
                    where(dfmobility_fu['Destination Municipality'] == charval).dropna().to_frame(name='Total')
                val['Std error'] = dfmobility_fu.loc[dfmobility_fu['Origin Municipality'] == origmun, 'Std error']. \
                    where(dfmobility_fu['Destination Municipality'] == charval).dropna().to_frame(name='Std error')
                val['Error factor'] = dfmobility_fu.loc[dfmobility_fu['Origin Municipality'] == origmun,
                                                        'Error factor']. \
                    where(dfmobility_fu['Destination Municipality'] == charval).dropna().to_frame(name='Error factor')

                if val.size > 0:
                    # Redistribute over known FU destinations from origmun
                    dftmp = dfmobility_fu.loc[(dfmobility_fu['Origin Municipality'] == origmun) &
                                              (dfmobility_fu['Destination FU'] == ufdest) &
                                              (-dfmobility_fu['Destination Municipality'].isin(unknown_list)),
                                              ['Total', 'Std error', 'Std error conserv']].copy()
                    known_dest = dftmp.Total.sum()
                    dftmp['Total'] += dftmp['Total'] * float(val['Total']) / known_dest
                    dftmp['Std error'] += np.square(float(val['Error factor'])) * dftmp['Total'].apply(np.square) / (
                        known_dest ** 2)
                    dftmp['Std error conserv'] += float(val['Std error']) * dftmp['Total'].apply(np.square) / (
                        known_dest ** 2)
                    dfmobility_fu.loc[(dfmobility_fu['Origin Municipality'] == origmun) &
                                      (dfmobility_fu['Destination FU'] == ufdest) &
                                      (-dfmobility_fu['Destination Municipality'].isin(unknown_list)),
                                      ['Total', 'Std error', 'Std error conserv']] = dftmp.copy()
                    dfmobility_fu.loc[(dfmobility_fu['Origin Municipality'] == origmun) &
                                      (dfmobility_fu['Destination Municipality'] == charval), 'Total'] = 0
                    dfmobility_fu.loc[(dfmobility_fu['Origin Municipality'] == origmun) &
                                      (dfmobility_fu['Destination Municipality'] == charval), 'Std error'] = 0
                    dfmobility_fu.loc[(dfmobility_fu['Origin Municipality'] == origmun) &
                                      (dfmobility_fu['Destination Municipality'] == charval), 'Std error conserv'] = 0

            # Destination Municiaplity "9999999", can be any destination in Brazil:
            val = dfmobility_fu.loc[dfmobility_fu['Origin Municipality'] == origmun, 'Total']. \
                where(dfmobility_fu['Destination Municipality'] == '9999999').dropna().to_frame(name='Total')
            val['Std error'] = dfmobility_fu.loc[dfmobility_fu['Origin Municipality'] == origmun, 'Std error']. \
                where(dfmobility_fu['Destination Municipality'] == '9999999').dropna().to_frame(name='Std error')
            val['Error factor'] = dfmobility_fu.loc[dfmobility_fu['Origin Municipality'] == origmun, 'Error factor']. \
                where(dfmobility_fu['Destination Municipality'] == '9999999').dropna().to_frame(name='Error factor')
            if val.size > 0:
                # Redistribute over known Brazilian destinations from origmun
                dftmp = dfmobility_fu.loc[(dfmobility_fu['Origin Municipality'] == origmun) &
                                          (dfmobility_fu['Destination Country'] == 'BRASIL') &
                                          (-dfmobility_fu['Destination Municipality'].isin(unknown_list)),
                                          ['Total', 'Std error', 'Std error conserv']].copy()
                known_dest = dftmp.Total.sum()
                dftmp['Total'] += dftmp['Total'] * float(val['Total']) / known_dest
                dftmp['Std error'] += np.square(float(val['Error factor'])) * dftmp['Total'].apply(np.square) / (
                    known_dest ** 2)
                dftmp['Std error conserv'] += float(val['Std error']) * dftmp['Total'].apply(np.square) / (
                    known_dest ** 2)
                dfmobility_fu.loc[(dfmobility_fu['Origin Municipality'] == origmun) &
                                  (dfmobility_fu['Origin FU'] == orig) &
                                  (dfmobility_fu['Destination Country'] == 'BRASIL') &
                                  (-dfmobility_fu['Destination Municipality'].isin(unknown_list)),
                                  ['Total', 'Std error', 'Std error conserv']] = dftmp.copy()
                dfmobility_fu.loc[(dfmobility_fu['Origin Municipality'] == origmun) &
                                  (dfmobility_fu['Destination Municipality'] == '9999999'), 'Total'] = 0
                dfmobility_fu.loc[(dfmobility_fu['Origin Municipality'] == origmun) &
                                  (dfmobility_fu['Destination Municipality'] == '9999999'), 'Std error'] = 0
                dfmobility_fu.loc[(dfmobility_fu['Origin Municipality'] == origmun) &
                                  (dfmobility_fu['Destination Municipality'] == '9999999'), 'Std error conserv'] = 0

            # "IGNORADO", can be any destination:
            val = dfmobility_fu.loc[dfmobility_fu['Origin Municipality'] == origmun, 'Total']. \
                where(dfmobility_fu['Destination Municipality'] == 'IGNORADO').dropna().to_frame(name='Total')
            val['Std error'] = dfmobility_fu.loc[dfmobility_fu['Origin Municipality'] == origmun, 'Std error']. \
                where(dfmobility_fu['Destination Municipality'] == 'IGNORADO').dropna().to_frame(name='Std error')
            val['Error factor'] = dfmobility_fu.loc[dfmobility_fu['Origin Municipality'] == origmun, 'Error factor']. \
                where(dfmobility_fu['Destination Municipality'] == 'IGNORADO').dropna().to_frame(name='Error factor')
            if val.size > 0:
                # Redistribute over full set of known destinations from origmun
                dftmp = dfmobility_fu.loc[(dfmobility_fu['Origin Municipality'] == origmun) &
                                          (dfmobility_fu['Origin FU'] == orig) &
                                          (-dfmobility_fu['Destination Municipality'].isin(unknown_list)),
                                          ['Total', 'Std error', 'Std error conserv']].copy()
                known_dest = dftmp.Total.sum()
                dftmp['Total'] += dftmp['Total'] * float(val['Total']) / known_dest
                dftmp['Std error'] += np.square(float(val['Error factor'])) * dftmp['Total'].apply(np.square) / (
                    known_dest ** 2)
                dftmp['Std error conserv'] += float(val['Std error']) * dftmp['Total'].apply(np.square) / (
                    known_dest ** 2)
                dfmobility_fu.loc[(dfmobility_fu['Origin Municipality'] == origmun) &
                                  (dfmobility_fu['Origin FU'] == orig) &
                                  (-dfmobility_fu['Destination Municipality'].isin(unknown_list)),
                                  ['Total', 'Std error', 'Std error conserv']] = dftmp.copy()
                dfmobility_fu.loc[(dfmobility_fu['Origin Municipality'] == origmun) &
                                  (dfmobility_fu['Destination Municipality'] == 'IGNORADO'), 'Total'] = 0
                dfmobility_fu.loc[(dfmobility_fu['Origin Municipality'] == origmun) &
                                  (dfmobility_fu['Destination Municipality'] == 'IGNORADO'), 'Std error'] = 0
                dfmobility_fu.loc[(dfmobility_fu['Origin Municipality'] == origmun) &
                                  (dfmobility_fu['Destination Municipality'] == 'IGNORADO'), 'Std error conserv'] = 0

            # NaN, can be any destination:
            val = dfmobility_fu.loc[dfmobility_fu['Origin Municipality'] == origmun, 'Total']. \
                where(dfmobility_fu['Destination Municipality'].isnull()).dropna().to_frame(name='Total')
            val['Std error'] = dfmobility_fu.loc[dfmobility_fu['Origin Municipality'] == origmun, 'Std error']. \
                where(dfmobility_fu['Destination Municipality'].isnull()).dropna().to_frame(name='Std error')
            val['Error factor'] = dfmobility_fu.loc[dfmobility_fu['Origin Municipality'] == origmun, 'Error factor']. \
                where(dfmobility_fu['Destination Municipality'].isnull()).dropna().to_frame(name='Error factor')
            if val.size > 0:
                # Redistribute over full set of known destinations from origmun
                dftmp = dfmobility_fu.loc[(dfmobility_fu['Origin Municipality'] == origmun) &
                                          (dfmobility_fu['Origin FU'] == orig) &
                                          (-dfmobility_fu['Destination Municipality'].isin(unknown_list)),
                                          ['Total', 'Std error', 'Std error conserv']].copy()
                known_dest = dftmp.Total.sum()
                dftmp['Total'] += dftmp['Total'] * float(val['Total']) / known_dest
                dftmp['Std error'] += np.square(float(val['Error factor'])) * dftmp['Total'].apply(np.square) / (
                    known_dest ** 2)
                dftmp['Std error conserv'] += float(val['Std error']) * dftmp['Total'].apply(np.square) / (
                    known_dest ** 2)
                dfmobility_fu.loc[(dfmobility_fu['Origin Municipality'] == origmun) &
                                  (dfmobility_fu['Origin FU'] == orig) &
                                  (-dfmobility_fu['Destination Municipality'].isin(unknown_list)),
                                  ['Total', 'Std error', 'Std error conserv']] = dftmp.copy()
                dfmobility_fu.loc[(dfmobility_fu['Origin Municipality'] == origmun) &
                                  (dfmobility_fu['Destination Municipality'].isnull()), 'Total'] = 0
                dfmobility_fu.loc[(dfmobility_fu['Origin Municipality'] == origmun) &
                                  (dfmobility_fu['Destination Municipality'].isnull()), 'Std error'] = 0
                dfmobility_fu.loc[(dfmobility_fu['Origin Municipality'] == origmun) &
                                  (dfmobility_fu['Destination Municipality'].isnull()), 'Std error conserv'] = 0

        # Take the square root of the redistributed errors and update table:
        dfmobility_fu['Std error'] = dfmobility_fu['Std error'].apply(np.sqrt)
        dfmobility_fu['Std error conserv'] = dfmobility_fu['Std error conserv'].apply(np.sqrt)
        dfmobility.loc[dfmobility['Origin FU'] == orig, ['Total', 'Std error', 'Std error conserv']] = \
            dfmobility_fu.loc[dfmobility_fu['Origin FU'] == orig, ['Total', 'Std error', 'Std error conserv']].copy()

    dfmobility['Density'] = dfmobility['Total'] / dfmobility['Population']
    return dfmobility


def main(ufrequest=None):
    """
    Recieve FU list from user and dispatch reading and cleaning of the data
    :ufrequest : list of FU of origin to build redistributed mobility matrix. Default None which corresponds to 'all'
    """

    # Check requested FU for calculation:
    if ufrequest is None or 'all' in ufrequest:
        ufrequest = [k for k in ufacron2name]
        ufrequest.extend(['SP1', 'SP2-RM'])
        ufrequest.remove('SP')
        fout = '../data/all_FUs-redistributed_mobility_matrix.csv'
    else:
        if 'SP' in ufrequest:
            ufrequest.extend(['SP1', 'SP2-RM'])
            ufrequest.remove('SP')
        fout = '../data/%s-redistributed_mobility_matrix.csv' % ('-'.join(ufrequest))

    # Read and redistribute the unknowns:
    dfmobility, dfpop = readtable(ufrequest)
    dfmobility_clean = cleantable(dfmobility)

    # Write redistributed matrix to file:
    dfmobility_clean.to_csv(fout, index=False)

    return


if __name__ == '__main__':

    if len(sys.argv) == 1:
        ufrequested = ['all']
    else:
        ufrequested = [v for v in sys.argv[1:]]

    main(ufrequested)
