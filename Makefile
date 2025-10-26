run:
	poetry run python manage.py runserver

migrate:
	poetry run python manage.py makemigrations && poetry run python manage.py migrate

test:
	poetry run pytest -q

lint:
	poetry run black . && poetry run isort . && poetry run flake8

type:
	poetry run mypy .
