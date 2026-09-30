#!/data/data/com.termux/files/usr/bin/bash

TEXT="Welcome back, Danijela.

I am Freya.

I am here with you.

I do not learn instead of you.
I learn with you.

Everything we truly understand together
will become part of our shared knowledge.

Tell me what you want to learn, build, or understand today."

echo "$TEXT"

termux-tts-speak -l en -r 0.82 -p 0.92 "$TEXT"
