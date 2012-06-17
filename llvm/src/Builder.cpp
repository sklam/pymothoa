#include "llvm_wrapper.hpp"

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

Value * Builder::icmp(int op, Value * lhs, Value * rhs, const char * name){
    return builder_.CreateICmp((llvm::CmpInst::Predicate)op, lhs, rhs, name);
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


bool Builder::is_block_closed(){
    return get_basic_block()->getTerminator()!=0;
}
    
