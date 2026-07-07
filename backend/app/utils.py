from datetime import date

from app.timezone import today_local

# --- Voci e parametri predefiniti ---
PRESTAZIONE_BASE = 58.82
CONTRIBUTO_PERCENTUALE = 0.02  # 2% - contributo calcolato sul prezzo base
BOLLO_COSTO = 2.00
BOLLO_SOGLIA = 77.47

# Omocodia: lettere sostitutive delle cifre nelle posizioni numeriche del CF
_CF_OMOCODIA = {'L': '0', 'M': '1', 'N': '2', 'P': '3', 'Q': '4',
                'R': '5', 'S': '6', 'T': '7', 'U': '8', 'V': '9'}
_CF_MESI = {'A': 1, 'B': 2, 'C': 3, 'D': 4, 'E': 5, 'H': 6,
            'L': 7, 'M': 8, 'P': 9, 'R': 10, 'S': 11, 'T': 12}


def _cf_digit(char: str) -> int:
    if char.isdigit():
        return int(char)
    return int(_CF_OMOCODIA[char.upper()])


def decode_codice_fiscale(codice_fiscale: str, oggi: date = None):
    """
    Decodifica sesso e data di nascita da un codice fiscale italiano.
    Gestisce anche i codici con omocodia. Il luogo di nascita non viene
    decodificato (richiederebbe la tabella dei codici catastali).

    Args:
        codice_fiscale: il CF da decodificare.
        oggi: data di riferimento per l'euristica del secolo (default: oggi).
            Iniettabile per rendere la funzione deterministica nei test.

    Ritorna {'sesso': 'M'|'F', 'data_nascita': date} oppure None se il
    codice non è decodificabile.
    """
    try:
        cf = (codice_fiscale or '').strip().upper()
        if len(cf) != 16:
            return None
        if oggi is None:
            oggi = today_local()
        anno = _cf_digit(cf[6]) * 10 + _cf_digit(cf[7])
        mese = _CF_MESI[cf[8]]
        giorno = _cf_digit(cf[9]) * 10 + _cf_digit(cf[10])
        sesso = 'F' if giorno > 40 else 'M'
        if giorno > 40:
            giorno -= 40
        # Secolo: se l'anno a due cifre supera quello corrente si assume il 1900
        anno_corrente = oggi.year % 100
        anno += 2000 if anno <= anno_corrente else 1900
        return {'sesso': sesso, 'data_nascita': date(anno, mese, giorno)}
    except (KeyError, ValueError):
        return None


def format_numero_sedute(numero: float) -> str:
    """
    Formatta il numero di sedute in modo intelligente:
    - Se intero (1.0, 2.0) -> "1", "2"
    - Se decimale (1.5, 2.5) -> "1,5", "2,5" (con virgola italiana)
    """
    if numero % 1 == 0:  # È un numero intero
        return str(int(numero))
    else:
        # Usa :g per rimuovere zeri trailing, sostituisce punto con virgola
        return f"{numero:g}".replace('.', ',')

def calculate_prezzo_base_da_totale(prezzo_totale_unitario: float) -> float:
    """
    Converte il prezzo totale inserito dall'utente (es. 60€, 65€, 70€) 
    nel prezzo base, sottraendo il contributo proporzionale del 2%.
    
    Formula: prezzo_base = prezzo_totale / (1 + CONTRIBUTO_PERCENTUALE)
    
    Esempio:
        60€ -> 58.82€
        65€ -> 63.73€
        70€ -> 68.63€
    """
    return prezzo_totale_unitario / (1 + CONTRIBUTO_PERCENTUALE)

def calculate_invoice_totals(numero_sedute: float, prezzo_base_unitario: float = None):
    """
    Calcola i totali usando la logica desiderata.
    Supporta sia interi che frazioni (es: 1.5, 2.5, ecc.)
    
    Args:
        numero_sedute: Numero di sedute (può essere decimale)
        prezzo_base_unitario: Prezzo base per seduta (opzionale, default PRESTAZIONE_BASE)
    """
    if numero_sedute < 0:
        numero_sedute = 0

    # Converte a float per assicurare operazioni in virgola mobile
    numero_sedute = float(numero_sedute)
    
    # Usa il prezzo base fornito o quello di default
    if prezzo_base_unitario is None:
        prezzo_base_unitario = PRESTAZIONE_BASE
    
    # Calcola il contributo proporzionale (2% del prezzo base)
    contributo_unitario = prezzo_base_unitario * CONTRIBUTO_PERCENTUALE
    totale_unitario = round(prezzo_base_unitario + contributo_unitario, 2)

    # Calcoli con supporto per frazioni
    subtotale_base = round(prezzo_base_unitario * numero_sedute, 2)
    contributo = round(contributo_unitario * numero_sedute, 2)
    totale_imponibile = round(subtotale_base + contributo, 2)

    bollo_flag = totale_imponibile > BOLLO_SOGLIA
    bollo_importo = BOLLO_COSTO if bollo_flag else 0.0

    totale = round(totale_imponibile + bollo_importo, 2)

    return {
        'numero_sedute': numero_sedute,
        'importo_unitario': prezzo_base_unitario,
        'contributo_unitario': contributo_unitario,
        'totale_unitario': totale_unitario,
        'subtotale_base': subtotale_base,
        'contributo': contributo,
        'bollo_flag': bollo_flag,
        'bollo_importo': bollo_importo,
        'totale_imponibile': totale_imponibile,
        'totale': totale
    }
