###################################################
# Construcao da matriz de distancias com base
# nos dados de localizacao geografica dos centroides
#
# Uso:
# python matriz-distancia.py <nome do arquivo com os dados>
# Ex.:
# python matriz-distancia.py centroides-lista.csv
#
###################################################

#!/usr/bin/env python
# -*- coding: utf-8 -*-
from pyproj import Geod
from collections import defaultdict
import csv
import sys

def readdata(fname):

    fin = csv.DictReader(open(fname, 'r'), delimiter=',')
    data_table = defaultdict(dict)
    for row in fin:
        name = row['CD_GEOCODM']
        data_table[name]['lon'] = row['X']
        data_table[name]['lat'] = row['Y']
        data_table[name]['name'] = row['NM_MUNICIP']

    return data_table

#############################################

def main(fname):
    
    # Define o sistema de coordenadas:
    coord = Geod(ellps='WGS84')

    # Le a tabela de dados com lat, lon e nome:
    points = readdata(fname)
    print(len(points))

    # Define arquivo de saida:
    foutname = '.'.join(fname.split('.')[:-1])+'-distancias.csv'
    fout = open(foutname, 'w')
    fout.write('Source geocode,Source name,Target geocode,Target name,Distance(km)\n')

    # Calcula matriz de distancia e salva:
    namelist = sorted(points.keys())
    print(len(namelist))
    count = 0
    for src in namelist[:-1]:
        src_lat = points[src]['lat']
        src_lon = points[src]['lon']
        src_lbl = points[src]['name']
        count += 1

        for tgt in namelist[count:]:
            tgt_lat = points[tgt]['lat']
            tgt_lon = points[tgt]['lon']
            tgt_lbl = points[tgt]['name']
            
            az1, az2, d = coord.inv(src_lon,src_lat,tgt_lon,tgt_lat)

            fout.write('%s,%s,%s,%s,%s\n' % (src, src_lbl, tgt, tgt_lbl, d/1000))
        print(count)

if __name__ == '__main__':
    main(sys.argv[1])
