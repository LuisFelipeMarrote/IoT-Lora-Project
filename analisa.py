import json
import csv
import os
from datetime import datetime

# Nome do arquivo CSV
arquivo_csv = 'dados.csv'
config_dict = None

def atualiza_config():
    global config_dict
    try:
        with open('config.json') as file:
            config_dict = json.load(file)

    except Exception as e:
        print(f"Não consegui abrir o config \nErro: {e}")    




def temperatura_desejada():
    return float(config_dict["valor"])

#Recebe uma lista de dic e itera sobre até achar
def payload_parser(json_list):
    atualiza_config()
    for item in json_list:
        if 'u' in item:
            if (item['u'] == config_dict["unidade"]):
                return decisão(item)
            else:
                return None 

def decisão(item):

    if 'v' not in item:
        return None    

    salvarArquivo(item)
    
    if item['v'] < temperatura_desejada(): 
        return "/ligar"
    else:
        return "/desligar"


def salvarArquivo(item):
    try:
        # Verifica se o cabeçalho já foi escrito no arquivo
        cabeçalho_existe = False
        if os.path.isfile(arquivo_csv):
            with open(arquivo_csv, mode='r') as file:
                # Checa se o cabeçalho já está no arquivo
                primeira_linha = file.readline().strip()
                cabeçalho_existe = primeira_linha == "data,valor,unidade"

        # Abrindo o arquivo no modo append (adicionar novas linhas)
        with open(arquivo_csv, mode='a', newline='') as file:
            writer = csv.DictWriter(file, fieldnames=['data', 'valor', 'unidade'])

            # Escreve o cabeçalho somente se ainda não existir
            if not cabeçalho_existe:
                writer.writeheader()

            # Pegando a data atual
            data_atual = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            # Iterando sobre os dados e extraindo o que é necessário
            if 'v' in item and 'u' in item:
                writer.writerow({
                    'data': data_atual,
                    'valor': item['v'],
                    'unidade': item['u']
                })

    except Exception as e:
        print(f"Não consegui abrir o dados.csv \nErro: {e}")

