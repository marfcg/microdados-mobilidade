import pandas as pd
import numpy as np
import seaborn as sns
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches

__author__ = 'Marcelo Ferreira da Costa Gomes'


def preparedata():

    dfflow = pd.read_csv('../data/src_all-tgt_all-extended-mobility_matrix.csv')

    dfflow['cumulative by distance'] = 0
    dfflow['uf percentage'] = 0
    for uf in dfflow.srcfu.unique():
        print(uf)
        ufflow = dfflow.flow[dfflow.srcfu == uf].sum()
        dfflow.loc[dfflow.srcfu == uf, 'uf percentage'] = dfflow.flow[dfflow.srcfu == uf]/ufflow
        dfflow.loc[dfflow.srcfu == uf, 'cumulative by distance'] = dfflow[dfflow.srcfu == uf].apply(lambda row:
                                                                            dfflow.loc[(dfflow.srcfu == uf) &
                                                                                       (dfflow.dist <= row['dist']),
                                                                                       'uf percentage'].sum(),
                                                                            axis=1)
    dfflow.sort_values(by=['srcfu','dist'], axis=0, inplace=True)
    dfflow.to_csv('distance_threshold.csv')

    return dfflow


def plotdistancedist(dfflow):

    dfregioes = pd.read_csv('data/regioesclimaticas.csv')
    for regdiv in ['Região oficial', 'Região']:
        regofic = list(dfregioes[regdiv].unique())
        nreg = len(regofic)
        colors = sns.color_palette('Set2', nreg)
        reg_counter = {reg: 0 for reg in regofic}
        reg_color = {}
        reg_palette = {}
        patches = []
        for n, reg in enumerate(regofic):
            col = colors[n]
            reg_color[reg] = col
            npal = len(dfregioes[dfregioes[regdiv] == reg])
            reg_palette[reg] = sns.light_palette(col, 2*npal)[-npal:]
            patches.append(mpatches.Patch(color=col, label=reg))
    
        dfflowgrp = dfflow.groupby('srcfu')
        fig, ax = plt.subplots()
        for name, group in dfflowgrp:
            reg = dfregioes.loc[dfregioes.Sigla == name, regdiv].values[0]
            col = reg_palette[reg][reg_counter[reg]]
            ax.plot(group['dist'], group['cumulative by distance'], color=col)
            reg_counter[reg] += 1
        plt.xscale('log')
        plt.xlabel('Distance (km)')
        plt.ylabel('Cumulative flow distribution')
        plt.legend(handles=patches, loc=0)
        xmax = dfflow.dist.max()
        plt.hlines(y=0.9, xmin=1, xmax=xmax, linestyles='--', color='k')
        plt.xlim([1, xmax])
        plt.ylim([0, 1])
        if regdiv == 'Região oficial':
            plt.savefig('distance_threshold_official_regions.svg')
        else:
            plt.savefig('distance_threshold_sari_regions.svg')

    return()


def main():
    '''
    Extract distance threshold per State, defined as the distance up to which 90% of the flow is obtained
    :return:
    '''

    df = preparedata()
    plotdistancedist(df)

    exit()


if __name__ == '__main__':
    main()