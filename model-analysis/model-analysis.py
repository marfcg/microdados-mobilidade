#!/usr/bin/env python
# -*- coding: utf-8 -*-

'''
Script to compare microdata information and model prediction for pendular
mobility in Brazilian municipalities.
'''

import pandas as pd
import numpy as np
from collections import defaultdict

ufacron2name = {'RO': 'RONDÔNIA', 'AC': 'ACRE', 'AM': 'AMAZONAS', 'RR': 'RORAIMA', 'PA': 'PARÁ', 'AP': 'AMAPÁ',
                'TO': 'TOCANTINS', 'MA': 'MARANHÃO', 'PI': 'PIAUÍ', 'CE': 'CEARÁ', 'RN': 'RIO GRANDE DO NORTE',
                'PB': 'PARAÍBA', 'PE': 'PERNAMBUCO', 'AL': 'ALAGOAS', 'SE': 'SERGIPE', 'BA': 'BAHIA',
                'MG': 'MINAS GERAIS', 'ES': 'ESPÍRITO SANTO', 'RJ': 'RIO DE JANEIRO', 'SP': 'SÃO PAULO',
                'PR': 'PARANÁ', 'SC': 'SANTA CATARINA', 'RS': 'RIO GRANDE DO SUL', 'MS': 'MATO GROSSO DO SUL',
                'MT': 'MATO GROSSO', 'GO': 'GOIÁS', 'DF': 'DISTRITO FEDERAL'}
ufname2acron = {v: k for k, v in ufacron2name.items()}

def readtable():
  
    dfmobility = pd.DataFrame()
    dfpop = pd.DataFrame()
    for uf in sorted(uflist):
        dftmp = pd.read_csv('../data/%s-matriz-mobilidade-microdados.csv')
        dftmppop = dftmp[['Origin Municipality', 'Origin FU', 'Population']].drop_duplicates().reset_index()
        for name, acron in ufname2acron.items():
            dftmp.loc[dftmp['Destination FU'] == name, 'Destination FU'] = acron

        dftmp.loc[(dftmp['Destination Country'] != 'BRASIL') & (-dftmp['Destination Country'].isnull()),
                  'Destination UF'] = dftmp.loc[(dftmp['Destination Country'] != 'BRASIL') &
                                                (-dftmp['Destination Country'].isnull()),
                                                'Destination Country']

        dftmp.loc[(dftmp['Destination Country'] != 'BRASIL') & (-dftmp['Destination Country'].isnull()),
                  'Destination Municipality'] = dftmp.loc[(dftmp['Destination Country'] != 'BRASIL') &
                                                (-dftmp['Destination Country'].isnull()),
                                                'Destination Country']

        dfmobility = dfmobility.append(dftmp, ignore_index=True)
        dfpop = dfpop.append(dftmppop, ignore_index=True)

    return dfmobility, dfpop

def cleantable(dfmobility):

    # Create list of unknowns
    unknown_list = ["%s,NÃO SABE MUNICÍPIO" % (uf) for uf in uflist] # Knows FU, does not know Municipality
    unknown_list.append("IGNORADO")                                  # No info
    unknown_list.append(np.nan)                                      # In Brazil, unknown destination
    unknown_list.append("MULTIPLE DESTINATIONS")                     # Multiple destinations

    # Define columns to be used for aggregating known totals
    dfknown_cols = ['Origin Municipality', 'Origin FU', 'Destination Country', 'Destination FU', 'Total', 'Std error']
    grpby_cols = ['Origin Municipality', 'Origin FU', 'Destination Country', 'Destination FU']

    # Aggregate knowns
    dfknown = dfmobility.loc[(-dfmobility['Total'].isnull()) &
                             (-dfmobility['Destination Municipality'].isin(unknown_list)), dfknown_cols]\
        .groupby(grpby_cols).sum().reset_index().copy()

    # Redistribute unkowns by known frequencies, respecting FU when known.
    # Keep "multiple destinations" as a separate entity since it's an unkown of different nature.
    for orig in ufacron2name:
        dfknown_fu = dfknown[dfknown['Origin FU'] == orig]
        dfmobility_fu = dfknown[dfknown['Origin FU'] == orig]
        for origmun in dfknown.loc[dfknown['Origin FU'] == orig, 'Origin Municipality']:

            # "IGNORADO", can be any destination:
            val = dfmobility_fu.loc[dfmobility_fu['Origin Municipality'] == origmun, 'Total'].\
                where(dfmobility_fu['Destination Municipality'] == 'IGNORADO').dropna().to_frame(name='Total')
            val['Std error'] = dfmobility_fu.loc[dfmobility_fu['Origin Municipality'] == origmun, 'Std error'].\
                where(dfmobility_fu['Destination Municipality'] == 'IGNORADO').dropna().to_frame(name='Std error')
            if val.size == 1:
                dftmp = dfmobility.loc[(dfmobility['Origin Municipality'] == origmun) &
                                       (dfmobility['Origin FU'] == orig) &
                                       (-dfmobility['Destination Municipality'].isin(unknown_list)),
                                       ['Total', 'Std error']]
                known_dest = dfknown_fu.Total[dfknown_fu['Origim Municipality'] == origmun].sum()
                dftmp['Total'] += dftmp*float(val['Total'])/known_dest
                dftmp['Std error'] += dftmp*float(val['Std error'])/known_dest

            # "NaN", can be any destination in Brazil:
            val = dfmobility_fu.loc[dfmobility_fu['Origin Municipality'] == origmun, 'Total'].\
                where(dfmobility_fu['Destination Municipality'] == np.nan).dropna().to_frame(name='Total')
            val['Std error'] = dfmobility_fu.loc[dfmobility_fu['Origin Municipality'] == origmun, 'Std error'].\
                where(dfmobility_fu['Destination Municipality'] == np.nan).dropna().to_frame(name='Std error')
            if val.size == 1:
                dftmp = dfmobility.loc[(dfmobility['Origin Municipality'] == origmun) &
                                       (dfmobility['Origin FU'] == orig) &
                                       (dfmobility['Destination Country'] == 'BRASIL')
                                       (-dfmobility['Destination Municipality'].isin(unknown_list)),
                                       ['Total', 'Std error']]
                known_dest = dfknown_fu.Total[(dfknown_fu['Origim Municipality'] == origmun) &
                                              (dfknown_fu['Destination Country'] == 'BRASIL')].sum()
                dftmp['Total'] += dftmp*float(val['Total'])/known_dest
                dftmp['Std error'] += dftmp*float(val['Std error'])/known_dest

            # "FU,NÃO SABE MUNICÍPIO", can be any destination in the specific FU, in Brazil:


        for dest, val in table[orig].items():
            if dest not in unknown_list:
                known_dest[orig] += val
