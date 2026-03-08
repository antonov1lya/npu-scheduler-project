# NPU Task Scheduler

Проект для планирования задач на **NPU** 

## 🚀 Gradio Demo

Веб-интерфейс позволяет:

- загрузить `input.txt` (тестовый файл находится в директории example)
- запустить планировщик
- посмотреть график выполнения
- скачать `output.txt`
- скачать PNG графика


### 🐳 Запуск через Docker

Сборка и запуск контейнера:

```
docker build -f gradio_demo/Dockerfile -t npu-demo .
docker run -it --rm -p 7860:7860 npu-demo
```

После запуска интерфейс будет доступен по адресу:
```
http://localhost:7860
```
### Локальный запуск
Сборка:
```
mkdir build
cd build
cmake .. && make
```
Установка python зависимостей:
```
pip install gradio matplotlib
```
Запсук демо:
```
python gradio_demo/demo.py
```