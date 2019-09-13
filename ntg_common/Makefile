.PHONY: clean pylint

PY_SOURCES := *.py

pylint:
	-pylint --rcfile=../pylintrc .

clean:
	rm -f *~
	rm -f pylintgraph.dot
	rm -rf __pycache__
