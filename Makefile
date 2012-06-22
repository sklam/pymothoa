deploy:
	python setup.py build
	python setup.py install --user

uninstall:
	rm -rf build
	rm -rf ~/.local/lib/python2.6/site-packages/pymothoa
	rm -rf ~/.local/lib/python2.6/site-packages/Pymothoa-*.egg-info
