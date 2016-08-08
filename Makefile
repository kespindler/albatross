COVERAGE=97
TEST=nosetests -s --with-coverage --cover-package=albatross --cover-branches $(TARGET)

upload:
	git push
	python3 setup.py sdist bdist_wheel upload

test:
	$(TEST) --cover-min-percentage $(COVERAGE)

cover:
	$(TEST) --cover-html
	which open && open cover/index.html

.PHONY: cover
