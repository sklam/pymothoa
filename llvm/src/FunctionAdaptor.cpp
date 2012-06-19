#include "llvm_wrapper.hpp"
#include "llvm/Support/raw_ostream.h"
#include <cassert>
#include <algorithm>

#define EnsureFunctionValid assert(valid() && "Function is not valid");

FunctionAdaptor::FunctionAdaptor(llvm::Function * fp)
    : func_(fp)
{   }


const char * FunctionAdaptor::name() const{
    EnsureFunctionValid;
    return func_->getName().data();
}

bool FunctionAdaptor::valid() const {
    return func_!=0;
}

FunctionAdaptor::operator bool () const{
    return valid();
}

std::string FunctionAdaptor::dump() const {
    if (valid()){
        std::string buf;
        llvm::raw_string_ostream oss(buf);
        func_->print(oss);
        return oss.str();
    }else{
        return "<invalid function>";
    }
}

llvm::Function * FunctionAdaptor::get_function() const {
    return func_;
}

llvm::BasicBlock * FunctionAdaptor::append_basic_block(const char name[]) {
    using namespace llvm;
    EnsureFunctionValid;
    return BasicBlock::Create(getGlobalContext(), name, func_);
}

std::vector<llvm::Value*> FunctionAdaptor::arguments() const{
    EnsureFunctionValid;
    typedef llvm::Function::arg_iterator arg_iterator;

    std::vector<llvm::Value*> args;
    args.reserve(arg_size());
    for(arg_iterator i=func_->arg_begin(); i!=func_->arg_end(); ++i){
        args.push_back(&*i);
    }
    return args;
}

unsigned int FunctionAdaptor::arg_size() const{
    EnsureFunctionValid;
    return func_->arg_size();
}

bool FunctionAdaptor::verify() const {
    EnsureFunctionValid;
    return not llvm::verifyFunction(*func_);
}
