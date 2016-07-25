import argparse
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


# Set font propoerties
fontproplgd = fm.FontProperties('Oswald')
fontproplgd.set_size(12)
fontproplbl = fm.FontProperties('Oswald')
fontproplbl.set_size(24)
fontpropticks = fm.FontProperties('Oswald')
fontpropticks.set_size(18)


def plotfig(df, xcol, ycol, title=None, xlbl=None, ylbl=None, fit=None):
    # Create identity line based with min, max based on data:
    x = [xi for xi in range(int(df[xcol].min()), int(df[xcol].max()), 100)]

    df.plot.hexbin(x=xcol, y=ycol, xscale='log', yscale='log', norm=LogNorm())
    plt.xscale('log')
    plt.yscale('log')
    plt.xlim([min(x), max(x)])
    ax = plt.gca()
    for label in ax.get_xticklabels():
        label.set_fontproperties(fontpropticks)
    for label in ax.get_yticklabels():
        label.set_fontproperties(fontpropticks)

    if title:
        plt.title(title, fontproperties=fontproplbl)
    if xlbl:
        plt.xlabel(xlbl, fontproperties=fontproplbl)
    if xlbl:
        plt.ylabel(ylbl, fontproperties=fontproplbl)

    if fit == 'direct':
        plt.plot(x, x, color='red')
        r, p = pearsonr(df[xcol], df[ycol])
        rmsd = np.sqrt(((df[xcol] - df[ycol]) ** 2).sum() / len(df))
    elif fit == 'ols':
        est = sm.OLS(df[ycol], df[xcol]).fit()
        slope = est.params[0]
        print(slope)
        y = [float(slope)*xi for xi in x]
        plt.plot(x, y, color='red', label='y = %.2f x' % slope)
        ax.legend(prop=fontproplgd, loc='upper left')
        r, p = pearsonr(slope*df[xcol], df[ycol])
        rmsd = np.sqrt(((slope*df[xcol] - df[ycol]) ** 2).sum() / len(df))

    if p < 0.01:
        plt.text(0.99, .01, 'RMSD = %.2f\nr = %.2f\np < 0.01' % (rmsd, r), fontproperties=fontproplgd,
                 transform=ax.transAxes, va='bottom', ha='right')
    else:
        plt.text(0.99, .01, 'RMSD = %.2f\nr = %.2f\np > 0.10' % (rmsd, r), fontproperties=fontproplgd,
                 transform=ax.transAxes, va='bottom', ha='right')

    plt.tight_layout()
    plt.savefig('%s-%s-%s.png' % (title.replace(' ','_'), xcol, ycol), dpi=200, facecolor=(0,0,0,0))

    return


def plothisto(df, title):
    minflow = df['flow'].min()
    maxflow = df['flow'].max()
    xbin = np.logspace(np.log10(minflow), np.log10(maxflow), 500)
    xhist, hbin = np.histogram(df['flow'], density=True, bins=xbin)
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
    plt.plot(xval, hval)
    plt.xscale('log')
    plt.yscale('log')
    plt.ylabel('Distribuição acumulada', fontproperties=fontproplbl)
    plt.xlabel('Fij', fontproperties=fontproplbl)
    plt.title(title, fontproperties=fontproplbl)
    ax = plt.gca()
    for label in ax.get_xticklabels():
        label.set_fontproperties(fontpropticks)
    for label in ax.get_yticklabels():
        label.set_fontproperties(fontpropticks)
    plt.tight_layout()
    plt.savefig('%s-histo-Fij.png' % title.replace(' ', '_'), facecolor=(0,0,0,0))
    plt.clf()

    dftmp = df[['src','Ti']].drop_duplicates()
    minti = dftmp['Ti'].min()
    maxti = dftmp['Ti'].max()
    xbin = np.logspace(np.log10(minti), np.log10(maxti), 500)
    xhist, hbin = np.histogram(dftmp['Ti'], density=True, bins=xbin)
    hval = [1.0]
    hold = 1
    xval = [minti]
    for i, v in enumerate(xhist):
        if v > 0:
            w = hbin[i+1] - hbin[i]
            hval.append(hold-v*w)
            xval.append(hbin[i+1])
            hold = hval[-1]

    print(hval[-2:])
    hval = hval[0:-1]
    xval = xval[0:-1]
    plt.plot(xval, hval)
    plt.xscale('log')
    plt.yscale('log')
    plt.ylabel('Distribuição acumulada', fontproperties=fontproplbl)
    plt.xlabel('Ti', fontproperties=fontproplbl)
    plt.title(title, fontproperties=fontproplbl)
    ax = plt.gca()
    for label in ax.get_xticklabels():
        label.set_fontproperties(fontpropticks)
    for label in ax.get_yticklabels():
        label.set_fontproperties(fontpropticks)
    plt.tight_layout()
    plt.savefig('%s-histo-Ti.png' % title.replace(' ','_'), facecolor=(0,0,0,0))
    plt.clf()


    mindist = df['dist'].min()
    maxdist = df['dist'].max()
    yhist, ybin = np.histogram(df['dist'], bins=[x for x in range(0,int(round(maxdist)+20),20)])
    plt.hist(df['dist'], normed=True, bins=ybin)
    ax = plt.gca()
    for label in ax.get_xticklabels():
        label.set_fontproperties(fontpropticks)
    for label in ax.get_yticklabels():
        label.set_fontproperties(fontpropticks)
    plt.xlim([0,1000])
    plt.ylabel('PDF', fontproperties=fontproplbl)
    plt.xlabel('Distância (km)', fontproperties=fontproplbl)
    plt.title(title, fontproperties=fontproplbl)
    plt.tight_layout()
    plt.savefig('%s-histo-distância.png' % title.replace(' ','_'), facecolor=(0,0,0,0))
    plt.clf()

    return



def main(fname, title=None):

    df = pd.read_csv(fname)

    dfsum = df[['src', 'srcpop', 'Ti']].drop_duplicates()
    plothisto(df[['src', 'flow', 'Ti', 'dist']], title)

    sns.set(rc={'axes.facecolor': 'white'})
    plotfig(dfsum, xcol='srcpop', ycol='Ti', title=title, xlbl='População de origem', ylbl='População móvel', fit='ols')
    plotfig(df, xcol='flow', ycol='grav', title=title, xlbl='Dados do Censo 2010',
            ylbl='Modelo gravitacional simples', fit='direct')
    plotfig(df, xcol='flow', ycol='rad', title=title, xlbl='Dados do Censo 2010',
            ylbl='Modelo de radiação', fit='direct')
    plotfig(df, xcol='grav', ycol='rad', title=title, xlbl='Modelo gravitacional simples',
            ylbl='Modelo de radiação', fit='direct')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Print Gravitational and Radiation Models flow estimate' +
                                                 ' and compare to real flow given.\n',
                                     formatter_class=RawDescriptionHelpFormatter)
    parser.add_argument('--path', help='Path to mobility matrix file',
                    default='../data/all_FUs-redistributed_mobility_matrix.csv')
    parser.add_argument('--title', help='Plot title')
    args = parser.parse_args()

    print(args)
    main(args.path, args.title)
