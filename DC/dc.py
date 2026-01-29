import misurazione
import time
import json
import socket
import cripto

def carica_config(nome_file):
    """Carica i parametri dal file di configurazione JSON"""
    try:
        with open(nome_file) as file:
            return json.load(file)
    except FileNotFoundError:
        print(f"Errore: file '{nome_file}' non trovato")
        return None
    except json.JSONDecodeError:
        print("Errore: JSON non valido")
        return None

def crea_dato_iot(config, rilevazione, temperatura, umidita):
    """Crea il dizionario con i dati IoT"""
    return {
        "cabina": config["cabina"],
        "ponte": config["ponte"],
        "sensore": config["sensore"],
        "identita": config["identita"],
        "osservazione": {
            "rilevazione": rilevazione,
            "temperatura": temperatura,
            "umidita": umidita
        }
    }

def main():
    # Carica configurazione
    config = carica_config('configurazionedc.conf')
    if not config:
        return
    
    # Crea socket e connette al server
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    
    try:
        client.connect(("127.0.0.1", 6767))
        print("Connesso al DA")
        
        # Riceve tempo di rilevazione
        tempo_rilevazione = int(client.recv(1024).decode())
        print(f"Tempo rilevazione: {tempo_rilevazione} secondi")
        
        rilevazione = 0
        
        # Ciclo principale di rilevazione
        while True:
            rilevazione += 1
            
            # Leggi sensori
            temperatura = misurazione.on_temperatura(
                config["sensore"]["tmin"],
                config["sensore"]["tmax"],
                config["sensore"]["erroret"]
            )
            umidita = misurazione.on_umidita(
                config["sensore"]["umin"],
                config["sensore"]["umax"],
                config["sensore"]["erroreu"]
            )
            
            # Crea e invia dato
            dato_iot = crea_dato_iot(config, rilevazione, temperatura, umidita)
            dato_json = json.dumps(dato_iot)
            dato_criptato = cripto.criptazione(dato_json)
            
            client.send(dato_criptato.encode())
            print("Dato inviato:")
            print(dato_json)
            
            time.sleep(tempo_rilevazione)
            
    except KeyboardInterrupt:
        print("\nChiusura client")
    except Exception as e:
        print(f"Errore: {e}")
    finally:
        client.close()
        print("Client terminato")

if __name__ == "__main__":
    main()