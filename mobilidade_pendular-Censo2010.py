#!/usr/bin/env python
# -*- coding: utf-8 -*-

##################################
# Código desenvolvido por 
# Marcelo F C Gomes
# marfcg <at> gmail <dot> com
#
# Implementacao de estrutura de DataFrame com Pandas
##################################

from collections import defaultdict
import numpy as np
import pandas as pd
import sys
import csv


def read_dicionario(fname,var):
    # Leitura do dicionario de posicao das variaveis no arquivo de microdados

    fin = open(fname, 'r')
    fin.next()
    frows = csv.DictReader(fin, delimiter=',')
    
    ponteiros = {key:{} for key in var}
    for row in frows:
        if row['VAR'] in var:
            # Posicoes reduzidas em uma unidade por conta da estrutura
            # posicional do Python, que comeca em 0 e nao em 1
            pi = int(row['POSIÇÃO INICIAL']) - 1
            sint = slice(pi, pi+int(row['INT']))
            if row['DEC'] == '':
                sdec = ''
            else:
                # slice(a,b) vai de a até a posicao b-1
                pf = int(row['POSIÇÃO FINAL'])
                sdec = slice(pf-int(row['DEC']),pf)

            ponteiros[row['VAR']] = {'NOME':row['NOME'],
                                     'FATIA':sint,
                                     'FATIADEC':sdec}
            
    fin.close()
    return ponteiros

##########################################################

def read_municipio():
    # Leitura da tabela de municipios e codigos de deslocamento

    fin = open('data/migracao_e_deslocamento_municipios-2010.csv', 'r')
    fin.next()
    fin.next()

    frows = csv.DictReader(fin, delimiter=',')

    codmun = {}
    for row in frows:
        codmun[row['Código']] = {'Município':row['Municípios'],
                                 'UF':row['Unidades da Federação']}
        
    fin.close()
    return codmun

##########################################################

def read_pais():
    # Leitura da tabela de paises e codigos de deslocamento

    fin = open('data/migracao_e_deslocamento_paises_estrangeiros-2010.csv')
    fin.next()
    fin.next()
    
    frows = csv.DictReader(fin, delimiter=',')

    codpais = {}
    for row in frows:
        codpais[row['CÓDIGOS']] = {'País':row['PAÍSES ESTRANGEIROS'],
                                 'Continente':row['CONTINENTES']}
        
    fin.close()
    return codpais

##########################################################

def read_uf():
    # Leitura da tabela de UFs e codigo de deslocamento

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

def escrever_tabelas(tab3599, tab3605, origdest, codmun, coduf, codpais):
    # Escrever as tabelas relevantes de saida

    # Escrever tab3605 (pessoas com 10 anos ou mais, por ocupacao, local de ocupacao,
    # freq escolar e local de estudo)
    tab3605.to_csv(path_or_buf='tab3605-microdados-df.csv')

    # Escrever tab3599 simples (pessoas com ate 9 anos, por frequencia escolar e local
    # de estudo):
    tab3599.to_csv(path_or_buf='tab3599-microdados-df.csv')

    # Escrever matriz origem-destino por cidade
    fout = open('matriz-mobilidade-microdados.csv', 'w')
    fieldnames = ['origem','destino país', 'destino uf', 'destino município','total']
    csvwriter = csv.DictWriter(fout, delimiter=',', fieldnames = fieldnames)
    csvwriter.writeheader()
    d = {fn:'' for fn in fieldnames}
    for mun in sorted(origdest.keys()):
        d['origem'] = codmun[mun]['Município']
        
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
            if dest_mun not in codmun:
                d['destino município'] = 'Em Branco'
            else:
                d['destino município'] = codmun[dest_mun]['Município']

            d['total'] = peso

            csvwriter.writerow(d)
    fout.close()
            
    return


def main(fdict,fdados):
    
    varlist = {'V0001':'res.uf', #Código UF
               'V0002':'res.mun', #Código Município
               'V0010':'peso', #Peso amostral
               'V6036':'idade', #Idade em anos
               'V0628':'escola', #Frequenta escola ou creche
               'V0636':'escola.local', #Local da escola
               'V6362':'escola.uf', #UF da escola
               'V6364':'escola.mun', #Municipio da escola
               'V6366':'escola.pais', #Pais da escola
               'V0660':'trab.local', #Local de trabalho
               'V6602':'trab.uf', #UF de trabalho
               'V6604':'trab.mun', #Municipio de trabalho
               'V6606':'trab.pais', #Pais de trabalho
               'V0661':'trab.diario', #Retorna do trabalho para casa diariamente
               'V0662':'trab.desloc', #Tempo habitual de deslocamento
               'V6920':'trab.situacao' #Situacao de ocupacao na semana de referencia
               }
    

    # Levanta informacao sobre posicao das variaveis de interesse:
    ponteiros = read_dicionario(fdict,varlist.keys())

    # Altera chaves para simplificar:
    for key, value in varlist.iteritems():
        ponteiros[value] = ponteiros.pop(key)

    # Levanta dicionarios de codigos de localizacao:
    codmun = read_municipio()
    coduf = read_uf()
    codpais = read_pais()

    # Prepara dataframes de interesse:
    trablist = ['total',
                'ocupadas',
                'munres',
                'outromun',
                'outropais',
                'variosmun',
                'naoocupadas']
    dictidades = ['0-4','5-9']
    pop_mun = []
    tab3605 = []
    tab3599 = []
    origdest = {}

    for cod in codmun:

        if cod[0:2] != '33' or cod[2:] == '99999':
            continue

        pop_mun.append({'local':cod,
                        'total':0,
                        'fixa':0,
                        'movel':0})
        
        origdest[cod] = defaultdict(int)

        
        for trab in trablist:
            dicttmp = {'local':cod,
                       'trab':trab,
                       'total':0,
                       'freq':0,
                       'munres':0,
                       'outromun':0,
                       'outropais':0,
                       'naofreq':0}
            tab3605.append(dicttmp)

        for idade in dictidades:
            dicttmp = {'local':cod,
                       'idade':idade,
                       'total':0,
                       'freq':0,
                       'munres':0,
                       'outromun':0,
                       'outropais':0,
                       'naofreq':0}
            tab3599.append(dicttmp)

    del(dicttmp)
    del(trablist)
    del(dictidades)

    tab3599 = pd.DataFrame(tab3599,columns=('local',
                                            'idade',
                                            'total',
                                            'freq',
                                            'munres',
                                            'outromun',
                                            'outropais',
                                            'naofreq'))
    tab3605 = pd.DataFrame(tab3605, columns=('local',
                                             'trab',
                                             'total',
                                             'freq',
                                             'munres',
                                             'outromun',
                                             'outropais',
                                             'naofreq'))
    pop_mun = pd.DataFrame(pop_mun, columns=('local','total','fixa','movel'))

    tagescola = {'1': 'munres', '2': 'outromun', '3': 'outropais'}
    tagtrab = {'1': 'munres', '2': 'munres', '3': 'outromun', '4': 'outropais', '5':'variosmun'}

    fin = open(fdados, 'r')
    for line in fin:

        freqescola = ['naofreq']
        escola_res = True
        escola_uf = ''
        escola_mun = ''
        escola_pais = ''

        freqtrab = ['naoocupada']
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
        pop_mun.total[pop_mun.local==mun] += peso
        
        if idade < 5:
            idadelbl = '0-4'
            tab3599.total[(tab3599.local==mun) & (tab3599.idade==idadelbl)] += peso
            menor = True
        elif idade < 10:
            idadelbl = '5-9'
            tab3599.total[(tab3599.local==mun) & (tab3599.idade==idadelbl)] += peso
            menor = True
        else:
            tab3605.total[(tab3605.local==mun) & (tab3605.trab=='total')] += peso
            menor = False

        # Verifica se frequenta escola:
        if int(line[ponteiros['escola']['FATIA']]) < 3:
            freqescola = ['freq']

        escola = line[ponteiros['escola.local']['FATIA']].strip()
        if escola != '': # Se nao frequenta, esta variavel esta em branco
            freqescola.append(tagescola[escola])
            escola = int(escola)

            if escola >= 2: # Fora do municipio
                escola_res = False
                escola_uf = line[ponteiros['escola.uf']['FATIA']]
                escola_mun = line[ponteiros['escola.mun']['FATIA']]
                escola_pais = line[ponteiros['escola.pais']['FATIA']]
                escola_dest = escola_pais + escola_uf + escola_mun

        # Verifica se trabalha:
        if line[ponteiros['trab.situacao']['FATIA']] == '1':
            freqtrab = ['ocupadas']

        trab = line[ponteiros['trab.local']['FATIA']].strip()
        
        if trab != '':
            freqtrab.append(tagtrab[trab])
            trab = int(trab)
            
            if trab > 2: # Fora do municipio
                trab_res = False
                trab_uf = line[ponteiros['trab.uf']['FATIA']]
                trab_mun = line[ponteiros['trab.mun']['FATIA']]
                trab_pais = line[ponteiros['trab.pais']['FATIA']]
                trab_dest = trab_pais + trab_uf + trab_mun

        # Incrementa os valores das tabelas:

        # Destino:
        if trab_res or escola_res:
            pop_mun.fixa[pop_mun.local==mun] += peso
        else:
            pop_mun.movel[pop_mun.local==mun] += peso

            if not trab_res:
                origdest[mun][trab_dest] += peso
            else:
                origdest[mun][escola_dest] += peso

        # Mobilidade para trabalho e/ou estudo:
        if menor:
            tab3599.loc[(tab3599.local==mun) & (tab3599.idade==idadelbl), freqescola] += peso
        else:
            freqescola.append('total')
            freqtrab.append('total')
            tab3605.loc[(tab3605.local==mun) & (tab3605.trab.isin(freqtrab)), freqescola] += peso
                

    escrever_tabelas(tab3599, tab3605, origdest, codmun, coduf, codpais)

    
if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2])
