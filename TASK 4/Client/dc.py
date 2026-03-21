import misurazione
import time
import json
import socket
import cripto # Mantenuto dal tuo codice originale
import wifidc # NUOVO: Importazione del modulo per il Wi-Fi
from machine import Pin
import dht
import network
import rp2

# Rimosso: from logging import config (inutile e spesso incompatibile su MicroPython)

CONFIG_FILE = 'configurazionedc.json'
ADDR_FILE = 'da.json'

def carica_config(nome_file):
    """Carica i parametri da un file JSON (MicroPython friendly)"""
    try:
        with open(nome_file) as file:
            return json.load(file)
    except OSError: # Manteniamo l'eccezione sicura per MicroPython
        print(f"Errore: file '{nome_file}' non trovato o errore di lettura")
        raise # Solleviamo l'errore per farlo gestire al blocco try/except nel main()
    except ValueError:
        print(f"Errore: formato JSON non valido in {nome_file}")
        raise

def crea_dato_iot(config, rilevazione, temperatura, umidita):
    """Crea il dizionario con i dati IoT in modo sicuro"""
    dato = config.copy() # Manteniamo .copy() dal tuo codice originale, è più sicuro!
    dato.pop("cablaggio", None) 
    
    dato["osservazione"] = {
        "rilevazione": rilevazione,
        "temperatura": temperatura,
        "umidita": umidita
    }
    return dato

def main():
    # --- NUOVO: AVVIO WI-FI (Usando il modulo del prof) ---
    print("Inizializzazione della scheda di rete...")
    rp2.country('IT')
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    
    # 1. Carica SSID e Password usando la funzione del prof
    # ATTENZIONE: devi avere un file chiamato 'wifipico.json' salvato sulla scheda!
    ssid, pw = wifidc.carica_credenziali('wifipico.json')
    
    # 2. Imposta il risparmio energetico e prova a connettersi
    wifidc.set_powersaving(wlan, disabilita=True)
    successo = wifidc.connetti_wifi(wlan, ssid, pw)
    
    if not successo:
        print("Errore critico: impossibile collegarsi al router Wi-Fi. Chiusura.")
        return # Ferma tutto se non c'è internet
    # --- FINE AVVIO WI-FI ---

    # --- DA QUI PARTE IL RESTO DEL TUO CODICE ---
    # 1. Caricamento configurazioni DC e DA
    try:
        config = carica_config(CONFIG_FILE)
        indirizzi = carica_config(ADDR_FILE)
        print("Caricamento parametri json eseguito correttamente")
    except Exception as err:
        print("Errore durante il caricamento dei parametri: ", err)
        return

    # 2. Inizializzazione Hardware
    led_interno = Pin(15, Pin.OUT)
    sensore = dht.DHT11(Pin(config["cablaggio"]["segnale"]))
    
    # 3. Setup Socket
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    
    try:
        client.connect((indirizzi["IP"], int(indirizzi["porta"])))
        print(f"Connesso al server (DA) {indirizzi['IP']}")
        
        tempo_rilevazione = int(client.recv(1024).decode())
        print(f"Intervallo ricevuto: {tempo_rilevazione}s")
        
        rilevazione = 0
        
        while True:
            # NUOVO: Gestione specifica per saltare il ciclo se il sensore fallisce la lettura
            try:
                temperatura, umidita = misurazione.lettura_sensore(sensore)
            except OSError as e:
                print("Errore durante la lettura dal sensore (ritento al prossimo ciclo): ", e)
                time.sleep(2)
                continue
            
            rilevazione += 1
            
            # Preparazione del messaggio usando la tua funzione
            dato_iot = crea_dato_iot(config, rilevazione, temperatura, umidita)
            dato_json = json.dumps(dato_iot)
            
            # Criptazione e invio (Mantenuto dal tuo codice originale)
            dato_criptato = cripto.criptazione(dato_json)
            messaggio = (dato_criptato + '\n').encode()
            
            led_interno.value(1)
            client.send(messaggio)
            led_interno.value(0)
            
            # NUOVO: Stampa a schermo dei dati in chiaro per facilitare il debug
            print(f"Rilevazione #{rilevazione} inviata:")
            print(dato_json)
            
            time.sleep(tempo_rilevazione)
            
    except KeyboardInterrupt:
        print("\nChiusura del client in corso...")
    except Exception as e:
        print(f"Errore generico: {e}")
    finally:
        client.close()
        led_interno.value(0)
        print("Client terminato correttamente.")

if __name__ == "__main__":
    main()
