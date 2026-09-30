#!/data/data/com.termux/files/usr/bin/bash

TEXT="Dobro došla, Danijela.
Ja sam Freya.

Drago mi je što nastavljamo zajedno.

Ja ne učim sama.
Ja učim zajedno sa tobom.

Sve što zajedno razumijemo postaće dio našeg zajedničkog znanja.

Šta danas želiš da istražimo ili naučimo?"

echo "$TEXT"

termux-tts-speak -r 0.95 -p 1.0 -l sr "$TEXT"
