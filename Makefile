test:
	python3 -m unittest discover -s tests -v

run_tests_in_kanku:
	kanku destroy || true
	kanku up --ll DEBUG 2>&1 |tee log/run_tests_in_kanku.log

rtik: run_tests_in_kanku

.PHONY: test run_tests_in_kanku rtik
