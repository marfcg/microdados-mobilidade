__author__ = 'Marcelo Ferreira da Costa Gomes'

import pandas as pd

capitals = [1200401,
            2704302,
            1302603,
            1600303,
            2927408,
            2304400,
            5300108,
            3205309,
            5208707,
            2111300,
            3106200,
            5103403,
            5002704,
            1501402,
            2507507,
            2611606,
            2211001,
            4106902,
            3304557,
            2408102,
            1100205,
            1400100,
            4314902,
            4205407,
            2800308,
            3550308,
            1721000]

mun_list = [2408102, 2611606, 3106200, 5002704]
dfpop = pd.read_csv('../data/Brazil-municipalities-2010.csv')[['CD_GEOCODM', 'POPULATION']] \
    .rename(columns={'CD_GEOCODM': 'geocode', 'POPULATION': 'Population'})
dfpop = dfpop.loc[dfpop.geocode.isin(capitals),].copy()


def flowdensity():

    dftotals = pd.read_csv('./totalinoutflow.csv')

    dftotals = dfpop.merge(dftotals, on='geocode', how='left')
    dftotals['Total_density'] = dftotals.Total / dftotals.Population

    dftotals.sort_values(by='Total_density', ascending=False, inplace=True)
    dftotals = dftotals.reset_index().drop('index', axis=1)
    dftotals['Density rank'] = dftotals.index + 1

    dftotals.sort_values(by='Total', ascending=False, inplace=True)
    dftotals = dftotals.reset_index().drop('index', axis=1)
    dftotals['Absolute rank'] = dftotals.index + 1

    dfarbo = dftotals.loc[dftotals.geocode.isin(mun_list), ].copy()

    return(dfarbo)


def interstateflow():

    df = pd.read_csv('./flowmatrix.csv')[['Origin geocode', 'Origin FU', 'Destination FU', 'Destination geocode',
                                          'Total']]
    df = df.loc[((df['Origin geocode'].isin(capitals)) | (df['Destination geocode'].isin([str(m) for m in capitals])))
                & (df['Origin FU'] != df['Destination FU']), ]

    dfinterstate_out = df.loc[df['Origin geocode'].isin(capitals), ['Origin geocode', 'Destination FU',
                                                                    'Total']].rename(
        columns={'Origin geocode': 'geocode', 'Destination FU': 'Connecting FU', 'Total': 'Total interstate out'})
    dfinterstate_out = dfinterstate_out.groupby(['geocode', 'Connecting FU'], as_index=False).agg(sum)

    dfinterstate_in = df.loc[df['Destination geocode'].isin([str(m) for m in capitals]), ['Destination geocode',
                                                                                         'Origin FU',
                                                                    'Total']].rename(
        columns={'Destination geocode': 'geocode', 'Origin FU': 'Connecting FU', 'Total': 'Total interstate in'})

    dfinterstate_in.geocode = dfinterstate_in.geocode.astype(int)
    dfinterstate_in = dfinterstate_in.groupby(['geocode', 'Connecting FU'], as_index=False).agg(sum)

    dfinterstate = dfinterstate_in.merge(dfinterstate_out, on=['geocode', 'Connecting FU'], how='outer')
    dfinterstate.fillna(0, inplace=True)
    dfinterstate['Total interstate'] = dfinterstate[['Total interstate in', 'Total interstate out']].sum(axis=1)
    dfinterstate = dfpop.merge(dfinterstate, how='right', on='geocode')
    dfinterstate['Total interstate density'] = dfinterstate['Total interstate'] / dfinterstate.Population
    dfinterstate.sort_values(by=['geocode', 'Total interstate'], ascending=False, inplace=True)
    dfinterstatesumed = dfinterstate[['geocode', 'Total interstate', 'Total interstate density']].\
        groupby('geocode', as_index=False).agg(sum)

    dfinterstatesumed.sort_values(by='Total interstate', ascending=False, inplace=True)
    dfinterstatesumed = dfinterstatesumed.reset_index().drop('index', axis=1)
    dfinterstatesumed['Interstate absolute flow rank'] = dfinterstatesumed.index + 1

    dfinterstatesumed.sort_values(by='Total interstate density', ascending=False, inplace=True)
    dfinterstatesumed = dfinterstatesumed.reset_index().drop('index', axis=1)
    dfinterstatesumed['Interstate density flow rank'] = dfinterstatesumed.index + 1

    dfinterstatesumed = dfinterstatesumed[dfinterstatesumed.geocode.isin(mun_list)].copy()
    dfinterstate = dfinterstate[dfinterstate.geocode.isin(mun_list)].copy()

    return(dfinterstate, dfinterstatesumed)


def main():

    dfarbo = flowdensity()
    dfinterstate, dfinterstatesumed = interstateflow()

    dfarbo = dfarbo.merge(dfinterstatesumed, on='geocode', how='left')
    dfarbo['Interstate over total flow'] = dfarbo['Total interstate'] / dfarbo['Total']
    dfarbo[['Total in', 'Total out', 'Total', 'Total interstate']] = dfarbo[['Total in', 'Total out', 'Total',
                                                                           'Total interstate']].round().astype(int)

    dfarbo.to_csv('arbo-alvo_workstudy_flow_summary.csv', index=False)

    dfinterstate[['Total interstate in', 'Total interstate out', 'Total interstate']] = \
        dfinterstate[['Total interstate in', 'Total interstate out', 'Total interstate']].round().astype(int)
    dfinterstate = dfinterstate.merge(dfarbo[['geocode', 'Municipality']], on='geocode', how='left')
    dfinterstate[[0,7]+list(range(1,7))].to_csv('arbo-alvo_workstudy_outofstateflow.csv', index=False)


if __name__ == '__main__':
    main()