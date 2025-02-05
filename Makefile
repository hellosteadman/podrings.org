run:
	@npm run build
	@python manage.py migrate
	@python manage.py runserver 0.0.0.0:8000

work:
	@python manage.py rqworker

test:
	@DEBUG=0 coverage run --source podrings manage.py test podrings
	@coverage html
	@rm .coverage

reset:
	@cp db.sqlite db.sqlite.bak && \
		python manage.py dumpdata community creative | python -m json.tool > data.json && \
		python manage.py migrate creative zero && \
		rm podrings/**/migrations/*.py

migrate:
	@python manage.py makemigrations creative && \
		python manage.py makemigrations community && \
		python manage.py migrate && \
		python manage.py loaddata data.json && \
		rm db.sqlite.bak && \
		rm data.json
