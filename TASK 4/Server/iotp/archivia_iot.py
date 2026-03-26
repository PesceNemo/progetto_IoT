import json
import paho.mqtt.client as mqtt
import cripto  # Il tuo modulo locale per la decriptazione

# --- 1. LETTURA DEL FILE DI CONFIGURAZIONE ---
# Leggiamo i parametri dal file iotp.json che si trova nella cartella iotp
try:
    with open("iotp.json", "r") as f:
        config = json.load(f)
except FileNotFoundError:
    print("Errore: File iotp.json non trovato! Assicurati di aver rinominato iotp.py in iotp.json.")
    exit(1)
except json.JSONDecodeError:
    print("Errore: Il file iotp.json non è un JSON valido. Controlla la sintassi.")
    exit(1)

# Estrazione dei dati di configurazione
TOPIC = config["topic"]
BROKER_HOST = config["broker"]["host"]
BROKER_PORTA = config["broker"]["porta"]
NOME_DB = config["dbfile"]["file"]
MODO_SCRITTURA = config["dbfile"]["modo"]


# --- 2. CALLBACK DEGLI EVENTI MQTT ---

def on_connect(client, userdata, flags, rc):
    """Callback eseguita quando il client si connette al broker."""
    if rc == 0:
        print(f"[OK] Connesso al broker {BROKER_HOST}:{BROKER_PORTA}")
        # Ci iscriviamo al topic configurato (es. iotnavi/+/misure)
        client.subscribe(TOPIC)
        print(f"[OK] Sottoscrizione effettuata al topic: {TOPIC}")
    else:
        print(f"[ERRORE] Connessione fallita con codice {rc}")

def on_message(client, userdata, msg):
    """Callback eseguita ogni volta che arriva un messaggio sul topic sottoscritto."""
    try:
        # 1. Ricezione: Il payload arriva come bytes, lo decodifichiamo in stringa
        payload_criptato = msg.payload.decode("utf-8")
        
        # 2. Decriptazione: Utilizziamo la funzione corretta dal tuo modulo cripto.py
        dati_in_chiaro = cripto.decriptazione(payload_criptato)
        
        # 3. Debug a schermo: Stampa dei dati IoT decriptati in chiaro
        print("\n--- NUOVO MESSAGGIO RICEVUTO ---")
        print(f"Topic di provenienza : {msg.topic}")
        print(f"Dato IoT (in chiaro) : {dati_in_chiaro}")
        
        # 4. Archiviazione: Apertura file in modalità "a" (append) e salvataggio
        with open(NOME_DB, MODO_SCRITTURA) as db:
            # Scriviamo il dato decriptato e andiamo a capo per il prossimo record
            db.write(dati_in_chiaro + "\n")
            
        print(f"[OK] Dato archiviato con successo in {NOME_DB}")

    except Exception as e:
        print(f"[ERRORE] Si è verificato un problema durante l'elaborazione: {e}")


# --- 3. INIZIALIZZAZIONE E AVVIO DEL CLIENT ---

# Creazione dell'istanza del client MQTT
client = mqtt.Client()

# Assegnazione delle funzioni di callback agli eventi del client
client.on_connect = on_connect
client.on_message = on_message

# Connessione al broker
print("Tentativo di connessione al broker in corso...")
client.connect(BROKER_HOST, BROKER_PORTA, 60)

# Avvio del loop infinito per restare in ascolto dei messaggi in arrivo
try:
    print("Archiviazione IOTP in attesa di dati... (Premi CTRL+C per terminare)")
    client.loop_forever()
except KeyboardInterrupt:
    print("\n[INFO] Disconnessione in corso...")
    client.disconnect()
    print("Script terminato.")