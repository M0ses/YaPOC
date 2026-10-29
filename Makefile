test:
	GIT_CONFIG_GLOBAL=/dev/null python3 -m unittest discover -s tests -v

run_tests_in_kanku:
	kanku destroy||true
	kanku up --ll DEBUG > log/run_tests_in_kanku.log 2>&1

rtik: run_tests_in_kanku

.PHONY: test run_tests_in_kanku rtik
