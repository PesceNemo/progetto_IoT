import misurazione
import time
import json
import socket
import cripto 
import random

CONFIG_FILE = 'configurazionedc.json'
ADDR_FILE = 'da.json'

# --- NUOVO: Definiamo il numero di decimali per la simulazione ---
NUMERO_DECIMALI = 1 

def carica_config(nome_file):
    try:
        with open(nome_file) as file:
            return json.load(file)
    except FileNotFoundError: 
        print(f"Errore: file '{nome_file}' non trovato.")
        raise 
    except ValueError:
        print(f"Errore: formato JSON non valido in {nome_file}")
        raise

def crea_dato_iot(config, rilevazione, temperatura, umidita):
    dato = config.copy() 
    dato.pop("cablaggio", None) 
    
    dato["osservazione"] = {
        "rilevazione": rilevazione,
        "temperatura": temperatura,
        "umidita": umidita
    }
    return dato

def main():
    print("--- AVVIO CLIENT DC IN MODALITA' SIMULAZIONE (PC) ---")

    # 1. Caricamento configurazioni DC e DA
    try:
        config = carica_config(CONFIG_FILE)
        indirizzi = carica_config(ADDR_FILE)
        print("Caricamento parametri json eseguito correttamente")

        cabina_assegnata = random.randint(100, 150) # Scegli il range che preferisci
        config["cabina"] = cabina_assegnata
        config["identita"] = f"DC{cabina_assegnata}-03"
        print(f"*** SIMULAZIONE: Sensore assegnato alla CABINA {cabina_assegnata} ***")
    except Exception as err:
        print("Errore durante il caricamento dei parametri: ", err)
        return

    # 2. Setup Socket (Connessione al DA)
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    
    try:
        client.connect((indirizzi["IP"], int(indirizzi["porta"])))
        print(f"Connesso al server (DA) {indirizzi['IP']}")
        
        tempo_rilevazione = int(client.recv(1024).decode())
        print(f"Intervallo ricevuto: {tempo_rilevazione}s")
        
        rilevazione = 0
        
        while True:
            # --- MODIFICA: Lettura simulata con le nuove funzioni e parametro N ---
            temperatura = misurazione.on_temperatura(NUMERO_DECIMALI)
            umidita = misurazione.on_umidita(NUMERO_DECIMALI)
            
            rilevazione += 1
            
            # Preparazione del messaggio
            dato_iot = crea_dato_iot(config, rilevazione, temperatura, umidita)
            dato_json = json.dumps(dato_iot)
            
            # --- DEBUG: Stampa a schermo ---
            print(f"\n[DEBUG] Preparazione Rilevazione #{rilevazione}")
            print(f"Dato in chiaro: {dato_json}")
            
            # Criptazione e invio
            dato_criptato = cripto.criptazione(dato_json)
            messaggio = (dato_criptato + '\n').encode()
            
            client.send(messaggio)
            
            time.sleep(tempo_rilevazione)
            
    except ConnectionRefusedError:
        print(f"Errore: Impossibile connettersi al server DA all'indirizzo {indirizzi['IP']}:{indirizzi['porta']}. Il server è acceso?")
    except KeyboardInterrupt:
        print("\nChiusura del client in corso...")
    except Exception as e:
        print(f"Errore generico: {e}")
    finally:
        client.close()
        print("Client terminato.")

if __name__ == "__main__":
    main()