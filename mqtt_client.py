import paho.mqtt.client as mqtt
import json
import analisa 
from datetime import datetime
import threading
import os
import tkinter as tk
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
# Configurações do broker MQTT
BROKER_ADDRESS = "{your emqx address}.com"  # Altere para o endereço do seu broker
BROKER_PORT = 8883  # Porta padrão para conexões seguras com TLS
CA_CERTIFICATE = "emqxsl-ca.crt"  # Caminho para o certificado CA
TOPIC_SUBSCRIBE = "/device/#"  # Tópico para assinar (receber mensagens)
TOPIC_PUBLISH = "/saida"  # Tópico para publicar mensagens
# Configurando autenticação
USERNAME = "EMQX_TAGOIO"  # Substitua pelo seu nome de usuário
PASSWORD = "1234"  # Substitua pela sua senha

flag = False
frame_canvas = None
root = None
arquivo_csv = 'dados.csv'

try:
    with open('config.json') as file:
        config_dict = json.load(file)

except Exception as e:
    print(f"Não consegui abrir o config \nErro: {e}")

# Callback chamado quando o cliente se conecta ao broker
def on_connect(client, userdata, flags, reasonCode, properties):
    if reasonCode == 0:
        print("Conectado ao broker com sucesso!")
        client.subscribe(TOPIC_SUBSCRIBE)  # Assina o tópico ao conectar
        print(f"Assinado no tópico: {TOPIC_SUBSCRIBE}")
    else:
        print(f"Falha ao conectar. Código de retorno: {reasonCode}")

# Callback chamado quando uma mensagem é recebida
def on_message(client, userdata, msg):    
    global flag
    msg_conteudo = json.loads(msg.payload.decode())
    msg_topic = msg.topic
    print(f"Mensagem recebida no tópico {msg_topic}: {msg_conteudo}")
    # Responder ou processar a mensagem recebida
    topic = analisa.payload_parser(msg_conteudo)
    if(topic != None):
        atualizar_grafico_thread_safe()
        if(topic == "/ligar"):
            flag = True
        elif(topic == "/desligar"):
            flag = False
        client.publish(topic, "O esp32 tem que receber")
    else:
        client.publish(TOPIC_PUBLISH, "Temperatura não atualizada")
        print(f"Mensagem publicada no tópico {TOPIC_PUBLISH}: Temperatura não atualizada")

# Callback chamado quando uma mensagem é publicada
def on_publish(client, userdata, mid):
    print(f"Mensagem publicada com ID: {mid}")

# Função que cria o cliente MQTT e conecta
def criar_cliente_mqtt():
    client = mqtt.Client(protocol=mqtt.MQTTv5)
    client.username_pw_set(USERNAME, PASSWORD)

    # Configurando TLS
    client.tls_set(CA_CERTIFICATE)

    # Atribuindo callbacks
    client.on_connect = on_connect
    client.on_message = on_message
    client.on_publish = on_publish

    try:
        # Conectando ao broker
        print(f"Conectando ao broker MQTT {BROKER_ADDRESS}:{BROKER_PORT} com TLS...")
        client.connect(BROKER_ADDRESS, BROKER_PORT, 60)

        # Inicia o loop de recebimento de mensagens MQTT
        print("Iniciando loop de mensagens MQTT. Pressione Ctrl+C para sair.")
        client.loop_forever()

    except Exception as e:
        print(f"Erro: {e}")

# Função para rodar o cliente MQTT em uma thread separada
def iniciar_thread_mqtt():
    mqtt_thread = threading.Thread(target=criar_cliente_mqtt)
    mqtt_thread.daemon = True  # Torna o thread daemon, ele será finalizado quando o programa terminar
    mqtt_thread.start()


# Função para encerrar o programa
def on_closing():
    print("Fechando o programa...")
    root.quit()  # Finaliza o loop do Tkinter
    root.destroy()  # Destrói a janela do Tkinter
    print("Acabei de destruir o root")

# Função segura para atualizar o gráfico a partir da thread principal
def atualizar_grafico_thread_safe():
    root.after(0, atualizar_grafico)  # Garante que a atualização ocorrerá na thread principal

def abrir_janela_inserir_valor():
    """Abre uma janela para inserir um valor float."""
    # Cria uma nova janela (Toplevel)
    janela_inserir = tk.Toplevel(root)
    janela_inserir.title("Inserir Valor")
    janela_inserir.geometry("300x200")

    # Label para instrução
    label = tk.Label(janela_inserir, text="Insira um valor (float):")
    label.pack(pady=10)

    # Entry para inserir o valor
    entrada_valor = tk.Entry(janela_inserir)
    entrada_valor.pack(pady=10)

    # Função para processar o valor inserido
    def atualiza_valor():
        novo_valor = entrada_valor.get()
        try:
            # Converte o valor para float
            valor_float = float(novo_valor)
            config_dict["valor"] = valor_float  # Atualiza o dicionário local
            
            # Salva no arquivo config.json
            with open('config.json', 'w') as file:
                json.dump(config_dict, file, indent=4)

            print(f"Valor inserido: {valor_float}")  # Você pode processar o valor aqui
            janela_inserir.destroy()  # Fecha a janela após a confirmação
        except ValueError:
            tk.messagebox.showerror("Erro", "Por favor, insira um número válido.")

    # Botão para confirmar o valor
    botao_confirmar = tk.Button(janela_inserir, text="Confirmar", command=atualiza_valor)
    botao_confirmar.pack(pady=10)
    
    atualizar_grafico()

def atualizar_grafico():
    global flag
    # Limpa o canvas para evitar sobreposição
    for widget in frame_canvas.winfo_children():
        widget.destroy()

    # Carrega o arquivo CSV
    if os.path.isfile(arquivo_csv):
        df = pd.read_csv(arquivo_csv, parse_dates=['data']).tail(24)

        # Cria o gráfico usando matplotlib
        fig, ax = plt.subplots(figsize=(8, 6))        
        # Obter a data atual
        data_atual = datetime.now().date()

        # Filtrar o DataFrame para manter apenas os registros do dia atual
        df_dia_atual = df[df['data'].dt.date == data_atual]
        ax.plot(df_dia_atual["data"], df_dia_atual["valor"], marker="o", label=config_dict["unidade"])
        ax.set_title(config_dict["nome"] + " ao longo do dia: " + str(data_atual))
        # Comentei a legenda do eixo x, pois não da para ver
        #ax.set_xlabel(data_atual)
        ax.set_ylabel(config_dict["unidade"])
        ax.tick_params(axis="x", rotation=45)
        ax.legend()

        # Adiciona o gráfico ao Tkinter usando FigureCanvasTkAgg
        canvas = FigureCanvasTkAgg(fig, master=frame_canvas)
        canvas.draw()
        canvas.get_tk_widget().pack()
        
        cor_quadrado = "green" if flag else "red"
        texto_legenda = "Status: Ligado" if flag else "Status: Desligado"
        
        # Cria um canvas para desenhar o quadrado
        canvas_quadrado = tk.Canvas(frame_canvas, width=150, height=150)
        canvas_quadrado.pack(side=tk.LEFT, padx=10, pady=10)
        # Desenha o quadrado
        canvas_quadrado.create_rectangle(20, 20, 80, 80, fill=cor_quadrado, outline="")

        # Adiciona o texto acima ou ao lado do quadrado
        canvas_quadrado.create_text(70, 100, text=texto_legenda, fill="black", font=("Arial", 12), anchor="n")



def main():
    global root, frame_canvas  # Declarando as variáveis globais

    # Criar a interface Tkinter
    root = tk.Tk()
    root.title("Aplicativo MQTT")
    root.geometry("800x800")

    # Atribui o método on_closing para quando a janela for fechada
    root.protocol("WM_DELETE_WINDOW", on_closing)

    # Frame para o gráfico
    frame_canvas = tk.Frame(root)
    frame_canvas.pack(fill=tk.BOTH, expand=True)

    # Botão para abrir a janela de inserir valor
    botao_inserir_valor = tk.Button(root, text="Inserir Valor", command=abrir_janela_inserir_valor)
    botao_inserir_valor.pack(side=tk.RIGHT, padx=2)

    # Exibir o gráfico pela primeira vez
    atualizar_grafico()

    #Inicia o client_mqtt numa thread seperada
    iniciar_thread_mqtt()

    # Iniciar o loop da interface gráfica
    root.mainloop()


main()
