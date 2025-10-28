# --- Voci e parametri predefiniti ---
PRESTAZIONE_BASE = 58.82
CONTRIBUTO_FISSO_PER_SEDUTA = 1.18
BOLLO_COSTO = 2.00
BOLLO_SOGLIA = 77.47

def calculate_invoice_totals(numero_sedute: float):
    """
    Calcola i totali usando la logica desiderata.
    Supporta sia interi che frazioni (es: 1.5, 2.5, ecc.)
    """
    if numero_sedute < 0:
        numero_sedute = 0

    # Converte a float per assicurare operazioni in virgola mobile
    numero_sedute = float(numero_sedute)
    
    prezzo_base_unitario = PRESTAZIONE_BASE
    contributo_unitario = CONTRIBUTO_FISSO_PER_SEDUTA
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
