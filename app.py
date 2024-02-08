import tkinter as tk
from tkinter import filedialog
from elasticsearch import Elasticsearch
from elasticsearch import helpers
import json

# Файл для хранения предыдущих значений
config_file = "config.json"

# Загружаем предыдущие значения, если они есть
try:
    with open(config_file, 'r') as f:
        config = json.load(f)
except FileNotFoundError:
    config = {}

def save_config():
    # Сохраняем текущие значения
    config['index_name'] = index_entry.get()
    config['elasticsearch_host'] = host_entry.get()

    # Записываем их в файл
    with open(config_file, 'w') as f:
        json.dump(config, f)

def index_logs(log_file, index_name, host, token, progress_var):
    es = Elasticsearch(
        [host],
        headers={"Authorization": f"Bearer {token}"},
        use_ssl=True,
        ca_certs='ca.crt',  # Путь к корневому сертификату CA
        cert='client.crt',  # Путь к сертификату клиента
        key='client.key'  # Путь к закрытому ключу клиента
    )

    # Создаем индекс, если его нет
    es.indices.create(index=index_name, ignore=400)

    # Открываем файл логов и читаем строки
    with open(log_file, 'r') as file:
        lines = file.readlines()

    # Подготавливаем данные для индексации
    actions = []
    total_lines = len(lines)

    for idx, line in enumerate(lines, start=1):
        log_data = {'message': line}
        action = {'_op_type': 'index', '_index': index_name, '_source': log_data}
        actions.append(action)

        # Обновляем полосу прогресса
        progress_value = (idx / total_lines) * 100
        progress_var.set(progress_value)
        root.update()

    # Индексируем данные в Elasticsearch с помощью bulk API
    helpers.bulk(es, actions)

def browse_file():
    file_path = filedialog.askopenfilename(filetypes=[("Log files", "*.log")])
    file_entry.delete(0, tk.END)
    file_entry.insert(tk.END, file_path)

def index_logs_from_gui():
    log_file = file_entry.get()
    index_name = index_entry.get()
    elasticsearch_host = host_entry.get()
    token = token_entry.get()

    if log_file and index_name and elasticsearch_host and token:
        # Создаем прогресс-бар
        progress_var = tk.DoubleVar()
        progress = tk.ttk.Progressbar(root, variable=progress_var, length=200, mode="determinate")
        progress.pack(pady=20)

        index_logs(log_file, index_name, elasticsearch_host, token, progress_var)
        result_label.config(text="Логи успешно загружены в Elasticsearch.")
        # Сохраняем текущие значения полей
        save_config()
    else:
        result_label.config(text="Заполните все поля.")

# Создание главного окна
root = tk.Tk()
root.title("Elasticsearch Log Uploader")

# Создание и настройка элементов управления
file_label = tk.Label(root, text="Выберите лог-файл:")
file_label.pack(pady=10)

file_entry = tk.Entry(root, width=50)
file_entry.pack(pady=10)

browse_button = tk.Button(root, text="Обзор", command=browse_file)
browse_button.pack(pady=10)

index_label = tk.Label(root, text="Имя индекса:")
index_label.pack(pady=10)

index_default = config.get('index_name', '')  # Значение по умолчанию из предыдущего ввода
index_entry = tk.Entry(root, width=50)
index_entry.insert(0, index_default)  # Установка значения по умолчанию
index_entry.pack(pady=10)

host_label = tk.Label(root, text="Хост Elasticsearch:")
host_label.pack(pady=10)

host_default = config.get('elasticsearch_host', '')  # Значение по умолчанию из предыдущего ввода
host_entry = tk.Entry(root, width=50)
host_entry.insert(0, host_default)  # Установка значения по умолчанию
host_entry.pack(pady=10)

token_label = tk.Label(root, text="Токен авторизации:")
token_label.pack(pady=10)

token_entry = tk.Entry(root, width=50)
token_entry.pack(pady=10)

upload_button = tk.Button(root, text="Загрузить в Elasticsearch", command=index_logs_from_gui)
upload_button.pack(pady=20)

result_label = tk.Label(root, text="")
result_label.pack(pady=10)

# Запуск главного цикла
root.mainloop()
