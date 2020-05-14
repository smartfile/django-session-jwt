.venv: Pipfile
	PIPENV_VENV_IN_PROJECT="enabled" pipenv install
	touch .venv

test: .venv
	pipenv run coverage run manage.py test django_session_jwt

ci:
	coverage run manage.py test django_session_jwt

install:
	python setup.py install
