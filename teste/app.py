from flask import Flask, render_template, request, redirect, url_for, Response
import paho.mqtt.client as mqtt
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('Agg')
import pandas as pd
import json
import threading
from datetime import datetime
import os
import analisa

app = Flask(__name__)

# Configurações do MQTT
BROKER_ADDRESS = ""  # Altere para o endereço do seu broker
BROKER_PORT = 8883
CA_CERTIFICATE = "emqxsl-ca.crt"
TOPIC_SUBSCRIBE = "/device/#"
TOPIC_PUBLISH = "/saida"
# Configurando autenticação
USERNAME = "EMQX_TAGOIO"  # Substitua pelo seu nome de usuário
PASSWORD = "1234"  # Substitua pela sua senha

# Variáveis globais
flag = False
config_dict = {}
arquivo_csv = 'dados.csv'

# Carregar config.json
try:
    with open('config.json') as file:
        config_dict = json.load(file)
except Exception as e:
    print(f"Erro ao carregar config.json: {e}")

# Função para criar o gráfico
def gerar_grafico():
    if os.path.isfile(arquivo_csv):
        df = pd.read_csv(arquivo_csv, parse_dates=['data']).tail(24)
        data_atual = datetime.now().date()
        df_dia_atual = df[df['data'].dt.date == data_atual]

        plt.figure(figsize=(8, 6))
        plt.plot(df_dia_atual['data'], df_dia_atual['valor'], marker='o', label=config_dict["unidade"])
        plt.title(f"{config_dict['nome']} ao longo do dia: {data_atual}")
        plt.ylabel(config_dict["unidade"])
        plt.xticks(rotation=45)
        plt.legend()
        plt.tight_layout()

        # Salva o gráfico como uma imagem
        plt.savefig('static/graph.png')
        plt.close()

# MQTT Callbacks
def on_connect(client, userdata, flags, reasonCode, properties):
    if reasonCode == 0:
        print("Conectado ao broker!")
        client.subscribe(TOPIC_SUBSCRIBE)
    else:
        print(f"Falha ao conectar: {reasonCode}")

def on_message(client, userdata, msg):
    global flag
    try:
        msg_conteudo = json.loads(msg.payload.decode())
        print(f"Recebido no tópico {msg.topic}: {msg_conteudo}")
        topic = analisa.payload_parser(msg_conteudo)
        # Exemplo simples: liga/desliga baseado no payload
        if topic != None:
            if topic == "/ligar":
                flag = True
            elif topic == "/desligar":
                flag = False
            print("Mandei para o EMQX")
            client.publish(topic, "O esp32 tem que receber")
            # gerar_grafico()
        else:
            client.publish(TOPIC_PUBLISH, "Temperatura não atualizada")
            print(f"Mensagem publicada no tópico {TOPIC_PUBLISH}: Temperatura não atualizada")
    except Exception as e:
        print(f"Erro ao processar mensagem: {e}")

def on_publish(client, userdata, mid):
    print(f"Mensagem publicada com ID: {mid}")

# Função MQTT em thread separada
def iniciar_mqtt():
    client = mqtt.Client(protocol=mqtt.MQTTv5)
    client.username_pw_set(USERNAME, PASSWORD)
    client.tls_set(CA_CERTIFICATE)

    client.on_connect = on_connect
    client.on_message = on_message
    client.on_publish = on_publish

    try:
        client.connect(BROKER_ADDRESS, BROKER_PORT, 60)
        client.loop_forever()
    except Exception as e:
        print(f"Erro MQTT: {e}")

# Rota principal
@app.route("/", methods=["GET", "POST"])
def index():
    global flag

    # Atualiza o valor configurado
    if request.method == "POST":
        valor = request.form.get("valor")
        if valor:
            with open('config.json', 'w') as f:
                config_dict["valor"] = float(valor)
                json.dump(config_dict, f, indent=4)
            gerar_grafico()
            return redirect(url_for("index"))

    # Gera o gráfico ao carregar a página
    gerar_grafico()
    return render_template("index.html", status="Ligado" if flag else "Desligado")
    
@app.route("/update_graph")
def update_graph():
    gerar_grafico()  # Regenera o gráfico sempre que esta rota for acessada
    return redirect(url_for('static', filename='graph.png'))

@app.route('/events')
def events():
    string = f"data: {str(flag).lower()}\n\n"  # Envia o valor de flag (true ou false)
    
    return Response(string, content_type='text/event-stream')

# Inicia o MQTT em uma thread
threading.Thread(target=iniciar_mqtt, daemon=True).start()

# Roda o servidor Flask
if __name__ == "__main__":
    app.run(debug=False)
