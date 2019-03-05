build:
	python setup.py bdist_wheel

install:
	pip install dist/*.whl

test:
	pip install requests itsdangerous==1.1.0
	python -m tests.test_kalos &
	python -m tests.test_api