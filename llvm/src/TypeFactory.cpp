#include "llvm_wrapper.hpp"

using namespace llvm;

Type * TypeFactory::make_int(unsigned int bit){
    return Type::getIntNTy(getGlobalContext(), bit);
}

Type * TypeFactory::make_int(){
    return TypeFactory::make_int(32);
}

Type * TypeFactory::make_float(){
    return Type::getFloatTy(getGlobalContext());
}

Type * TypeFactory::make_double(){
    return Type::getDoubleTy(getGlobalContext());
}

Type * TypeFactory::make_void(){
    return Type::getVoidTy(getGlobalContext());
}

