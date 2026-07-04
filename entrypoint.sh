#!/bin/sh
ollama serve &

sleep 5

for modelfile in /modelfiles/Modelfile.*; do
    model_name=$(basename "$modelfile" | sed 's/^Modelfile\.//')
    echo "Creating model: $model_name from $modelfile"
    ollama create "$model_name" -f "$modelfile"
done

# Оставляем работающим
wait