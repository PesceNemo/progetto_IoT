import json
import time
import random
import misurazione

# Variabile globale per ID rilevazioni
rilevazioni = 1

# Liste per calcolare le medie
temperature_rilevate = []
umidita_rilevate = []

#Carica parametri dal file di configurazione
def carica_parametri():
    try:
        with open('configurazione/parametri.conf') as file:
            parametri = json.load(file)
            print("Parametri caricati correttamente\n")
            return parametri
    except FileNotFoundError:
        print("Errore: file parametri.conf non trovato")
        return None
    except json.JSONDecodeError:
        print("Errore: formato JSON non valido")
        return None

# Crea un dato IoT in formato dizionario
def crea_dato(temperatura, umidita, num_cabine, num_ponti):
    global rilevazioni
    
    # Genera casualmente cabina e ponte
    cabina = random.randint(1, num_cabine)
    ponte = random.randint(1, num_ponti)
    
    dato = {
        "cabina": cabina,
        "ponte": ponte,
        "rilevazione": rilevazioni,
        "dataeora": time.time(),
        "temperatura": temperatura,
        "umidita": umidita
    }
    rilevazioni += 1
    return dato

#Salva il dato sul file
def salva_dato(dato):
    try:
        with open('dati/iotdata.dbt', 'a') as file:
            json.dump(dato, file, indent=4)
            file.write("\n")
        return True
    except IOError:
        print("Errore nella scrittura del file")
        return False

#Esegue una singola rilevazione
def esegui_rilevazione(parametri):
    #Leggi sensori
    temp = misurazione.on_temperatura(parametri["NUMERO_DECIMALI"])
    umid = misurazione.on_umidita(parametri["NUMERO_DECIMALI"])
    
    #Salva per calcolare medie
    temperature_rilevate.append(temp)
    umidita_rilevate.append(umid)
    
    #Crea dato
    dato = crea_dato(temp, umid, parametri["NUMERO_CABINE"], parametri["NUMERO_PONTI"])
    
    #Stampa con indentazione
    print(json.dumps(dato, indent=4))
    print()  # Riga vuota per separare
    
    # Salva su file
    salva_dato(dato)

# Mostra statistiche finali
def mostra_statistiche(parametri):
    print("STATISTICHE FINALI")
    print(f"Numero di rilevazioni effettuate: {rilevazioni - 1}")
    
    if temperature_rilevate:
        temp_media = round(sum(temperature_rilevate) / len(temperature_rilevate), parametri["NUMERO_DECIMALI"])
        umid_media = round(sum(umidita_rilevate) / len(umidita_rilevate), parametri["NUMERO_DECIMALI"])
        
        print(f"Temperatura media: {temp_media}°C")
        print(f"Umidità media: {umid_media}%")
#Funzione principale
def main():
    print("AVVIO SIMULAZIONE IoT")
    
    # Carica parametri
    parametri = carica_parametri()
    if parametri is None:
        print("Impossibile avviare il programma")
        return
    
    #Ciclo principale
    try:
        while True:
            esegui_rilevazione(parametri)
            time.sleep(parametri["TEMPO_RILEVAZIONE"])
            
    except KeyboardInterrupt:
        print("\n\nInterruzione da tastiera (CTRL+C)")
        mostra_statistiche(parametri)
        
    finally:
        print("\nProgramma terminato")

# Avvio programma
if __name__ == "__main__":

    main()


