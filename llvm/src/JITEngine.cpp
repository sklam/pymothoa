#include "llvm_wrapper.hpp"

#include "llvm/Support/raw_ostream.h"
#include "llvm/Support/FormattedStream.h"
#include "llvm/Support/Host.h"

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
void CreatePasses(){
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

JITEngine::JITEngine(std::vector<std::string> passes, bool killOnBadPass)
    : module_(0),
      ee_(0),
      last_error_("no error")
{
    // Reference: Kaleidoscope: Adding JIT and Optimizer Support
    //            http://llvm.org/docs/tutorial/LangImpl4.html
    using namespace llvm;
    InitializeNativeTarget();
    InitializeNativeTargetAsmPrinter();

    CreatePasses();

    LLVMContext & Context = getGlobalContext();

    module_ = new Module("default", Context);

    // Create the JIT.  This takes ownership of the module.
    std::string ErrStr;

    EngineBuilder & engine_builder = EngineBuilder(module_).setErrorStr(&ErrStr);
    engine_builder.setEngineKind(EngineKind::JIT); // force JIT
    // engine_builder.setOptLevel(CodeGenOpt::Aggressive);

    ee_ = engine_builder.create();

    if (!ee_) {
        std::cerr << "Could not create ExecutionEngine: " << ErrStr << '\n';
        exit(1);    // Abort.
    }

    ee_->DisableLazyCompilation(); // No lazy compiling

    fpm_ = new FunctionPassManager(module_);

    PassRegistry & registry = *PassRegistry::getPassRegistry();
    for (size_t i=0; i<passes.size(); ++i) {
        const PassInfo * passinfo = registry.getPassInfo(passes[i]);
        if (passinfo) {
            fpm_->add(passinfo->createPass());
        } else {
            std::cerr << "Warning: " << passes[i] << " not found! skipped!" << std::endl;
            if (killOnBadPass) exit(1);
        }
    }
//    // Set up the optimizer pipeline.  Start with registering info about how the
//    // target lays out data structures.
//    fpm_->add(new TargetData(*ee_->getTargetData()));
//    // Promote allocas to registers.
//    fpm_->add(createPromoteMemoryToRegisterPass());
//    // Provide basic AliasAnalysis support for GVN.
//    fpm_->add(createBasicAliasAnalysisPass());
//    // Do simple "peephole" optimizations and bit-twiddling optzns.
//    fpm_->add(createInstructionCombiningPass());
//    // Reassociate expressions.
//    fpm_->add(createReassociatePass());
//    // Eliminate Common SubExpressions.
//    fpm_->add(createGVNPass());
//    // - ? - Unroll loop - Am I using this correctly? Cannot not see any change!
//    fpm_->add(createIndVarSimplifyPass());
//    fpm_->add(createLoopUnrollPass());
//    // - ? - Vectorize - Am I using this correctly
//    fpm_->add(createBBVectorizePass());
//    // Simplify the control flow graph (deleting unreachable blocks, etc).
//    fpm_->add(createCFGSimplificationPass());
//    // - ? - Eliminate tail recursion
//    fpm_->add(createTailCallEliminationPass());



    fpm_->doInitialization();
}

JITEngine::~JITEngine(){
    delete ee_;
    delete fpm_;
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

std::string JITEngine::dump_asm(FunctionAdaptor fn){
    using namespace llvm;

    std::string buffer;
    raw_string_ostream rso(buffer);
    formatted_raw_ostream fso(rso);

    TargetMachine * tm = EngineBuilder(module_).selectTarget();

    FunctionPassManager fpm(module_);

    fpm.add(new TargetData(*ee_->getTargetData()));

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
