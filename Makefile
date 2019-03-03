build:
	python setup.py bdist_wheel

install:
	pip install dist/*.whl

test:
    python -m tests.test_httpY