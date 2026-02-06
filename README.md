Для запуска тестов в корневой директории:
```python -m pytest tests```

Для инициализации бд:
```
cd db 
pgmigrate -t latest  migrate
```

Для запуска kafka:
```docker-compose up -d```

Запуск воркера:
```python -m workers.moderation_worker```
