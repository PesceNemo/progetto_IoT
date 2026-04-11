import json
import paho.mqtt.client as mqtt
import cripto  

# Tenta il caricamento della configurazione da una directory di livello superiore rispetto allo script
try:
    with open("../iotp.json", "r") as f:
        config = json.load(f)
except FileNotFoundError:  
    print("Errore: File iotp.json non trovato! Assicurati di aver rinominato iotp.py in iotp.json.")
    exit(1)
except json.JSONDecodeError:
    print("Errore: Il file iotp.json non è un JSON valido. Controlla la sintassi.")
    exit(1)

TOPIC = config["topic"]
BROKER_HOST = config["broker"]["host"]
BROKER_PORTA = config["broker"]["porta"]
NOME_DB = config["dbfile"]["file"]
MODO_SCRITTURA = config["dbfile"]["modo"]

def on_connect(client, userdata, flags, rc):
    # rc (return code) uguale a 0 indica che la connessione al broker ha avuto successo
    if rc == 0:
        print(f"[OK] Connesso al broker {BROKER_HOST}:{BROKER_PORTA}")
        client.subscribe(TOPIC)
        print(f"[OK] Sottoscrizione effettuata al topic: {TOPIC}")
    else:
        print(f"[ERRORE] Connessione fallita con codice {rc}")

def on_message(client, userdata, msg):
    try:
        # Il payload arriva come flusso di byte, è necessaria la decodifica in stringa UTF-8
        payload_criptato = msg.payload.decode("utf-8")
        
        dati_in_chiaro = cripto.decriptazione(payload_criptato)
        
        print("\n--- NUOVO MESSAGGIO RICEVUTO ---")
        print(f"Topic di provenienza : {msg.topic}")
        print(f"Dato IoT (in chiaro) : {dati_in_chiaro}")
        
        # Apre il file e aggiunge un newline ('\n') per garantire che ogni JSON sia su una riga separata
        with open(NOME_DB, MODO_SCRITTURA) as db:
            db.write(dati_in_chiaro + "\n")
            
        print(f"[OK] Dato archiviato con successo in {NOME_DB}")

    except Exception as e:
        print(f"[ERRORE] Si è verificato un problema durante l'elaborazione: {e}")

client = mqtt.Client()
client.on_connect = on_connect
client.on_message = on_message

print("Tentativo di connessione al broker in corso...")
client.connect(BROKER_HOST, BROKER_PORTA, 60)

try:
    print("Archiviazione IOTP in attesa di dati... (Premi CTRL+C per terminare)")
    # Mantiene vivo lo script e gestisce in automatico la ricezione dei pacchetti MQTT in background
    client.loop_forever()
except KeyboardInterrupt:
    print("\n[INFO] Disconnessione in corso...")
    client.disconnect()
    print("Script terminato.")