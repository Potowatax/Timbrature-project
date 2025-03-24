import csv
from datetime import datetime, date, timedelta
from collections import defaultdict

class Timbrature:
    def __init__(self):
        self.registro = []
        self.attivita = []
        self.orari_sospensione = "07:45-14:57"
        self.orari_didattica = "07:45-14:30"
        self.causali_negativo = {}
        self.causali_positivo = []
        self.causali_compensazione = ["Permesso_per_servizio"]
        self.causali_anno = {}
        self.giorno_rientro_pomeridiano = "Lunedì"
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
                    if len(parts) >= 4:
                        data = parts[0]
                        rientro = parts[1]
                        ora = parts[2]
                        evento = parts[3]
                        causale = parts[4] if len(parts) > 4 else ""
                        self.registro.append({
                            "data": data,
                            "rientro": rientro,
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
                            elif "giorno programmato per rientro pomeridiano" in section:
                                self.giorno_rientro_pomeridiano = value
                            elif "ore da lavorare per sospensione" in section:
                                ore, minuti = map(int, value.split(":"))
                                self.ore_sospensione = timedelta(hours=ore, minutes=minuti)
                            elif "ore da lavorare per didattica" in section:
                                ore, minuti = map(int, value.split(":"))
                                self.ore_didattica = timedelta(hours=ore, minutes=minuti)
                            elif "soglia calcolo pausa pranzo" in section:
                                ore, minuti = map(int, value.split(":"))
                                self.soglia_pausa_pranzo = timedelta(hours=ore, minutes=minuti)
                        elif ";" in line:
                            key, value = map(str.strip, line.split(";", 1))
                            if "calcolo negativo" in section:
                                self.causali_negativo[key] = int(value) if value else 0
                            elif "altri tipi di causali" in section:
                                self.causali_anno[key] = int(value) if value else 0
                        else:
                            if "calcolo positivo" in section:
                                self.causali_positivo.append(line.strip())
                            elif "compensazione delle ore non lavorate" in section:
                                self.causali_compensazione.append(line.strip())
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
            ora = datetime.strptime(evento["ora"], "%H:%M").time()
            chiave = data_parsed

            if chiave not in risultati:
                risultati[chiave] = {"rientro": evento["rientro"], "entrate": [], "uscite": [], "causali_entrata": [], "causali_uscita": []}

            if "Ent" in evento["evento"]:
                risultati[chiave]["entrate"].append(ora)
                risultati[chiave]["causali_entrata"].append(evento["causale"])
            elif "Usc" in evento["evento"]:
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

    # Determina l'orario in base alla data e all'attività
    def determina_orario(self, data, attivita):
        if attivita == "Sospensione":
            return self.orari_sospensione
        elif attivita == "Didattica":
            return self.orari_didattica
        return ""

    # Calcola la pausa pranzo in base alle regole specificate
    def calcola_pausa_pranzo(self, entrate, uscite, causali):
        if len(entrate) == 0 or len(uscite) == 0:
            return timedelta()

        totale_lavorato = timedelta()
        for i in range(min(len(entrate), len(uscite))):
            entrata = datetime.combine(date.min, entrate[i])
            uscita = datetime.combine(date.min, uscite[i])
            totale_lavorato += uscita - entrata

        # Check for 'PAUSA_PR', 'Formazione' or 'STRAORDINARIO' causal
        if "PAUSA_PR" in causali or "Formazione" in causali or "STRAORDINARIO" in causali:
            return timedelta()

        # Add 30 minutes if continuous work exceeds the threshold and no 'RECUPERO' causal
        if "RECUPERO" not in causali and totale_lavorato > self.soglia_pausa_pranzo:
            return timedelta(minutes=30)
        return timedelta()

    # Calcola il saldo delle ore lavorate per ogni giornata
    def calcola_saldo(self, entrate, uscite, pausa_pranzo, attivita, rientro, causali_uscita, causali_entrata):
        totale_lavorato = timedelta()
        for i in range(min(len(entrate), len(uscite))):
            entrata = datetime.combine(date.min, entrate[i])
            uscita = datetime.combine(date.min, uscite[i])
            totale_lavorato += uscita - entrata

        # Gestione della causale "Permesso_per_servizio"
        for i in range(len(uscite) - 1):
            if (causali_uscita[i] == "Permesso_per_servizio" and
                causali_entrata[i + 1] == "Permesso_per_servizio"):
                uscita = datetime.combine(date.min, uscite[i])
                entrata = datetime.combine(date.min, entrate[i + 1])
                totale_lavorato += entrata - uscita

        totale_lavorato -= pausa_pranzo

        if rientro == "R":
            ore_richieste = self.ore_rientro
        elif attivita == "Sospensione":
            ore_richieste = self.ore_sospensione
        elif attivita == "Didattica":
            ore_richieste = self.ore_didattica
        else:
            ore_richieste = timedelta()

        saldo = totale_lavorato - ore_richieste

        # Se non c'è la causale "STRAORDINARIO", le ore eccedenti sono usate solo per recuperare i ritardi
        if "STRAORDINARIO" not in causali_entrata + causali_uscita:
            ritardo = max(ore_richieste - totale_lavorato, timedelta())
            if ritardo > timedelta():
                saldo = -ritardo
            else:
                saldo = min(totale_lavorato - ore_richieste, timedelta())

        # Gestione del saldo negativo
        if saldo < timedelta():
            saldo = -((timedelta(days=1) - abs(saldo)) % timedelta(days=1))

        return saldo

    # Calcola il totale delle ore lavorate per ogni giornata
    def calcola_totale_lavorato(self, entrate, uscite, pausa_pranzo, causali_uscita, causali_entrata):
        totale_lavorato = timedelta()
        for i in range(min(len(entrate), len(uscite))):
            entrata = datetime.combine(date.min, entrate[i])
            uscita = datetime.combine(date.min, uscite[i])
            totale_lavorato += uscita - entrata

        # Gestione della causale "Permesso_per_servizio"
        for i in range(len(uscite) - 1):
            if (causali_uscita[i] == "Permesso_per_servizio" and
                causali_entrata[i + 1] == "Permesso_per_servizio"):
                uscita = datetime.combine(date.min, uscite[i])
                entrata = datetime.combine(date.min, entrate[i + 1])
                totale_lavorato += entrata - uscita

        totale_lavorato -= pausa_pranzo
        return totale_lavorato

    # Aggiorna i contatori annuali basati sulle causali
    def aggiorna_contatori_annuali(self, causali):
        for causale in causali:
            if causale in self.contatori_annuali:
                self.contatori_annuali[causale] += 1

    # Aggiorna i totali annuali e mensili
    def aggiorna_totali_annuali_mensili(self, saldo, causali, chiave):
        if saldo < timedelta():
            self.totale_negativo += abs(saldo)
            self.contatori_mensili[chiave.strftime('%Y-%m')]["totale_negativo"] += abs(saldo)
        else:
            self.totale_eccedenze += saldo
            self.contatori_mensili[chiave.strftime('%Y-%m')]["totale_eccedenze"] += saldo

        for causale in causali:
            if causale == "Straordinario":
                self.totale_straordinario += saldo
                self.contatori_mensili[chiave.strftime('%Y-%m')]["totale_straordinario"] += saldo

        self.saldo_finale += saldo
        self.contatori_mensili[chiave.strftime('%Y-%m')]["saldo_finale"] += saldo

    # Parsea la data considerando l'anno scolastico
    def parse_data(self, data_str):
        day, month = map(int, data_str.split("/"))
        if month >= 9:
            year = 2024
        else:
            year = 2025
        return date(year, month, day)

    # Esporta i risultati in un file CSV
    def esporta_csv(self, risultati, filename="Cartellino.csv"):
        try:
            with open(filename, mode="w", newline="", encoding="utf-8") as file:
                fieldnames = ["Data", "Giorno della Settimana", "Attività", "Orario", "Totale Lavorato", "Pausa Pranzo", "Saldo"]
                for i in range(1, 7):
                    fieldnames.extend([f"Entrata {i}", f"Causale Entrata {i}", f"Uscita {i}", f"Causale Uscita {i}"])

                writer = csv.DictWriter(file, fieldnames=fieldnames, delimiter=";")
                writer.writeheader()

                for chiave, eventi in risultati.items():
                    giorno_settimana = chiave.strftime('%A')
                    attivita = self.determina_attivita(chiave)
                    orario = self.determina_orario(chiave, attivita)
                    pausa_pranzo = self.calcola_pausa_pranzo(eventi["entrate"], eventi["uscite"], eventi["causali_entrata"] + eventi["causali_uscita"])
                    saldo = self.calcola_saldo(eventi["entrate"], eventi["uscite"], pausa_pranzo, attivita, eventi["rientro"], eventi["causali_uscita"], eventi["causali_entrata"])
                    totale_lavorato = self.calcola_totale_lavorato(eventi["entrate"], eventi["uscite"], pausa_pranzo, eventi["causali_uscita"], eventi["causali_entrata"])

                    self.aggiorna_contatori_annuali(eventi["causali_entrata"] + eventi["causali_uscita"])
                    self.aggiorna_totali_annuali_mensili(saldo, eventi["causali_entrata"] + eventi["causali_uscita"], chiave)

                    row = {
                        "Data": chiave.strftime('%d/%m/%Y'),
                        "Giorno della Settimana": giorno_settimana,
                        "Attività": attivita,
                        "Orario": orario,
                        "Totale Lavorato": str(totale_lavorato),
                        "Pausa Pranzo": str(pausa_pranzo),
                        "Saldo": str(saldo).replace("-1 day, ", "-"),
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
