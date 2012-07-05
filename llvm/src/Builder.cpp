/**
Copyright (c) 2012, Siu Kwan Lam
All rights reserved.
**/

#include "llvm_wrapper.hpp"
#include "llvm/Intrinsics.h"

Builder::Builder()
    : builder_(llvm::getGlobalContext())
{
    //empty
}

void Builder::insert_at(llvm::BasicBlock * bb){
    builder_.SetInsertPoint(bb);
}

llvm::BasicBlock * Builder::get_basic_block() const {
    return builder_.GetInsertBlock();
}


using llvm::Value;

Value * Builder::phi(llvm::Type* type, std::vector<llvm::BasicBlock*> in_blocks, std::vector<Value*> in_values, const char* name){
    using namespace llvm;
    assert(in_blocks.size()==in_values.size());
    const unsigned int N = in_blocks.size();
    PHINode * node = builder_.CreatePHI(type, N, name);
    for(unsigned int i=0; i<N; ++i){
        node->addIncoming(in_values[i], in_blocks[i]);
    }
    return node;
}

// instrinsic
Value * Builder::intrinsic_pow(Value * val, Value * power, const char * name){
    using namespace llvm;

    llvm::Module * M = builder_.GetInsertBlock()->getParent()->getParent();

    // Automatically determine the use of pow or powi
    Intrinsic::ID id;
    if ( power->getType()->isIntegerTy() ){
        id = Intrinsic::powi;
    }else{
        id = Intrinsic::pow;
    }

    Function * function = Intrinsic::getDeclaration(M, id, val->getType());

    assert(0!=fnty && "Cannot get intrinsic");

    Value * args[] = { val, power };

    return builder_.CreateCall(function, args, name);
}

// bitwise operations

Value * Builder::bitwise_and(Value * lhs, Value * rhs, const char * name){
    return builder_.CreateAnd(lhs, rhs, name);
}

Value * Builder::bitwise_or(Value * lhs, Value * rhs, const char * name){
    return builder_.CreateOr(lhs, rhs, name);
}

Value * Builder::bitwise_xor(Value * lhs, Value * rhs, const char * name){
    return builder_.CreateXor(lhs, rhs, name);
}

Value * Builder::bitwise_not(Value * val, const char * name){
    return builder_.CreateNot(val, name);
}

Value * Builder::shl(Value * value, Value * amt, const char * name){
    return builder_.CreateShl(value, amt, name);
}

Value * Builder::lshr(Value * value, Value * amt, const char * name){
    return builder_.CreateLShr(value, amt, name);
}

Value * Builder::ashr(Value * value, Value * amt, const char * name){
    return builder_.CreateAShr(value, amt, name);
}

// integer operations

Value * Builder::add(Value * lhs, Value * rhs, const char * name){
    return builder_.CreateAdd(lhs, rhs, name);
}

Value * Builder::sub(Value * lhs, Value * rhs, const char * name){
    return builder_.CreateSub(lhs, rhs, name);
}

Value * Builder::mul(Value * lhs, Value * rhs, const char * name){
    return builder_.CreateMul(lhs, rhs, name);
}

Value * Builder::sdiv(Value * lhs, Value * rhs, const char * name){
    return builder_.CreateSDiv(lhs, rhs, name);
}

Value * Builder::udiv(Value * lhs, Value * rhs, const char * name){
    return builder_.CreateUDiv(lhs, rhs, name);
}

Value * Builder::umod(Value * lhs, Value * rhs, const char * name){
    return builder_.CreateURem(lhs, rhs, name);
}

Value * Builder::smod(Value * lhs, Value * rhs, const char * name){
    return builder_.CreateSRem(lhs, rhs, name);
}

Value * Builder::icmp(int op, Value * lhs, Value * rhs, const char * name){
    return builder_.CreateICmp((llvm::CmpInst::Predicate)op, lhs, rhs, name);
}

Value * Builder::negative(Value * value, const char * name){
    return builder_.CreateNeg(value, name);
}

// float operations

Value * Builder::fadd(Value * lhs, Value * rhs, const char * name){
    return builder_.CreateFAdd(lhs, rhs, name);
}

Value * Builder::fsub(Value * lhs, Value * rhs, const char * name){
    return builder_.CreateFSub(lhs, rhs, name);
}

Value * Builder::fmul(Value * lhs, Value * rhs, const char * name){
    return builder_.CreateFMul(lhs, rhs, name);
}

Value * Builder::fdiv(Value * lhs, Value * rhs, const char * name){
    return builder_.CreateFDiv(lhs, rhs, name);
}

Value * Builder::fmod(Value * lhs, Value * rhs, const char * name){
    return builder_.CreateFRem(lhs, rhs, name);
}

Value * Builder::fcmp(int op, Value * lhs, Value * rhs, const char * name){
    return builder_.CreateFCmp((llvm::CmpInst::Predicate)op, lhs, rhs, name);
}

// casting operations

Value * Builder::icast(Value * val, llvm::Type * ty, bool is_signed, const char * name){
    return builder_.CreateIntCast(val, ty, is_signed, name);
}

Value * Builder::fcast(Value * val, llvm::Type * ty, const char * name){
    return builder_.CreateFPCast(val, ty, name);
}

Value * Builder::sitofp(Value * val, llvm::Type * ty, const char * name){
    return builder_.CreateSIToFP(val, ty, name);
}

Value * Builder::fptosi(Value * val, llvm::Type * ty, const char * name){
    return builder_.CreateFPToSI(val, ty, name);
}

Value * Builder::uitofp(Value * val, llvm::Type * ty, const char * name){
    return builder_.CreateUIToFP(val, ty, name);
}

Value * Builder::fptoui(Value * val, llvm::Type * ty, const char * name){
    return builder_.CreateFPToUI(val, ty, name);
}

// control-flow operations

void Builder::ret(Value * retval){
    builder_.CreateRet(retval);
}

void Builder::ret_void(){
    builder_.CreateRetVoid();
}

void Builder::branch(llvm::BasicBlock * bb){
    builder_.CreateBr(bb);
}

void Builder::cond_branch(Value * Cond, llvm::BasicBlock * bb_true, llvm::BasicBlock * bb_false){
    builder_.CreateCondBr(Cond, bb_true, bb_false);
}

Value * Builder::alloc(llvm::Type * ty, const char * name){
    return builder_.CreateAlloca(ty, 0, name);
}

Value * Builder::alloc_array(llvm::Type * ty, Value * ct, const char * name){
    return builder_.CreateAlloca(ty, ct, name);
}

Value * Builder::load(Value * ptr, const char * name){
    return builder_.CreateLoad(ptr, name);
}

Value * Builder::store(Value * val, Value * ptr){
    return builder_.CreateStore(val, ptr);
}

Value * Builder::call(FunctionAdaptor func, std::vector<Value*> args, const char * name){
    return builder_.CreateCall(func.get_function(), args, name);
}


void Builder::unreachable(){
    builder_.CreateUnreachable();
}

// pointer function

Value * Builder::gep(Value * ptr, Value * idx, const char * name){
    return builder_.CreateGEP(ptr, idx, name);
}

Value * Builder::gep2(Value * ptr, std::vector<Value*> indices, const char * name){
    return builder_.CreateGEP(ptr, indices, name);
}

// vector function

Value * Builder::extract_element(Value * vector, Value * idx, const char * name){
    return builder_.CreateExtractElement(vector, idx, name);
}

Value * Builder::insert_element(Value * vector, Value * newvalue, Value * idx, const char * name){
    return builder_.CreateInsertElement(vector, newvalue, idx, name);
}

bool Builder::is_block_closed(){
    return get_basic_block()->getTerminator()!=0;
}

