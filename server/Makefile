.PHONY: pylint clean

PY_SOURCES := *.py

pylint:
	-pylint --rcfile=../pylintrc .

clean:
	rm -f *~
	rm -f templates/*~
	rm -f pylintgraph.dot
	rm -rf __pycache__
