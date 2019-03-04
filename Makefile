build:
	python setup.py bdist_wheel

install:
	pip install dist/*.whl

test:
	pip install requests
	python -m tests.test_kalos &
	python -m tests.test_api