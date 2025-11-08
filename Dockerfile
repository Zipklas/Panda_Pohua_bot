# Используем официальный Python образ
FROM python:3.12-slim

# Рабочая директория в контейнере
WORKDIR /app

# Копируем файлы проекта
COPY . .

# Устанавливаем зависимости
RUN pip install --no-cache-dir -r requirements.txt

# Открываем бота
CMD ["python", "main.py"]