## Бот для проверки статуса ревью при использовании API Яндекс Практикум

Телеграмм бот в автоматическом режиме каждые 10 минут направляет запрос к API сервису ЯП и получении ответа сравнивает статус проекта, находящегося на ревью с последним полученным ответом. При наличии изменений Телеграмм бот отправляет сообщение об изменении (проект принят на ревью, возвращен с правками или принят) в телеграмм чат.

В проекте реализовано логирование ошибок. Об ошибках бот также отправляет сообщение в телеграмм чат.
