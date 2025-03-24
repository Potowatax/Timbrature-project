import csv
from datetime import datetime, date, timedelta
from collections import defaultdict

class Timbrature:
    def __init__(self):
        self.registro = []
        self.attivita = []
        self.orari_sospensione = "07:30-14:42"
        self.orari_didattica = "07:30-14:15"
        self.causali_negativo = {}
        self.causali_positivo = []
        self.causali_compensazione = ["Permesso_per_servizio"]
        self.causali_anno = {}
        self.ore_sospensione = timedelta(hours=7, minutes=12)
        self.ore_didattica = timedelta(hours=6, minutes=45)
        self.ore_rientro = timedelta(hours=9)
        self.soglia_pausa_pranzo = timedelta(hours=7, minutes=12)
        self.contatori_annuali = {
            "Assemblea": 0,
            "Legge_104": 0,
            "Visita_specialistica": 0,
            "Permesso_studio": 0
        }
        self.totale_negativo = timedelta()
        self.totale_straordinario = timedelta()
        self.totale_eccedenze = timedelta()
        self.saldo_finale = timedelta()
        self.contatori_mensili = defaultdict(lambda: {
            "totale_negativo": timedelta(),
            "totale_straordinario": timedelta(),
            "totale_eccedenze": timedelta(),
            "saldo_finale": timedelta()
        })

    # Importa i dati dal file di testo
    def importa_txt(self, filename="timbrature.txt"):
        try:
            with open(filename, mode="r", encoding="utf-8") as file:
                for line in file:
                    parts = line.strip().split()
                    if len(parts) >= 3:
                        data = parts[0]
                        ora = parts[1]
                        evento = parts[2]
                        causale = parts[3] if len(parts) > 3 else ""
                        self.registro.append({
                            "data": data,
                            "ora": ora,
                            "evento": evento,
                            "causale": causale
                        })
        except FileNotFoundError:
            print(f"Errore: Il file {filename} non esiste.")
        except UnicodeDecodeError:
            print(f"Errore di codifica: il file {filename} non è in formato UTF-8.")
        except Exception as e:
            print(f"Errore imprevisto durante l'importazione del file {filename}: {e}")

    # Importa i dati dal file settings.txt
    def importa_settings(self, filename="settings.txt"):
        try:
            with open(filename, mode="r", encoding="utf-8") as file:
                section = None
                for line in file:
                    line = line.strip()
                    if line.startswith("#"):
                        section = line.lower()
                    elif not line:
                        section = None
                    else:
                        if ":" in line:
                            key, value = map(str.strip, line.split(":", 1))
                            if "-" in key:
                                self.attivita.append((key, value))
                            elif "orari settimanali per sospensione" in section:
                                self.orari_sospensione = value
                            elif "orari settimanali per didattica" in section:
                                self.orari_didattica = value
                            elif "ore da lavorare per sospensione" in section:
                                ore, minuti = map(int, value.split(":"))
                                self.ore_sospensione = timedelta(hours=ore, minutes=minuti)
                            elif "ore da lavorare per didattica" in section:
                                ore, minuti = map(int, value.split(":"))
                                self.ore_didattica = timedelta(hours=ore, minutes=minuti)
                            elif "ore da lavorare per il giorno di rientro" in section:
                                ore, minuti = map(int, value.split(":"))
                                self.ore_rientro = timedelta(hours=ore, minutes=minuti)
        except FileNotFoundError:
            print(f"Errore: Il file {filename} non esiste.")
        except UnicodeDecodeError:
            print(f"Errore di codifica: il file {filename} non è in formato UTF-8.")
        except Exception as e:
            print(f"Errore imprevisto durante l'importazione del file {filename}: {e}")

    # Calcola le ore lavorate e organizza i dati
    def calcola_ore(self):
        risultati = {}
        for evento in self.registro:
            data_parsed = self.parse_data(evento['data'])
            try:
                ora = datetime.strptime(evento["ora"], "%H:%M").time()
            except ValueError:
                continue

            chiave = data_parsed

            if chiave not in risultati:
                risultati[chiave] = {"entrate": [], "uscite": [], "causali_entrata": [], "causali_uscita": []}

            if "Entrata" in evento["evento"]:
                risultati[chiave]["entrate"].append(ora)
                risultati[chiave]["causali_entrata"].append(evento["causale"])
            elif "Uscita" in evento["evento"]:
                risultati[chiave]["uscite"].append(ora)
                risultati[chiave]["causali_uscita"].append(evento["causale"])
        return risultati

    # Determina l'attività in base alla data
    def determina_attivita(self, data):
        for intervallo, attivita in self.attivita:
            start_date, end_date = intervallo.split("-")
            start_date = self.parse_data(start_date)
            end_date = self.parse_data(end_date)
            if start_date <= data <= end_date:
                return attivita
        return ""

    # Determina le ore da lavorare in base all'attività
    def determina_ore_da_lavorare(self, data, attivita):
        if attivita == "Sospensione":
            return self.ore_sospensione
        elif attivita == "Didattica":
            return self.ore_didattica
        return timedelta()

    # Parsea la data considerando l'anno scolastico
    def parse_data(self, data_str):
        day, month = map(int, data_str.split("/"))
        if month >= 9:
            year = 2024
        else:
            year = 2025
        return date(year, month, day)

    # Determina il valore della colonna Rientro
    def determina_rientro(self, giorno_settimana, attivita):
        if attivita == "Didattica" and giorno_settimana == "Monday":
            return "Rientro"
        return "Normale"

    # Determina l'orario di inizio e fine lavoro
    def determina_orari(self, attivita, rientro):
        if attivita == "Sospensione":
            inizio = "07:30"
            fine = "14:42"
        elif attivita == "Didattica":
            inizio = "07:30"
            fine = "14:15"
            if rientro == "Rientro":
                fine = "17:00"
        else:
            inizio = ""
            fine = ""
        return inizio, fine

    # Esporta i risultati in un file CSV
    def esporta_csv(self, risultati, filename="Cartellino.csv"):
        try:
            with open(filename, mode="w", newline="", encoding="utf-8") as file:
                fieldnames = ["Data", "Giorno della Settimana", "Attività", "Ore da lavorare", "Rientro", "Pausa pranzo", "Inizio", "Fine", "DurataPausaPranzo"]
                for i in range(1, 7):
                    fieldnames.extend([f"Entrata {i}", f"Causale Entrata {i}", f"Uscita {i}", f"Causale Uscita {i}"])

                writer = csv.DictWriter(file, fieldnames=fieldnames, delimiter=";")
                writer.writeheader()

                for chiave, eventi in risultati.items():
                    giorno_settimana = chiave.strftime('%A')
                    attivita = self.determina_attivita(chiave)
                    ore_da_lavorare = str(self.determina_ore_da_lavorare(chiave, attivita))
                    rientro = self.determina_rientro(giorno_settimana, attivita)
                    inizio, fine = self.determina_orari(attivita, rientro)

                    row = {
                        "Data": chiave.strftime('%d/%m/%Y'),
                        "Giorno della Settimana": giorno_settimana,
                        "Attività": attivita,
                        "Ore da lavorare": ore_da_lavorare,
                        "Rientro": rientro,
                        "Pausa pranzo": "",
                        "Inizio": inizio,
                        "Fine": fine,
                        "DurataPausaPranzo": "00:30:00",
                    }
                    for i in range(1, 7):
                        row[f"Entrata {i}"] = eventi["entrate"][i-1].strftime('%H:%M') if i <= len(eventi["entrate"]) else ""
                        row[f"Causale Entrata {i}"] = f"(E){eventi['causali_entrata'][i-1]}" if i <= len(eventi["causali_entrata"]) and eventi["causali_entrata"][i-1] else ""
                        row[f"Uscita {i}"] = eventi["uscite"][i-1].strftime('%H:%M') if i <= len(eventi["uscite"]) else ""
                        row[f"Causale Uscita {i}"] = f"(U){eventi['causali_uscita'][i-1]}" if i <= len(eventi["causali_uscita"]) and eventi["causali_uscita"][i-1] else ""

                    writer.writerow(row)
            print(f"Dati esportati in {filename}")
        except IOError as e:
            print(f"Errore durante l'esportazione dei dati in {filename}: {e}")

    # Mostra a schermo il registro degli eventi
    def mostra_registro(self):
        for evento in self.registro:
            print(f"{evento['data']} - {evento['ora']} - {evento['evento']} - {evento['causale']}")

if __name__ == "__main__":
    timbrature = Timbrature()
    timbrature.importa_txt("timbrature.txt")
    timbrature.importa_settings("settings.txt")
    timbrature.mostra_registro()
    risultati = timbrature.calcola_ore()
    timbrature.esporta_csv(risultati)
