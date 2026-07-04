FROM ollama/ollama:latest

# Копируем скрипт для автоматического создания модели
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

EXPOSE 11436
ENTRYPOINT ["/entrypoint.sh"]