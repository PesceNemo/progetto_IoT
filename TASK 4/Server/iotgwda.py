#importazione librerie
import socket #per la gestione delle socket
import time #per la gestione del tempo
import json #per gestire i file json
import cripto #per la gestione della crittografia
import threading #per la gestione dei thread (devono potersi connettere piu dc contemporaneamente)
import paho.mqtt.client as mqtt #per la gestione del protocollo MQTT

#leggo i parametri presenti nel file: parametri.json
with open("configurazione/parametri.json", "r") as file:
    parametri = json.load(file)

TEMPO_RILEVAZIONE = parametri["TEMPO_RILEVAZIONE"]
TEMPO_INVIO = parametri["TEMPO_INVIO"] 
NUMERO_DECIMALI = parametri["NUMERO_DECIMALI"]
IP_SERVER = parametri["IP_SERVER"]
PORTA_SERVER = parametri["PORTA_SERVER"]
TOPIC = parametri["TOPIC"]               
BROKER = parametri["BROKER"]            
PORTA_BROKER = parametri["PORTA_BROKER"] 

#Configurazione e connessione MQTT (Message Queue Telemetry Transport)
client_mqtt = mqtt.Client() #creazione del client MQTT
client_mqtt.connect(BROKER, PORTA_BROKER) #connessione al broker MQTT da parte de client
client_mqtt.loop_start() #avvia il loop in background per MQTT

#funzione per gestire la connessione con il client 
def gestione_client(client, indirizzo):
    #invio al DC il tempo di rilevazione
    client.send(str(parametri["TEMPO_RILEVAZIONE"]).encode())   

    #dichiarazione e inizializzazione variabili
    temperature = []
    umidita = []
    invio_numero = 0
    inizio = time.time() 

    try:
        #finchè la connessione è attiva, ricevo dati
        while True:
            #DEBUG richiesto come da specifiche di progetto
            print("Gateway IoT in attesa di dati") 
            
            #ricevo i dati dal client
            dato = client.recv(1024).decode()
            #se la connessione viene chiusa, esco dal ciclo
            if not dato:
                break

            #decriptazione del dato ricevuto
            dato_json = cripto.decriptazione(dato)
            dato = json.loads(dato_json)

            #aggiungo i dati ricevuti agli array
            temperature.append(dato["osservazione"]["temperatura"])
            umidita.append(dato["osservazione"]["umidita"])

            #controllo il tempo di invio
            if time.time() - inizio >= TEMPO_INVIO:
                #incremento il numeo di invii
                invio_numero = invio_numero + 1 

                #calcolo la media delle temperature e delle umidità
                media_t = round(sum(temperature) / len(temperature), NUMERO_DECIMALI)
                media_u = round(sum(umidita) / len(umidita), NUMERO_DECIMALI)

                #calcolo la data e ora della rilevazione
                rilevazione_data_ora = time.time()

                #creo il dizionario da inviare alla platform
                dato_iot = {
                    "invio_numero": invio_numero,
                    "identita_giot": parametri.get("IDENTITA_GIOT", parametri.get("ID_GIOT")),
                    "cabina": dato["cabina"],
                    "ponte": dato["ponte"],
                    "data_ora": rilevazione_data_ora,
                    "media_temperatura": media_t,
                    "media_umidita": media_u,
                    "dc": dato["identita"],
                }

                #crittografia del dato
                dato_json = json.dumps(dato_iot)
                dato_cripto = cripto.criptazione(dato_json)

                #Invio del dato tramite MQTT (Publisher)
                client_mqtt.publish(TOPIC, dato_cripto, 0)
                
                #DEBUG richiesto come da specifiche di progetto
                print("Gateway IoT in ricezione e invio")

                #resetto l'array delle temperature, delle umidità e la data di inizio
                temperature = []
                umidita = []
                inizio = time.time()

    except Exception as e:
        print(f"Errore con DC: {e}")
        print(f"(Connessione chiusa con {indirizzo}. Numero invii: {invio_numero})")

    finally:
        client.close()

#server multithread
server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM) #creazione di una socket tcp/ipv4 
server_socket.bind((IP_SERVER, PORTA_SERVER)) #"collego" la socket all'ip e porta specificti
server_socket.listen() #ascolto più connessioni 

#mostro un messaggio in output per indicare che il DA è in ascolto
print("DA avviato. In attesa del DC..")

try:
    while True:
        #dichiarazione e inizializzazione variabili
        client, indirizzo = server_socket.accept() #accetto la connessione in entrata

        #mostro un messaggio in output per indicare che il DC e il DA sono connessi
        print("Connessione con DC effettuata da:", indirizzo)

        #creazione del thread
        thread = threading.Thread(target=gestione_client, args=(client, indirizzo))
        thread.daemon = True
        thread.start()

except KeyboardInterrupt:
    print("DA chiuso")

finally:
    server_socket.close()
    #Chiusura della connessione MQTT
    client_mqtt.loop_stop()
    client_mqtt.disconnect()