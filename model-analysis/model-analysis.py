#!/usr/bin/env python
# -*- coding: utf-8 -*-

'''
Script to compare microdata information and model prediction for pendular
mobility in Brazilian municipalities.
'''

import pandas as pd
import numpy as np

ufacron2name = {'RO': 'RONDÔNIA', 'AC': 'ACRE', 'AM': 'AMAZONAS', 'RR': 'RORAIMA', 'PA': 'PARÁ', 'AP': 'AMAPÁ',
                'TO': 'TOCANTINS', 'MA': 'MARANHÃO', 'PI': 'PIAUÍ', 'CE': 'CEARÁ', 'RN': 'RIO GRANDE DO NORTE',
                'PB': 'PARAÍBA', 'PE': 'PERNAMBUCO', 'AL': 'ALAGOAS', 'SE': 'SERGIPE', 'BA': 'BAHIA',
                'MG': 'MINAS GERAIS', 'ES': 'ESPÍRITO SANTO', 'RJ': 'RIO DE JANEIRO', 'SP': 'SÃO PAULO',
                'PR': 'PARANÁ', 'SC': 'SANTA CATARINA', 'RS': 'RIO GRANDE DO SUL', 'MS': 'MATO GROSSO DO SUL',
                'MT': 'MATO GROSSO', 'GO': 'GOIÁS', 'DF': 'DISTRITO FEDERAL'}
ufname2acron = {v: k for k, v in ufacron2name.items()}

def readtable(uflist):

    dfmobility = pd.DataFrame()
    dfpop = pd.DataFrame()
    for uf in sorted(uflist):
        dftmp = pd.read_csv('../data/%s-mobility-matrix-microdata.csv' % uf)
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

    dfmobility = dfmobilityin.copy()
    # Create list of unknowns
    unknown_list = ["%s,NÃO SABE MUNICÍPIO" % (uf) for uf in uflist] # Knows FU, does not know Municipality
    unknown_list.append("IGNORADO")                                  # No info
    unknown_list.append(np.nan)                                      # In Brazil, unknown destination
    unknown_list.append("MULTIPLE DESTINATIONS")                     # Multiple destinations

    # Define columns to be used for aggregating known totals
    dfknown_cols = ['Origin Municipality', 'Origin FU', 'Destination Country', 'Destination FU', 'Total', 'Std error']
    grpby_cols = ['Origin Municipality', 'Origin FU', 'Destination Country', 'Destination FU']

    # # Aggregate knowns
    # dfknown = dfmobility.loc[(-dfmobility['Total'].isnull()) &
    #                          (-dfmobility['Destination Municipality'].isin(unknown_list)), dfknown_cols]\
    #     .groupby(grpby_cols).sum().reset_index().copy()

    # Redistribute unkowns by known frequencies, respecting FU when known.
    # Keep "multiple destinations" as a separate entity since it's an unknown of different nature.
    for orig in ufacron2name:
        dfmobility_fu = dfmobility[dfmobility['Origin FU'] == orig]
        for origmun in dfmobility_fu['Origin Municipality'].unique():

            # "FU,NÃO SABE MUNICÍPIO", can be any destination in the specific FU, in Brazil:
            for ufdest in ufacron2name:
                charval = "%s NÃO SABE MUNICÍPIO" % (ufdest)
                val = dfmobility_fu.loc[dfmobility_fu['Origin Municipality'] == origmun, 'Total'].\
                    where(dfmobility_fu['Destination Municipality'] == charval).dropna().to_frame(name='Total')
                val['Std error'] = dfmobility_fu.loc[dfmobility_fu['Origin Municipality'] == origmun, 'Std error'].\
                    where(dfmobility_fu['Destination Municipality'] == charval).dropna().to_frame(name='Std error')
                if val.size == 1:
                    # Redistribute over known FU destinations from origmun
                    dftmp = dfmobility_fu.loc[(dfmobility_fu['Origin Municipality'] == origmun) &
                                              (dfmobility_fu['Destination FU'] == ufdest) &
                                              (-dfmobility_fu['Destination Municipality'].isin(unknown_list)),
                                              ['Total', 'Std error']]
                    known_dest = dftmp.Total.sum()
                    dftmp['Total'] += dftmp['Total']*float(val['Total'])/known_dest
                    dftmp['Std error'] += dftmp['Std error']*float(val['Std error'])/known_dest
                    dfmobility_fu.loc[(dfmobility_fu['Origin Municipality'] == origmun) &
                                      (dfmobility_fu['Destination FU'] == ufdest) &
                                      (-dfmobility_fu['Destination Municipality'].isin(unknown_list)),
                                      ['Total', 'Std error']] = dftmp
            
            # "NaN", can be any destination in Brazil:
            val = dfmobility_fu.loc[dfmobility_fu['Origin Municipality'] == origmun, 'Total'].\
                where(dfmobility_fu['Destination Municipality'] == np.nan).dropna().to_frame(name='Total')
            val['Std error'] = dfmobility_fu.loc[dfmobility_fu['Origin Municipality'] == origmun, 'Std error'].\
                where(dfmobility_fu['Destination Municipality'] == np.nan).dropna().to_frame(name='Std error')
            if val.size == 1:
                # Redistribute over known Brazilian destinations from origmun
                dftmp = dfmobility_fu.loc[(dfmobility_fu['Origin Municipality'] == origmun) &
                                          (dfmobility_fu['Destination Country'] == 'BRASIL') &
                                          (-dfmobility_fu['Destination Municipality'].isin(unknown_list)),
                                          ['Total', 'Std error']]
                known_dest = dftmp.Total.sum()
                dftmp['Total'] += dftmp['Total']*float(val['Total'])/known_dest
                dftmp['Std error'] += dftmp['Std error']*float(val['Std error'])/known_dest
                dfmobility.loc[(dfmobility_fu['Origin Municipality'] == origmun) &
                               (dfmobility_fu['Origin FU'] == orig) &
                               (dfmobility_fu['Destination Country'] == 'BRASIL') &
                               (-dfmobility_fu['Destination Municipality'].isin(unknown_list)),
                               ['Total', 'Std error']] = dftmp

            # "IGNORADO", can be any destination:
            val = dfmobility_fu.loc[dfmobility_fu['Origin Municipality'] == origmun, 'Total'].\
                where(dfmobility_fu['Destination Municipality'] == 'IGNORADO').dropna().to_frame(name='Total')
            val['Std error'] = dfmobility_fu.loc[dfmobility_fu['Origin Municipality'] == origmun, 'Std error'].\
                where(dfmobility_fu['Destination Municipality'] == 'IGNORADO').dropna().to_frame(name='Std error')
            if val.size == 1:
                # Redistribute over full set of known destinations from origmun
                dftmp = dfmobility.loc[(dfmobility_fu['Origin Municipality'] == origmun) &
                                       (dfmobility_fu['Origin FU'] == orig) &
                                       (-dfmobility_fu['Destination Municipality'].isin(unknown_list)),
                                       ['Total', 'Std error']]
                known_dest = dftmp.Total.sum()
                dftmp['Total'] += dftmp['Total']*float(val['Total'])/known_dest
                dftmp['Std error'] += dftmp['Std error']*float(val['Std error'])/known_dest
                dfmobility.loc[(dfmobility_fu['Origin Municipality'] == origmun) &
                               (dfmobility_fu['Origin FU'] == orig) &
                               (-dfmobility_fu['Destination Municipality'].isin(unknown_list)),
                               ['Total', 'Std error']] = dftmp
        dfmobility.loc[dfmobility['Origin FU'] == orig,] = dfmobility_fu.loc[dfmobility['Origin FU'] == orig,]

    return dfmobility