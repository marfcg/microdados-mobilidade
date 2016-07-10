import argparse
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
from matplotlib.colors import LogNorm
from argparse import RawDescriptionHelpFormatter

__author__ = 'Marcelo Ferreira da Costa Gomes'


# Set font propoerties
fontproplgd = fm.FontProperties('Oswald')
fontproplgd.set_size(28)
fontproplbl = fm.FontProperties('Oswald')
fontproplbl.set_size(24)
fontpropticks = fm.FontProperties('Oswald')
fontpropticks.set_size(18)


def plotfig(df, xcol, ycol, title=None, xlbl=None, ylbl=None):
    # Create identity line based with min, max based on data:
    x = [xi for xi in range(int(df[xcol].min()), int(df[xcol].max()), 100)]

    df.plot.hexbin(x=xcol, y=ycol, xscale='log', yscale='log', norm=LogNorm())
    plt.plot(x, x, color='red')
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

    plt.tight_layout()
    plt.savefig('%s-%s-%s.svg' % (title.replace(' ','_'), xcol, ycol), dpi=200)

    return


def main(fname, title=None):

    df = pd.read_csv(fname)
    plotfig(df, xcol='flow', ycol='grav', title=title, xlbl='Dados do Censo 2010',
            ylbl='Modelo gravitacional simples')
    plotfig(df, xcol='flow', ycol='rad', title=title, xlbl='Dados do Censo 2010',
            ylbl='Modelo de radiação')
    plotfig(df, xcol='grav', ycol='rad', title=title, xlbl='Modelo gravitacional simples',
            ylbl='Modelo de radiação')


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
