#include "llvm_wrapper.hpp"

using namespace llvm;

Value * ConstantFactory::make_int(Type * ty, unsigned long long val){
    return ConstantInt::get(ty, val);
}

Value * ConstantFactory::make_int_signed(Type * ty, unsigned long long val){
    return ConstantInt::get(ty, val, true);
}

Value * ConstantFactory::make_real(Type * ty, double val){
    return ConstantFP::get(ty, val);
}


