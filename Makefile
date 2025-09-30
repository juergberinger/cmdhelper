# Makefile for cmdhelper.py

PKGNAME = cmdhelper
CURRENTVERSION = `python -c 'import $(PKGNAME); print($(PKGNAME).__version__)'`

build:
	@echo 'Building ...'
	@python3 -m build
	@echo ''
	@echo 'Testing installation ...'
	@python3 -m venv --clear dist_test
	@. dist_test/bin/activate; cd dist_test; python -m pip install ../dist/`ls -tr ../dist | tail -1`; python -m pip show $(PKGNAME); python -c 'import $(PKGNAME); print("\nFound version",$(PKGNAME).__version__)'
	@rm -rf dist_test

newversion:
	@bumpversion patch
	@python3 -c 'import $(PKGNAME); print("New version is",$(PKGNAME).__version__)'

test-upload: build
	@echo ''
	@echo 'Uploading to TEST PyPI ...'
	@twine upload --repository cmdhelper-test dist/*$(CURRENTVERSION)*
	@echo ''
	@echo 'Testing installation from test PyPI ...'
	@python3 -m venv --clear dist_test
	@. dist_test/bin/activate; cd dist_test; python -m pip install -i https://test.pypi.org/simple  --extra-index-url https://pypi.org/simple $(PKGNAME); python -m pip show $(PKGNAME); python -c 'import $(PKGNAME); print("\nFound version",$(PKGNAME).__version__)'
	@rm -rf dist_test
	@firefox https://test.pypi.org/project/$(PKGNAME)/

upload: build
	@echo ''
	@echo 'Uploading to PyPI ...'
	@twine upload --repository cmdhelper-pypi dist/*$(CURRENTVERSION)*
	@echo ''
	@echo 'Testing installation from PyPI ...'
	@python3 -m venv --clear dist_test
	@. dist_test/bin/activate; cd dist_test; python -m pip install $(PKGNAME); python -m pip show $(PKGNAME); python -c 'import $(PKGNAME); print("\nFound version",$(PKGNAME).__version__)'
	@rm -rf dist_test
	@firefox https://pypi.org/project/$(PKGNAME)/

tag:
	@echo 'Commit and tag new version ...'
	@git diff
	@git commit -a -m "Version $(CURRENTVERSION)"
	@git tag -a -m "v$(CURRENTVERSION) as uploaded to PyPI" v$(CURRENTVERSION)
	@git push
	@git push origin v$(CURRENTVERSION)
	@firefox https://github.com/juergberinger/$(PKGNAME)
