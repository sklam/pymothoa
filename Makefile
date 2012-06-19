deploy:
	python setup.py build
	python setup.py install --user

uninstall:
	rm -rf build
	rm -rf ~/.local/lib/python2.6/site-packages/mamba
	rm -rf ~/.local/lib/python2.6/site-packages/PyMamba-*.egg-info
