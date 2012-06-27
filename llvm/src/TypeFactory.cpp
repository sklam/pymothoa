/**
Copyright (c) 2012, Siu Kwan Lam
All rights reserved.
**/

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

Type * TypeFactory::make_pointer(Type * elemty){
    return PointerType::getUnqual(elemty);
}

Type * TypeFactory::make_vector(Type * elemty, unsigned int elemct){
    return VectorType::get(elemty, elemct);
}

