.venv: Pipfile
	PIPENV_VENV_IN_PROJECT="enabled" pipenv install
	touch .venv

test: .venv
	pipenv run coverage run manage.py test django_session_jwt

lint: .venv
	pipenv run pylint django_session_jwt --ignore=settings.py,models.py,admin.py,urls.py,wsgi.py,apps.py

ci:
	coverage run manage.py test django_session_jwt

install:
	python setup.py install
