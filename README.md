## A bot for checking the review status when using the Yandex Practicum API.

A Telegram bot operates automatically, sending a request to the Yandex Practicum API every 10 minutes. Upon receiving a response, it compares the status of the project under review with the last received response. If there are changes, the Telegram bot sends a message to the Telegram chat regarding the change (project accepted for review, returned with amendments, or accepted).

Error logging is implemented in the project. The bot also sends a message to the Telegram chat about any errors encountered.
