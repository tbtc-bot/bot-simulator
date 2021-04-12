# bot-simulator
Simulatore del bot Griglia4Terrabitcoin

## Installazione
- Creare un ambiente Python e installare le dipendenze elencate nel file env.yml. Il modo più semplice è installare Anaconda.

- Inserire i parametri desiderati nel file configuration.xml e salvare le modifiche.

- Aprire una console o un IDE Python ed eseguire il file main.py. Se si ha scelto una finestra temporale di mesi ci può volere qualche minuto per scaricare il dataset.

- I risultati vengono salvati nella cartella dataset, ordinati per data della simulazione. In particolare viene salvato un file .csv con i prezzi del token, un file .csv con i risultati numerici, e due grafici .png per ogni simulazione.


NOTA:
Se si avvia una simulazione ed è presenta già il corrispondente dataset, il programma evita di scaricarlo nuovamente ma lo carica direttamente. Stessa cosa per i risultati numerici di una simulazione.


Nota sui parametri di configurazione:
- Symbol: formato del tipo BTCUSDT
- BuySell: tipo di strategia. Valori ammissibili: BOTH, LONG
