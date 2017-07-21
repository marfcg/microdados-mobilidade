import pandas as pd
import seaborn as sns
import numpy as np
import matplotlib.pyplot as plt
import statsmodels.api as sm
import matplotlib.font_manager as fm
from matplotlib.colors import LogNorm
from scipy.stats import pearsonr
from argparse import RawDescriptionHelpFormatter

__author__ = 'Marcelo Ferreira da Costa Gomes'


def extracthisto(df, col):
    minflow = df[col].min()
    maxflow = df[col].max()
    xbin = np.logspace(np.log10(minflow), np.log10(maxflow), 500)
    xhist, hbin = np.histogram(df[col], density=True, bins=xbin)
    hval = [1.0]
    hold = 1
    xval = [minflow]
    for i, v in enumerate(xhist):
        if v > 0:
            w = hbin[i + 1] - hbin[i]
            hval.append(hold - v * w)
            xval.append(hbin[i + 1])
            hold = hval[-1]

    print(hval[-2:])
    hval = hval[0:-1]
    xval = xval[0:-1]

    return hval, xval


def main():
    # Set font propoerties
    fontproplgd = fm.FontProperties('Oswald')
    fontproplgd.set_size(12)
    fontproplbl = fm.FontProperties('Oswald')
    fontproplbl.set_size(24)
    fontpropticks = fm.FontProperties('Oswald')
    fontpropticks.set_size(18)

    dfBR = pd.read_csv('../data/src_all-tgt_all-extended-mobility_matrix.csv')
    dfSP = pd.read_csv('../data/src_SP-tgt_SP-mobility_grav_rad_matrix.csv')
    dfRJ = pd.read_csv('../data/src_RJ-tgt_RJ-mobility_grav_rad_matrix.csv')
    dfPR = pd.read_csv('../data/src_PR-tgt_PR-mobility_grav_rad_matrix.csv')

    nodes = len(dfBR.src.unique())
    vertices = len(dfBR)
    d = vertices / (nodes*(nodes-1))
    print('BR', nodes, vertices, d)
    nodes = len(dfSP.src.unique())
    vertices = len(dfSP)
    d = vertices / (nodes*(nodes-1))
    print('SP', nodes, vertices, d)
    nodes = len(dfRJ.src.unique())
    vertices = len(dfRJ)
    d = vertices / (nodes*(nodes-1))
    print('RJ', nodes, vertices, d)
    nodes = len(dfPR.src.unique())
    vertices = len(dfPR)
    d = vertices / (nodes*(nodes-1))
    print('PR', nodes, vertices, d)


    print(dfBR.flow.sum())
    print(dfBR.loc[dfBR['srcfu'].isin(['SP', 'RJ', 'PR']), ['srcfu', 'flow']].groupby('srcfu').agg(sum))
    print(dfBR.loc[(dfBR['srcfu'] == 'SP') & (dfBR['tgtfu'] == 'SP'), ['srcfu', 'flow']].groupby('srcfu').agg(sum))
    print(dfBR.loc[(dfBR['srcfu'] == 'RJ') & (dfBR['tgtfu'] == 'RJ'), ['srcfu', 'flow']].groupby('srcfu').agg(sum))
    print(dfBR.loc[(dfBR['srcfu'] == 'PR') & (dfBR['tgtfu'] == 'PR'), ['srcfu', 'flow']].groupby('srcfu').agg(sum))

    print(dfBR[['src', 'srcfu', 'srcpop']].drop_duplicates().groupby('srcfu').agg(sum))
    print(dfBR[['src', 'srcfu', 'srcpop']].drop_duplicates().groupby('srcfu').agg(sum).sum())
    print('BR')
    dftmp = dfBR[['src', 'srcname', 'srcpop', 'Ti']].drop_duplicates()
    dftmp['Ti density'] = dftmp['Ti'].div(dftmp['srcpop'])
    print(dftmp.sort_values(by='Ti', ascending=False).head(10))
    print(dftmp.sort_values(by='Ti density', ascending=False).head(10))
    print('SP')
    dftmp = dfSP[['src', 'srcname', 'srcpop', 'Ti']].drop_duplicates()
    dftmp['Ti density'] = dftmp['Ti'].div(dftmp['srcpop'])
    print(dftmp.sort_values(by='Ti', ascending=False).head(10))
    print(dftmp.sort_values(by='Ti density', ascending=False).head(10))
    print('RJ')
    dftmp = dfRJ[['src', 'srcname', 'srcpop', 'Ti']].drop_duplicates()
    dftmp['Ti density'] = dftmp['Ti'].div(dftmp['srcpop'])
    print(dftmp.sort_values(by='Ti', ascending=False).head(10))
    print(dftmp.sort_values(by='Ti density', ascending=False).head(10))
    print('PR')
    dftmp = dfPR[['src', 'srcname', 'srcpop', 'Ti']].drop_duplicates()
    dftmp['Ti density'] = dftmp['Ti'].div(dftmp['srcpop'])
    print(dftmp.sort_values(by='Ti', ascending=False).head(10))
    print(dftmp.sort_values(by='Ti density', ascending=False).head(10))

    print('BR')
    dftmp = dfBR[['tgt', 'tgtname', 'tgtpop']].drop_duplicates()
    dfsum = dfBR[['tgt', 'tgtname', 'flow']].groupby(['tgt'], as_index=False).agg(sum)[['tgt','flow']]
    dftmp = pd.merge(dftmp, dfsum, on=['tgt'])
    dftmp['flow density'] = dftmp['flow'].div(dftmp['tgtpop'])
    print(dftmp.sort_values(by='flow', ascending=False).head(10))
    print(dftmp.sort_values(by='flow density', ascending=False).head(10))
    print('SP')
    dftmp = dfSP[['tgt', 'tgtname', 'tgtpop']].drop_duplicates()
    dfsum = dfSP[['tgt', 'tgtname', 'flow']].groupby(['tgt'], as_index=False).agg(sum)[['tgt','flow']]
    dftmp = pd.merge(dftmp, dfsum, on=['tgt'])
    dftmp['flow density'] = dftmp['flow'].div(dftmp['tgtpop'])
    print(dftmp.sort_values(by='flow', ascending=False).head(10))
    print(dftmp.sort_values(by='flow density', ascending=False).head(10))
    print('RJ')
    dftmp = dfRJ[['tgt', 'tgtname', 'tgtpop']].drop_duplicates()
    dfsum = dfRJ[['tgt', 'tgtname', 'flow']].groupby(['tgt'], as_index=False).agg(sum)[['tgt','flow']]
    dftmp = pd.merge(dftmp, dfsum, on=['tgt'])
    dftmp['flow density'] = dftmp['flow'].div(dftmp['tgtpop'])
    print(dftmp.sort_values(by='flow', ascending=False).head(10))
    print(dftmp.sort_values(by='flow density', ascending=False).head(10))
    print('PR')
    dftmp = dfPR[['tgt', 'tgtname', 'tgtpop']].drop_duplicates()
    dfsum = dfPR[['tgt', 'tgtname', 'flow']].groupby(['tgt'], as_index=False).agg(sum)[['tgt','flow']]
    dftmp = pd.merge(dftmp, dfsum, on=['tgt'])
    dftmp['flow density'] = dftmp['flow'].div(dftmp['tgtpop'])
    print(dftmp.sort_values(by='flow', ascending=False).head(10))
    print(dftmp.sort_values(by='flow density', ascending=False).head(10))


    hval, xval = extracthisto(dfBR, 'flow')
    plt.plot(xval, hval, label='BR')
    hval, xval = extracthisto(dfSP, 'flow')
    plt.plot(xval, hval, label='SP')
    hval, xval = extracthisto(dfRJ, 'flow')
    plt.plot(xval, hval, label='RJ')
    hval, xval = extracthisto(dfPR, 'flow')
    plt.plot(xval, hval, label='PR')

    plt.xscale('log')
    plt.yscale('log')
    plt.ylabel('Distribuição acumulada', fontproperties=fontproplbl)
    plt.xlabel('Fij', fontproperties=fontproplbl)
    plt.title('Fluxo por conexão', fontproperties=fontproplbl)
    ax = plt.gca()
    for label in ax.get_xticklabels():
        label.set_fontproperties(fontpropticks)
    for label in ax.get_yticklabels():
        label.set_fontproperties(fontpropticks)
    ax.legend(prop=fontproplgd, loc='lower left')
    plt.tight_layout()
    plt.savefig('histo-Fij.png', facecolor=(0,0,0,0))
    plt.clf()

    dftmp = dfBR[['src','Ti']].drop_duplicates()
    hval, xval = extracthisto(dftmp, 'Ti')
    plt.plot(xval, hval, label='BR')

    dftmp = dfSP[['src','Ti']].drop_duplicates()
    hval, xval = extracthisto(dftmp, 'Ti')
    plt.plot(xval, hval, label='SP')

    dftmp = dfRJ[['src','Ti']].drop_duplicates()
    hval, xval = extracthisto(dftmp, 'Ti')
    plt.plot(xval, hval, label='RJ')

    dftmp = dfPR[['src','Ti']].drop_duplicates()
    hval, xval = extracthisto(dftmp, 'Ti')
    plt.plot(xval, hval, label='PR')

    plt.xscale('log')
    plt.yscale('log')
    plt.ylabel('Distribuição acumulada', fontproperties=fontproplbl)
    plt.xlabel('Ti', fontproperties=fontproplbl)
    plt.title('População móvel por município', fontproperties=fontproplbl)
    ax = plt.gca()
    for label in ax.get_xticklabels():
        label.set_fontproperties(fontpropticks)
    for label in ax.get_yticklabels():
        label.set_fontproperties(fontpropticks)
    ax.legend(prop=fontproplgd, loc='lower left')
    plt.tight_layout()
    plt.savefig('histo-Ti.png', facecolor=(0,0,0,0))
    plt.clf()


if __name__ == '__main__':
    main()
