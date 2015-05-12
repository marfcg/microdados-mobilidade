# microdados-mobilidade
Extração de dados de mobilidade a partir dos microdados do Censo 2010

Algumas observações importantes:

- Para fins de cálculo de fluxo de mobilidade, deslocamento para estudo ou trabalho são considerados equivalentes, salvo quando há ocorrência de ambos;
- Nos casos em que há tanto mobilidade para estudo quanto para trabalho, optou-se pelo destino do trabalho;
- Há casos de pessoas que relatam mobilidade porém sem informação sobre seu destino. Tais ocorrências podem possuir mais de um marcador na tabela final (ex.: "Em branco" ou "IGNORADO").

Este ramo armazena os dados de entrada em um dataframe, ao invés de dicionário aninhado.
Extremamente lento em comparação com a versão original.
