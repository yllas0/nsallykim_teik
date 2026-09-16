.PHONY: setup pipeline dashboard

setup:
	pip install -r requirements.txt

pipeline:
	python load_data.py
	python part2.py
	python part3.py
	python part4.py

dashboard:
	python dashboard.py