1) Клонируем РЕПО
2) созадем виртуальное окружение python3 -m venv .venv
3) активируем вируальное окружение source .venv/bin/activate
4) pip install -r requirements.txt
5) скачиваем модель в папку ggufs https://huggingface.co/yandex/YandexGPT-5-Lite-8B-instruct-GGUF/tree/main (5Гб)
6) создаем контейнер  docker build -t ollama-yandex .
7) запускаем docker run -d -p 11436:11434   -v $(pwd)/ggufs:/ggufs   -v $(pwd)/modelfiles:/modelfiles:ro   --name ollama-container ollama-yandex
   Без флага --gpus all - Контейнеры по умолчанию не видят GPU, таким образом получаем искомый CPU инференс
8) Последовательно идем по шагам solution.ipynb
