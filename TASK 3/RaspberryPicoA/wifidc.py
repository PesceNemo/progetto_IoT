import rp2
import network
import ubinascii
import machine
import time
import json

# Costanti di stato
STATI_WIFI = {
    0: "Link Down",
    1: "Link Join",
    2: "Link NoIp",
    3: "Link Up",
    -1: "Link Fail",
    -2: "Link NoNet",
    -3: "Link BadAuth"
}

def carica_credenziali(nome_file='wifipico.conf'):
    """Recupera SSID e Password dal file JSON."""
    try:
        with open(nome_file, 'r') as file:
            config = json.load(file)
            return config.get("ssid"), config.get("pw")
    except OSError:
        print(f"Errore: File {nome_file} non trovato!")
        return None, None

def set_powersaving(wlan, disabilita=False):
    """
    Gestisce il risparmio energetico del chip CYW43439.
    0xa11140: Disabilita per massima reattività.
    0x004022: Valore standard (default).
    """
    if disabilita:
        wlan.config(pm=0xa11140)
        print("Powersaving: Disabilitato")
    else:
        print("Powersaving: Attivo (Default)")

def segnala_errore_led(stato):
    """Fa lampeggiare il LED integrato in base al codice di errore."""
    led = machine.Pin('LED', machine.Pin.OUT)
    # Se lo stato è negativo (es. -3), usiamo il valore assoluto per i blink
    volte = abs(stato) if stato != 0 else 1 
    
    for _ in range(volte):
        led.on()
        time.sleep(0.2)
        led.off()
        time.sleep(0.2)

def info_wifi(wlan):
    """Mostra i dettagli tecnici della scheda e scansiona le reti."""
    mac = ubinascii.hexlify(wlan.config('mac'), ':').decode()
    print("-" * 30)
    print(f"MAC Address: {mac}")
    print(f"Canale:      {wlan.config('channel')}")
    print(f"Potenza TX:  {wlan.config('txpower')}")
    print("Scansione reti disponibili...")
    print("(SSID, BSSID, Channel, RSSI, Security, Hidden)")
    for rete in wlan.scan():
        print(rete)
    print("-" * 30)

def connetti_wifi(wlan, ssid, password, timeout=10):
    """Esegue la procedura di connessione."""
    if not ssid or not password:
        print("Errore: Credenziali mancanti.")
        return False

    print(f"Connessione a {ssid}...")
    wlan.connect(ssid, password)

    while timeout > 0:
        stato = wlan.status()
        # Se lo stato è 3 (Link Up) o un errore critico (< 0), usciamo dal loop
        if stato < 0 or stato >= 3:
            break
        
        timeout -= 1
        print(f"Attesa... ({timeout})")
        time.sleep(1)

    stato_finale = wlan.status()
    if stato_finale == 3:
        config = wlan.ifconfig()
        print("\nConnessione Riuscita!")
        print(f"IP:      {config[0]}")
        print(f"Subnet:  {config[1]}")
        print(f"Gateway: {config[2]}")
        return True
    else:
        desc_errore = STATI_WIFI.get(stato_finale, "Sconosciuto")
        print(f"\nErrore di connessione: {stato_finale} ({desc_errore})")
        return False

# --- MAIN ---
if __name__ == "__main__":
    # Inizializzazione Hardware
    rp2.country('IT')
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)

    # 1. Caricamento dati
    SSID, PASW = carica_credenziali()

    # 2. Configurazione opzionale
    set_powersaving(wlan, disabilita=True)
    info_wifi(wlan)

    # 3. Tentativo di connessione
    successo = connetti_wifi(wlan, SSID, PASW)

    if not successo:
        # In caso di errore, entra in un loop di segnalazione LED
        print("Blocco sistema per errore WiFi. Segnalazione LED in corso...")
        while True:
            segnala_errore_led(wlan.status())
            time.sleep(1)