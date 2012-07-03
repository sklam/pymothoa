/**
Copyright (c) 2012, Siu Kwan Lam
All rights reserved.
**/

#include "llvm_wrapper.hpp"

#include "llvm/Support/raw_ostream.h"
#include "llvm/Support/FormattedStream.h"
#include "llvm/Support/Host.h"
#include "llvm/Support/TargetRegistry.h"
#include "llvm/Transforms/IPO/PassManagerBuilder.h"

#include <sstream>

class PassRegistryPrinter : public llvm::PassRegistrationListener{
public:
    std::ostringstream stringstream;

    void passEnumerate(const llvm::PassInfo * pass_info){
        stringstream << pass_info->getPassArgument() << ": "
                     << pass_info->getPassName() << '\n';
    }
};

static
void InitializePasses(){
    using namespace llvm;
    PassRegistry &registry = *PassRegistry::getPassRegistry();
    initializeCore(registry);
    initializeScalarOpts(registry);
    initializeVectorization(registry);
    initializeIPO(registry);
    initializeAnalysis(registry);
    initializeIPA(registry);
    initializeTransformUtils(registry);
    initializeInstCombine(registry);
//    initializeInstrumentation(registry);
    initializeTarget(registry);
}

llvm::ExecutionEngine * JITEngine::the_exec_engine_=0;

JITEngine::JITEngine(std::string modname, int optlevel, bool vectorize)
    : module_(0),
      last_error_("no error")
{
    // Reference: Kaleidoscope: Adding JIT and Optimizer Support
    //            http://llvm.org/docs/tutorial/LangImpl4.html
    //
    // Jun 26, 2012
    //   Actually, It has been changed so much at this point the code
    //   does not look like the tutorial at all.
    using namespace llvm;
    InitializeNativeTarget();
    InitializeNativeTargetAsmPrinter();

    InitializePasses();

    LLVMContext & Context = getGlobalContext();

    // Check host target
    const Target * host_target = TargetRegistry::getClosestTargetForJIT(last_error_);
    if (0==host_target){
        std::cerr << "Cannot create JIT target for the host." << std::endl;
        std::cerr << last_error_ << std::endl;
        exit(1);
    }

    module_ = new Module(modname, Context);
    module_->setTargetTriple(sys::getDefaultTargetTriple());

    if (0==the_exec_engine_) {// First instance of JITEngine

        // Create the JIT.  This takes ownership of the module.
        std::string ErrStr;

        EngineBuilder & engine_builder = EngineBuilder(module_).setErrorStr(&ErrStr);
        engine_builder.setEngineKind(EngineKind::JIT); // force JIT
        engine_builder.setOptLevel(CodeGenOpt::Aggressive); // in order to use SSE

        the_exec_engine_ = engine_builder.create();

        if (!the_exec_engine_) {
            std::cerr << "Could not create ExecutionEngine: " << ErrStr << '\n';
            exit(1);    // Abort.
        }

        the_exec_engine_->DisableLazyCompilation(); // No lazy compiling
    } else {
        // Simply add new module to the already existent execution-engine
        the_exec_engine_->addModule(module_);
    }

    // Set the data layout (is it necessary?)
    module_->setDataLayout(the_exec_engine_->getTargetData()->getStringRepresentation());

    // Use PassManagerBuilder to populate the pass managers.
    // (as suggested by Tobias Grosser)
    PassManagerBuilder pm_builder;
    pm_builder.OptLevel = optlevel;     // O3
    pm_builder.Vectorize = vectorize; // ensure vectorizing

    mpm_ = new PassManager;
    fpm_ = new FunctionPassManager(module_);

    pm_builder.populateModulePassManager(*mpm_);
    pm_builder.populateFunctionPassManager(*fpm_);

}

JITEngine::~JITEngine(){
    delete mpm_;
    delete fpm_;
    // do not delete the_exec_engine_ which lives for the entire lifetime of the process.
    // do not delete module_ because it is owned by the execution engine.
}

void JITEngine::start_multithreaded(){
    llvm::llvm_start_multithreaded();
}

void JITEngine::stop_multithreaded(){
    llvm::llvm_stop_multithreaded();
}

bool JITEngine::is_multithreaded(){
    return llvm::llvm_is_multithreaded();
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
    Function * func = Function::Create(fnty,
                                       Function::ExternalLinkage,
                                       name, module_);

    // Named conflicted. LLVM will auto rename
    if (func->getName() != name) {
        func->eraseFromParent();
        func = module_->getFunction(name);

        // If func is already defined, reject.
        if (!func->empty()){
            last_error_ = "Redefinition of function.";
            return 0;
        }

        // If argument count differs, reject.
        if (func->arg_size() != params.size()) {
            last_error_ = "Redefinition of function with a different number of args.";
            return 0;
        }
    }

    // Otherwise, function creation okay

    // (Experimental) Set no aliasing for all parameters
    for (size_t i=0; i<params.size(); ++i){
        if (params[i]->isPointerTy()){
            func->setDoesNotAlias(1+i);// zero is the return; therefore, start with 1
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

void JITEngine::optimize(){
    mpm_->run(*module_);
}

void JITEngine::optimize_function(FunctionAdaptor fn) const{
    fpm_->run(*fn.get_function());
}

void * JITEngine::get_pointer_to_function(FunctionAdaptor fn){
    return the_exec_engine_->getPointerToFunction(fn.get_function());
}

std::string JITEngine::dump_asm(FunctionAdaptor fn){
    using namespace llvm;

    std::string buffer;
    raw_string_ostream rso(buffer);
    formatted_raw_ostream fso(rso);

    TargetMachine * tm = EngineBuilder(module_).selectTarget();

    FunctionPassManager fpm(module_);

    fpm.add(new TargetData(*the_exec_engine_->getTargetData()));

    if ( tm->addPassesToEmitFile(fpm, fso, TargetMachine::CGFT_AssemblyFile, true) ) {
        rso << "Not Supported\n";
    }

    fpm.doInitialization();

    fpm.run(*fn.get_function());

    fpm.doFinalization();

    return buffer;
}

std::string JITEngine::dump_passes(){
    using namespace llvm;
    PassRegistry &registry = *PassRegistry::getPassRegistry();
    PassRegistryPrinter prp;
    registry.enumerateWith(&prp);
    return prp.stringstream.str();
}
