#importazione librerie
import socket #per la gestione delle socket
import time #per la gestione del tempo
import json #per gestire i file json
import cripto #per la gestione della crittografia

#leggo i parametri presenti nel file: parametri.conf
with open("parametri.conf", "r") as file:
    parametri = json.load(file)

TEMPO_RILEVAZIONE = parametri["TEMPO_RILEVAZIONE"]
TEMPO_INVIO = parametri["TEMPO_INVIO"] * 60 #conversione in secondi
NUMERO_DECIMALI = parametri["NUMERO_DECIMALI"]
IP_SERVER = parametri["IP_SERVER"]
PORTA_SERVER = parametri["PORTA_SERVER"]

#creazione di una socket tcp/ipv4 
server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_socket.bind((IP_SERVER, PORTA_SERVER)) #"collego" la socket all'ip e porta specificti
server_socket.listen(1) #ascolto 1 connessione

#mostro un messaggio in output per indicare che il DA è in ascolto
print("DA avviato. In attesa del DC..")

##dichiarazione e inizializzazione variabili
client, indirizzo = server_socket.accept() #accetto la connessione in entrata
#mostro un messaggio in output per indicare che il DC e il DA sono connessi
print("Connessione con DC effettuata da:", indirizzo)
#invio al DC il tempo di rilevazione
client.send(str(parametri["TEMPO_RILEVAZIONE"]).encode())
#usiamo la funzione encode() per convertire la richiesta da stringa in ytes-objec

#dichiarazione e inizializzazione variabili
temperature = []
umidita = []
invio_numero = 0
inizio = time.time() 

try:
    #finchè la connessione è attiva, ricevo dati
    while True:
        #ricevo i dati dal client
        dato = client.recv(1024).decode()
        #se la connessione viene chiusa, esco dal ciclo
        if not dato:
            break

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
                "identita_giot": parametri["ID_GIOT"],
                "cabina": dato["cabina"],
                "ponte": dato["ponte"],
                "data_ora": rilevazione_data_ora,
                "media_temperatura": media_t,
                "media_umidita": media_u,
                "dc": dato["identita"],
            }

            #salvataggio nel file iotdata.dvt
            with open("../IOTP/iotdata.dbt", "a") as file:
                file.write(json.dumps(dato_iot) + "\n")

            #crittografia del dato
            dato_json = json.dumps(dato_iot)
            dato_cripto = cripto.criptazione(dato_json)

            #resetto l'array delle temperature, delle umidità e la data di inizio
            temperature = []
            umidita = []
            inizio = time.time()

except KeyboardInterrupt:
    print("DA chiuso. Numero invii:", invio_numero)
    
client.close()
server_socket.close()