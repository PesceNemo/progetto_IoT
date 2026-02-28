import misurazione
import time
import json
import socket
import sys
sys.path.append("../Computer-Raspberry")
import cripto
from machine import Pin
import dht

# Costanti per i nomi dei file (come nel primo script)
CONFIG_FILE = 'configurazionedc.json'
ADDR_FILE = 'da.json'

def carica_config(nome_file):
    """Carica i parametri da un file JSON con gestione errori"""
    try:
        with open(nome_file) as file:
            return json.load(file)
    except FileNotFoundError:
        print(f"Errore: file '{nome_file}' non trovato")
        return None
    except json.JSONDecodeError:
        print(f"Errore: formato JSON non valido in {nome_file}")
        return None

def crea_dato_iot(config, rilevazione, temperatura, umidita):
    """Crea il dizionario con i dati IoT rimuovendo i parametri di cablaggio"""
    # Usiamo una copia per non sporcare la config originale
    dato = config.copy()
    dato.pop("cablaggio", None) 
    
    dato["osservazione"] = {
        "rilevazione": rilevazione,
        "temperatura": temperatura,
        "umidita": umidita
    }
    return dato

def main():
    # 1. Caricamento configurazioni
    config = carica_config(CONFIG_FILE)
    indirizzi = carica_config(ADDR_FILE)
    
    if not config or not indirizzi:
        return

    # 2. Inizializzazione Hardware (LED e Sensore)
    led_interno = Pin(15, Pin.OUT)
    # Usa il pin specificato nel file json per il sensore DHT11
    pin_sensore = Pin(config["cablaggio"]["segnale"])
    sensore = dht.DHT11(pin_sensore)
    
    # 3. Setup Socket
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    
    try:
        # Connessione usando i dati del file da.json
        client.connect((indirizzi["IP"], int(indirizzi["porta"])))
        print(f"Connesso al server {indirizzi['IP']}")
        
        # Ricezione tempo di campionamento
        tempo_rilevazione = int(client.recv(1024).decode())
        print(f"Intervallo ricevuto: {tempo_rilevazione}s")
        
        rilevazione = 0
        
        while True:
            try:
                # Lettura dal sensore (usando il modulo misurazione come nel primo script)
                temperatura, umidita = misurazione.lettura_sensore(sensore)
                rilevazione += 1
                
                # Preparazione del messaggio
                dato_iot = crea_dato_iot(config, rilevazione, temperatura, umidita)
                dato_json = json.dumps(dato_iot)
                
                # Criptazione e aggiunta del terminatore di riga
                dato_criptato = cripto.criptazione(dato_json)
                messaggio = (dato_criptato + '\n').encode()
                
                # Invio con feedback visivo sul LED
                led_interno.value(1)
                client.send(messaggio)
                led_interno.value(0)
                
                print(f"Rilevazione #{rilevazione} inviata correttamente")
                
            except OSError as e:
                print(f"Errore hardware sensore: {e}")
            
            time.sleep(tempo_rilevazione)
            
    except KeyboardInterrupt:
        print("\nInterruzione manuale: chiusura in corso...")
    except Exception as e:
        print(f"Errore critico: {e}")
    finally:
        client.close()
        led_interno.value(0)
        print("Client spento.")

if __name__ == "__main__":
    main()