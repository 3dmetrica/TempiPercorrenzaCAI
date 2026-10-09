"""
Tempi di percorrenza escursionistici secondo il diagramma CAI
(Schweizer Wanderwege 1986, riportato nel manuale CAI "Sentieri - Segnaletica", p. 66).
Funzione per il Function Editor di QGIS, gruppo "CAI".

Uso nel calcolatore di campi:
    tempo_cai(length($geometry), z(end_point($geometry)) - z(start_point($geometry)))
Restituisce i MINUTI necessari per percorrere il tratto.
  lunghezza  = distanza orizzontale in metri (quella che si misura sulla carta)
  dislivello = quota finale - quota iniziale in metri (+ salita, - discesa)
"""
from qgis.core import qgsfunction

# -----------------------------------------------------------------------------
# SCELTA 1 - Una tabella al posto di una formula.
# Lungo una pendenza costante le curve del diagramma sono equidistanti:
# il tempo cresce in proporzione alla distanza. Quindi tutto il diagramma
# si riassume in un numero per ogni pendenza: i minuti al km.
# I valori sono letti sul diagramma ogni 5% di pendenza, da -40% a +40%
# (il campo coperto dal diagramma).
# -----------------------------------------------------------------------------
TABELLA_CAI = [
    # pendenza %, minuti al km
    (-40, 36.4),
    (-35, 31.9),
    (-30, 27.5),
    (-25, 23.5),
    (-20, 19.8),
    (-15, 16.6),
    (-10, 14.2),
    (-5,  13.2),   # il punto piu' veloce: leggera discesa
    (0,   14.3),   # piano: 4,2 km/h
    (5,   16.6),
    (10,  20.0),
    (15,  25.2),
    (20,  32.3),
    (25,  40.1),
    (30,  48.5),
    (35,  58.4),
    (40,  66.9),
]


def minuti_al_km(pendenza):
    """Minuti al km per una pendenza in %, letti dalla tabella CAI."""
    # SCELTA 2 - Fuori dal diagramma (oltre +/-40%) si usa il valore al limite.
    # Alternative scartate: restituire NULL (un solo tratto ripido annullerebbe
    # la somma dell'intero sentiero) o estrapolare (inventare valori che il
    # diagramma non da'). Il tempo di quei tratti risulta sottostimato:
    # vanno contati e segnalati a parte.
    p_min, p_max = TABELLA_CAI[0][0], TABELLA_CAI[-1][0]
    p = max(p_min, min(p_max, pendenza))

    # SCELTA 3 - Interpolazione lineare tra le due righe vicine.
    # E' quello che fa l'occhio quando il punto cade tra due curve.
    # Errore rispetto alla lettura diretta: meno di 0,5 min/km.
    for (p0, v0), (p1, v1) in zip(TABELLA_CAI, TABELLA_CAI[1:]):
        if p0 <= p <= p1:
            return v0 + (v1 - v0) * (p - p0) / (p1 - p0)


# SCELTA 4 - La funzione riceve due numeri (lunghezza e dislivello), non una
# geometria. Cosi' si usa allo stesso modo su un segmento, dentro un'espressione
# che scorre i vertici di una linea, o con valori scritti a mano per le prove.
# group='CAI' crea il gruppo nella lista delle funzioni; referenced_columns=[]
# dice a QGIS che la funzione non legge campi della tabella attributi.
@qgsfunction(group='CAI', referenced_columns=[])
def tempo_cai(lunghezza, dislivello, feature, parent):
    """
    Tempo di percorrenza in minuti di un tratto di sentiero,
    secondo il diagramma CAI dei tempi di percorrenza.
    <h4>Sintassi</h4>
    tempo_cai(<i>lunghezza</i>, <i>dislivello</i>)
    <h4>Argomenti</h4>
    lunghezza: distanza orizzontale in metri<br>
    dislivello: quota finale - quota iniziale in metri
    <h4>Esempi</h4>
    tempo_cai(2000, 200) -> 40.0<br>
    tempo_cai(2000, -200) -> 28.4<br>
    tempo_cai(700, 0) -> 10.0
    """
    # SCELTA 5 - Dati mancanti o tratto di lunghezza nulla: nessun risultato,
    # invece di un errore che bloccherebbe il calcolatore di campi.
    if lunghezza is None or dislivello is None or lunghezza <= 0:
        return None

    # SCELTA 6 - Pendenza = dislivello / distanza ORIZZONTALE, come sugli assi
    # del diagramma. Il segno decide salita (+) o discesa (-): per il ritorno
    # basta invertire il dislivello.
    pendenza = dislivello / lunghezza * 100.0

    # SCELTA 7 - Si restituiscono minuti con i decimali, senza arrotondare.
    # Arrotondare ogni tratto di pochi metri azzererebbe quasi tutti i tempi:
    # l'arrotondamento si fa solo sul totale, come sui cartelli.
    return lunghezza / 1000.0 * minuti_al_km(pendenza)