#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Script para extração da matriz de mobilidade a partir
dos microdados do Censo 2010.

Arquivos necessários:
./data/migracao_e_deslocamento_municipios-2010.csv
./data/migracao_e_deslocamento_unidades_da_federacao-2010.csv
./data/migracao_e_deslocamento_paises_estrangeiros-2010.csv
./data/Layout_microdados_Amosra-pessoa.csv

Dados de entrada:
Caminho para o arquivo com os microdados de pessoas

Uso:
python mobilidade_pendular-Censo2010.py <caminho para microdados>

Ex.:
python mobilidade_pendular-Censo2010.py data/Amostra_Pessoas_33.txt

Saida:
./data/tab3605-microdados.csv  - Tabela similar àquela obtida no SIDRA
./data/tab3599-microdados.csv  - Tabela similar àquela obtida no SIDRA
./data/matriz-mobilidade-microdados.csv  - Matriz de mobilidade

Código desenvolvido por 
Marcelo F C Gomes
marfcg <at> gmail <dot> com
"""

from collections import defaultdict
import numpy as np
import sys
import csv
import zipfile

def read_dicionario(var):
    """
    Leitura do dicionario de posicao das variaveis no arquivo de microdados
    :param fname:
    :param var:
    :return:
    """

    fin = open('data/Layout_microdados_Amostra-pessoa.csv', 'r')
    fin.next()
    frows = csv.DictReader(fin, delimiter=',')

    ponteiros = {key: {} for key in var}
    for row in frows:
        if row['VAR'] in var:
            # Posicoes reduzidas em uma unidade por conta da estrutura
            # posicional do Python, que comeca em 0 e nao em 1
            pi = int(row['POSIÇÃO INICIAL']) - 1
            sint = slice(pi, pi + int(row['INT']))
            if row['DEC'] == '':
                sdec = ''
            else:
                # slice(a,b) vai de a até a posicao b-1
                pf = int(row['POSIÇÃO FINAL'])
                sdec = slice(pf - int(row['DEC']), pf)

            ponteiros[row['VAR']] = {'NOME': row['NOME'],
                                     'FATIA': sint,
                                     'FATIADEC': sdec}

    fin.close()
    return ponteiros


##########################################################

def read_municipio():
    """
    Leitura da tabela de municipios e codigos de deslocamento
    :return:
    """

    fin = open('data/migracao_e_deslocamento_municipios-2010.csv', 'r')
    fin.next()
    fin.next()

    frows = csv.DictReader(fin, delimiter=',')

    codmun = {}
    for row in frows:
        codmun[row['Código']] = {'Município': row['Municípios'],
                                 'UF': row['Unidades da Federação']}

    fin.close()

    fin = open('data/Brazil-municipalities-2010.csv', 'r')

    frows = csv.DictReader(fin, delimiter=',')

    geocodm = {}
    for row in frows:
        geocodm[row['CD_GEOCODM']] = {'Município': row['NM_MUNICIP'],
                                 'UF': row['SIGLA_ESTADO']}

    fin.close()
    return codmun, geocodm


##########################################################

def read_pais():
    """
    Leitura da tabela de paises e codigos de deslocamento
    :return:
    """
    fin = open('data/migracao_e_deslocamento_paises_estrangeiros-2010.csv')
    fin.next()
    fin.next()

    frows = csv.DictReader(fin, delimiter=',')

    codpais = {}
    for row in frows:
        codpais[row['CÓDIGOS']] = {'País': row['PAÍSES ESTRANGEIROS'],
                                   'Continente': row['CONTINENTES']}

    fin.close()
    return codpais


##########################################################

def read_uf():
    """
    Leitura da tabela de UFs e codigo de deslocamento
    :return:
    """

    fin = open('data/migracao_e_deslocamento_unidades_da_federacao-2010.csv')
    fin.next()
    fin.next()

    frows = csv.DictReader(fin, delimiter=',')

    coduf = {}
    for row in frows:
        coduf[row['CÓDIGOS']] = row['UNIDADES DA FEDERAÇÃO']

    fin.close()
    return coduf


##########################################################

def escrever_tabelas(tab3599, tab3605, origdest, geocodm, codmun, coduf,
                     codpais, pref):
    """
    Escrever as tabelas relevantes de saida

    Escreve a tab3605 (pessoas com 10 anos ou mais, por ocupacao, local de ocupacao,
    frequencia escolar e local de estudo), tab3599 (pessoas menores de 10 anos, 
    por frequencia escolar e local de estudo) e matriz de deslocamento.

    :param tab3599:  dict with data on mobility for education, for people 
                     below 10yo
    :param tab3605:  dict with data on mobility for education and work,
                     for people with 10yo or more
    :param origdest:  dict with aggregated mobility flow by city
    :param geocodm:  dict with codes for every municipality
    :param codmun:  dict with mobility code for municipalities
    :param coduf:  dict with mobility code for states
    :param codpais:  dict with mobility code for countries
    :param pref:  preffix for output files
    :return:
    """

    # Escreve a tab3605 (pessoas com 10 anos ou mais, por ocupacao, local de ocupacao,
    # frequencia escolar e local de estudo):
    fout = open('data/%s-tab3605-microdados.csv' % (pref), 'w')
    fieldnames = ['local', 'trab', 'total', 'freq', 'munres', 'outromun', 'outropais', 'naofreq']
    csvwriter = csv.DictWriter(fout, delimiter=',', fieldnames=fieldnames)
    csvwriter.writeheader()
    d = {fn: '' for fn in fieldnames}

    for mun in sorted(tab3605.keys()):
        d['local'] = geocodm[mun]['Município']
        for trabfn in tab3605[mun].keys():
            d['trab'] = trabfn
            d.update((k, round(v)) for k, v in tab3605[mun][trabfn].items())
            csvwriter.writerow(d)
    fout.close()

    # Escrever tab3599 simples (pessoas com ate 9 anos, por frequencia escolar e local
    # de estudo):
    fout = open('data/%s-tab3599-microdados.csv' % (pref), 'w')
    fieldnames = ['local', 'idade', 'total', 'freq', 'munres', 'outromun', 'outropais', 'naofreq']
    csvwriter = csv.DictWriter(fout, delimiter=',', fieldnames=fieldnames)
    csvwriter.writeheader()
    d = {fn: '' for fn in fieldnames}

    for mun in sorted(tab3599.keys()):
        d['local'] = geocodm[mun]['Município']
        for idade in tab3599[mun].keys():
            d['idade'] = idade
            d.update((k, round(v)) for k, v in tab3599[mun][idade].items())
            csvwriter.writerow(d)
    fout.close()

    # Escrever matriz origem-destino por cidade
    fout = open('data/%s-matriz-mobilidade-microdados.csv' % (pref), 'w')
    fieldnames = ['origem', 'destino país', 'destino uf', 'destino município', 'total']
    csvwriter = csv.DictWriter(fout, delimiter=',', fieldnames=fieldnames)
    csvwriter.writeheader()
    d = {fn: '' for fn in fieldnames}
    for mun in sorted(origdest.keys()):
        d['origem'] = geocodm[mun]['Município']

        for dest, peso in sorted(origdest[mun].items()):
            dest_pais = dest[0:7]
            dest_uf = dest[7:14]
            dest_mun = dest[14:21]

            if dest_pais not in codpais:
                d['destino país'] = 'Em Branco'
            else:
                d['destino país'] = codpais[dest_pais]['País']
            if dest_uf not in coduf:
                d['destino uf'] = 'Em Branco'
            else:
                d['destino uf'] = coduf[dest_uf]
                
            # codmun table from IBGE does not have all municipalities
            # but have special descriptors for missing data
            # If the code does represent a municipality, it matches
            # the entry in geocodm.
            if dest_mun not in geocodm:
                if dest_mun in codmun: 
                    d['destino município'] = codmun[dest_mun]['Município']
                else:
                    d['destino município'] = 'Em Branco'
            else:
                d['destino município'] = geocodm[dest_mun]['Município']

            d['total'] = round(peso)

            csvwriter.writerow(d)
    fout.close()

    return


def main(fdados):
    """
    Faz a leitura do arquivo dos microdados e extrai dados de mobilidade
    Dados de entrada
    :param fdados:  # Caminho para o microdado relativo às pessoas
                    # Amostra_Pessoas_<#UF>.txt
    :return:
    """
    varlist = {'V0001': 'res.uf',  # Código UF
               'V0002': 'res.mun',  # Código Município
               'V0010': 'peso',  # Peso amostral
               'V6036': 'idade',  # Idade em anos
               'V0628': 'escola',  # Frequenta escola ou creche
               'V0636': 'escola.local',  # Local da escola
               'V6362': 'escola.uf',  # UF da escola
               'V6364': 'escola.mun',  # Municipio da escola
               'V6366': 'escola.pais',  # Pais da escola
               'V0660': 'trab.local',  # Local de trabalho
               'V6602': 'trab.uf',  # UF de trabalho
               'V6604': 'trab.mun',  # Municipio de trabalho
               'V6606': 'trab.pais',  # Pais de trabalho
               'V0661': 'trab.diario',  # Retorna do trabalho para casa diariamente
               'V0662': 'trab.desloc',  # Tempo habitual de deslocamento
               'V6920': 'trab.situacao'  # Situacao de ocupacao na semana de referencia
               }


    # Levanta informacao sobre posicao das variaveis de interesse:
    ponteiros = read_dicionario(varlist.keys())

    # Altera chaves para simplificar:
    for key, value in varlist.iteritems():
        ponteiros[value] = ponteiros.pop(key)

    # Levanta dicionarios de codigos de localizacao:
    codmun, geocodm = read_municipio()
    coduf = read_uf()
    codpais = read_pais()

    # Prepara dicionarios de interesse:
    pop_mun = {}
    origdest = {}
    tab3605 = {}
    tab3599 = {}

    if fdados.split('.')[-1] == 'zip':
        pref = fdados.split('/')[-1].split('.')[0]
    else:
        pref = fdados.split('/')[-1].split('.')[0].split('Amostra_Pessoas_')[-1]

    for cod in geocodm:
        if geocodm[cod]['UF'] != pref[0:2] and cod[0:2] != pref:
            continue
            
        pop_mun[cod] = {'total': 0,
                        'fixa': 0,
                        'movel': 0}

        origdest[cod] = defaultdict(int)

        tab3605[cod] = {'total': {},
                        'ocupadas': {},
                        'munres': {},
                        'munresdom': {},
                        'munresfora': {},
                        'outromun': {},
                        'outropais': {},
                        'variosmun': {},
                        'naoocupadas': {}}

        for key in tab3605[cod]:
            tab3605[cod][key] = {'total': 0,
                                 'freq': 0,
                                 'munres': 0,
                                 'outromun': 0,
                                 'outropais': 0,
                                 'naofreq': 0}

        tab3599[cod] = {'total': {},
                        '0-4': {},
                        '5-9': {}}

        for key in tab3599[cod]:
            tab3599[cod][key] = {'total': 0,
                                 'freq': 0,
                                 'munres': 0,
                                 'outromun': 0,
                                 'outropais': 0,
                                 'naofreq': 0}

    tagescola = {'1': 'munres', '2': 'outromun', '3': 'outropais'}
    tagtrab = {'1': 'munres', '2': 'munres', '3': 'outromun', '4': 'outropais', '5': 'variosmun'}

    
    # Check wether the input is a zip file.
    # If so, assumes that it is the regular state microdata from IBGE
    # and crawls to the necessary file inside it
    
    if fdados.split('.')[-1] == "zip":
        fzip = zipfile.ZipFile(fdados, 'r')
        for fname in fzip.namelist():
            if pref+"/Pessoas/Amostra_Pessoas_" in fname:
                fin = fzip.open(fname)
                break
    else:
        fin = open(fdados, 'r')

    for line in fin:

        freqescola = False
        escola_res = True
        escola_uf = ''
        escola_mun = ''
        escola_pais = ''

        freqtrab = False
        trab_res = True
        trab_uf = ''
        trab_mun = ''
        trab_pais = ''

        # Idade (em anos):
        idade = int(line[ponteiros['idade']['FATIA']])

        # Codigo do municipio de residencia:
        mun = (line[ponteiros['res.uf']['FATIA']] +
               line[ponteiros['res.mun']['FATIA']])

        # Peso individual:
        peso = np.double(line[ponteiros['peso']['FATIA']] +
                         '.' +
                         line[ponteiros['peso']['FATIADEC']])

        # Populacao total do municipio:
        pop_mun[mun]['total'] += peso

        if idade < 5:
            tab3599[mun]['total']['total'] += peso
            tab3599[mun]['0-4']['total'] += peso
            menor = True
            idadelabel = '0-4'
        elif idade < 10:
            tab3599[mun]['total']['total'] += peso
            tab3599[mun]['5-9']['total'] += peso
            menor = True
            idadelabel = '5-9'
        else:
            tab3605[mun]['total']['total'] += peso
            menor = False

        # Verifica se frequenta escola:
        if int(line[ponteiros['escola']['FATIA']]) < 3:
            freqescola = True

        escola = line[ponteiros['escola.local']['FATIA']].strip()
        if escola != '':  # Se nao frequenta, esta variavel esta em branco
            escolalabel = tagescola[escola]
            escola = int(escola)

            if escola >= 2:  # Fora do municipio
                escola_res = False
                escola_uf = line[ponteiros['escola.uf']['FATIA']]
                escola_mun = line[ponteiros['escola.mun']['FATIA']]
                escola_pais = line[ponteiros['escola.pais']['FATIA']]
                escola_dest = escola_pais + escola_uf + escola_mun

        # Verifica se trabalha:
        if line[ponteiros['trab.situacao']['FATIA']] == '1':
            freqtrab = True

        trab = line[ponteiros['trab.local']['FATIA']].strip()

        if trab != '':
            trablabel = tagtrab[trab]
            trab = int(trab)

            if trab > 2:  # Fora do municipio
                trab_res = False
                trab_uf = line[ponteiros['trab.uf']['FATIA']]
                trab_mun = line[ponteiros['trab.mun']['FATIA']]
                trab_pais = line[ponteiros['trab.pais']['FATIA']]
                trab_dest = trab_pais + trab_uf + trab_mun

        # Incrementa os valores das tabelas:

        # Destino:
        if trab_res or escola_res:
            pop_mun[mun]['fixa'] += peso
        else:
            pop_mun[mun]['movel'] += peso

            if not trab_res:
                origdest[mun][trab_dest] += peso
            else:
                origdest[mun][escola_dest] += peso

        # Mobilidade para trabalho e/ou estudo:
        if menor:
            if freqescola:
                tab3599[mun]['total']['freq'] += peso
                tab3599[mun][idadelabel]['freq'] += peso
                tab3599[mun]['total'][escolalabel] += peso
                tab3599[mun][idadelabel][escolalabel] += peso
            else:
                tab3599[mun]['total']['naofreq'] += peso
                tab3599[mun][idadelabel]['naofreq'] += peso
        else:
            if freqescola:
                tab3605[mun]['total']['freq'] += peso
            else:
                tab3605[mun]['total']['naofreq'] += peso

            if freqtrab:
                tab3605[mun]['ocupadas']['total'] += peso
                tab3605[mun][trablabel]['total'] += peso
                if freqescola:
                    tab3605[mun]['total'][escolalabel] += peso
                    tab3605[mun]['ocupadas']['freq'] += peso
                    tab3605[mun]['ocupadas'][escolalabel] += peso
                    tab3605[mun][trablabel]['freq'] += peso
                    tab3605[mun][trablabel][escolalabel] += peso
                else:
                    tab3605[mun]['ocupadas']['naofreq'] += peso
                    tab3605[mun][trablabel]['naofreq'] += peso
            else:
                tab3605[mun]['naoocupadas']['total'] += peso
                if freqescola:
                    tab3605[mun]['total'][escolalabel] += peso
                    tab3605[mun]['naoocupadas']['freq'] += peso
                    tab3605[mun]['naoocupadas'][escolalabel] += peso
                else:
                    tab3605[mun]['naoocupadas']['naofreq'] += peso

    escrever_tabelas(tab3599, tab3605, origdest, geocodm, codmun, coduf,
                     codpais, pref)


if __name__ == '__main__':
    main(sys.argv[1])
