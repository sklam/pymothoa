# Generate SWIG interface file from C++ header
all: build_wrapper

build_wrapper:
	python tools/swig.py llvm_wrapper.hpp llvm_wrapper.i
	swig -Wall -c++ -python llvm_wrapper.i

clean:
	rm -f sip*.cpp sip*.h
	rm -f llvm_wrapper_wrap.cxx

