#include "llvm_wrapper.hpp"
#include "llvm/Support/raw_ostream.h"

JITEngine::JITEngine()
    : module_(0), ee_(0), last_error_("no error")
{
    // Reference: Kaleidoscope: Adding JIT and Optimizer Support
    //            http://llvm.org/docs/tutorial/LangImpl4.html
    using namespace llvm;   
    InitializeNativeTarget();
    LLVMContext & Context = getGlobalContext();

    module_ = new Module("default", Context);

    // Create the JIT.  This takes ownership of the module.
    std::string ErrStr;
    ee_ = EngineBuilder(module_).setErrorStr(&ErrStr).create();
    if (!ee_) {
        std::cerr << "Could not create ExecutionEngine: " << ErrStr << std::endl;
        exit(1);    // Abort.
    }

    fpm_ = new FunctionPassManager(module_);

    // Set up the optimizer pipeline.  Start with registering info about how the
    // target lays out data structures.
    fpm_->add(new TargetData(*ee_->getTargetData()));
    // Promote allocas to registers.
    fpm_->add(createPromoteMemoryToRegisterPass());
    // Provide basic AliasAnalysis support for GVN.
    fpm_->add(createBasicAliasAnalysisPass());
    // Do simple "peephole" optimizations and bit-twiddling optzns.
    fpm_->add(createInstructionCombiningPass());
    // Reassociate expressions.
    fpm_->add(createReassociatePass());
    // Eliminate Common SubExpressions.
    fpm_->add(createGVNPass());
    // Simplify the control flow graph (deleting unreachable blocks, etc).
    fpm_->add(createCFGSimplificationPass());
    // Eliminate tail recursion
    fpm_->add(createTailCallEliminationPass());

    fpm_->doInitialization();
}

JITEngine::~JITEngine(){
    delete ee_;
    delete fpm_;
    // do not delete module_ because it is owned by the execution engine.
}

std::string JITEngine::dump(){
    std::string buf;
    llvm::raw_string_ostream oss(buf);
    module_->print(oss, 0);
    return oss.str();
}

FunctionAdaptor JITEngine::make_function(const char name[], llvm::Type *result, std::vector<llvm::Type*> params){
    // Reference: Kaleidoscope: Adding JIT and Optimizer Support
    //            http://llvm.org/docs/tutorial/LangImpl4.html
    using namespace llvm;
    FunctionType * fnty = FunctionType::get(result, params, false);
    Function * func = Function::Create(fnty, Function::ExternalLinkage, name, module_);
    
    // Named conflicted. LLVM will auto rename
    if (func->getName() != name) {
        func->eraseFromParent();
        func = module_->getFunction(name);
        
        // If func is already defined, reject.
        if (!func->empty()){
            last_error_ = "redefinition of function";
            return 0;
        }
        
        // If argument count differs, reject.
        if (func->arg_size() != params.size()) {
            last_error_ = "redefinition of function with difference number of args";
            return 0;
        }
    }   
    
    return FunctionAdaptor(func);
}

const char * JITEngine::last_error() const {
    return last_error_.c_str();
}

bool JITEngine::verify() const {
    return not llvm::verifyModule(*module_);
}

void JITEngine::optimize(FunctionAdaptor func){
    fpm_->run(*func.get_function());
}

void * JITEngine::get_pointer_to_function(FunctionAdaptor fn){
    return ee_->getPointerToFunction(fn.get_function());
}

