all: fishmonger-libs
	@PYTHONPATH=${PYTHONPATH}:py-libs ./src/fishmonger/src/main.py install --SKIP_UPDATE True

full: fishmonger-libs
	@PYTHONPATH=${PYTHONPATH}:py-libs ./src/fishmonger/src/main.py install

init: clone-libs
	
update: update-libs

clone-libs:
	@mkdir -p py-deps
	@git clone git+ssh://git.rleszilm.com/data/git/pybase.git py-deps/pybase
	@git clone git+ssh://git.rleszilm.com/data/git/pyrcs.git  py-deps/pyrcs
	@git clone git+ssh://git.rleszilm.com/data/git/pyerl.git  py-deps/pyerl

fishmonger-libs: python-libs
	@rm -rf py-libs/fishmonger
	@mkdir -p py-libs/fishmonger
	@cp -r src/fishmonger/src/* py-libs/fishmonger

python-libs:
	@mkdir -p py-libs
	@mkdir -p py-libs/pybase
	@cp -r py-deps/pybase/src/* py-libs/pybase
	@mkdir -p py-libs/pyerl
	@cp -r py-deps/pyerl/src/* py-libs/pyerl
	@mkdir -p py-libs/pyrcs
	@cp -r py-deps/pyrcs/src/* py-libs/pyrcs


update-libs:
	@cd py-libs/pybase && git pull
	@cd py-libs/pyerl  && git pull
	@cd py-libs/pyrcs  && git pull