'''I just hacked this to work for Ubuntu. May need to modify this file for other platform. 
'''
from distutils.core import setup, Extension
import os, sys

LLVM_CONFIG_PATH = 'llvm-config'

def llvm_config(args):
    return os.popen(LLVM_CONFIG_PATH+' '+args).read().rstrip()
    
def llvm_config_filter(args, prefix, strip=False):
    post = lambda X:X
    if strip: 
        post = lambda X: X[len(prefix):]
    return [post(i) for i in llvm_config(args).split(' ') if i.startswith(prefix)]
    
def llvm_config_macros():
    return [(i, None) for i in llvm_config_filter('--cxxflags', '-D', strip=True)]
    
def llvm_config_statis_lib():
    base = llvm_config('--libdir')
    return [base+os.sep+'lib'+i+'.a' for i in llvm_config_filter('--libs core jit native', '-l', strip=True)]

def list_file_with_extension(path, ext):
    return [path+os.sep+P for P in os.listdir(path) if P.endswith(ext)]

def create_llvm_wrapper():
    INC = ['.']+llvm_config_filter('--cxxflags', '-I', strip=True)
    SRC = list_file_with_extension('src', '.cpp') + list_file_with_extension('.', '.cxx')

    return Extension('llvm._llvm_wrapper', 
            #extra_compile_args=llvm_config_filter('--cxxflags', '-f'),
            define_macros = llvm_config_macros(),
            include_dirs = INC,
            extra_link_args = [llvm_config('--ldflags')],
            extra_objects = llvm_config_statis_lib(),
            language='c++',
            sources = SRC,
            )

ext_llvm_wrapper = create_llvm_wrapper()

setup (name = 'llvm_wrapper',
       version = '0.1',
       description = 'LLVM JIT binding',
       author = 'Siu Kwan Lam',    
       py_modules = ['llvm_wrapper'],
       ext_modules = [ext_llvm_wrapper])

