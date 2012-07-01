%module llvm_wrapper
%{
#define SWIG_FILE_WITH_INIT
#include "llvm_wrapper.hpp"
%}
%include "std_vector.i"
%include "std_string.i"

%template (ArrayString) std::vector<std::string>;
%template (ArrayInt) std::vector<int>;
%template (ArrayTypePtr) std::vector<llvm::Type*>;
%template (ArrayValuePtr) std::vector<llvm::Value*>;
%template (ArrayBBPtr) std::vector<llvm::BasicBlock*>;


enum {
    ICMP_EQ  = llvm::CmpInst::ICMP_EQ,      // equal
    ICMP_NE  = llvm::CmpInst::ICMP_NE,      // not equal
    ICMP_UGT = llvm::CmpInst::ICMP_UGT,     // unsigned greater than
    ICMP_UGE = llvm::CmpInst::ICMP_UGE,     // unsigned greater or equal
    ICMP_ULT = llvm::CmpInst::ICMP_ULT,     // unsigned less than
    ICMP_ULE = llvm::CmpInst::ICMP_ULE,     // unsigned less or equal
    ICMP_SGT = llvm::CmpInst::ICMP_SGT,     // signed greater than
    ICMP_SGE = llvm::CmpInst::ICMP_SGE,     // signed greater equal
    ICMP_SLT = llvm::CmpInst::ICMP_SLT,     // signed less than
    ICMP_SLE = llvm::CmpInst::ICMP_SLE,     // signed less or equal

    FCMP_FALSE = llvm::CmpInst::FCMP_FALSE,  // Always false (always folded)
    FCMP_OEQ = llvm::CmpInst::FCMP_OEQ,      // True if ordered and equal
    FCMP_OGT = llvm::CmpInst::FCMP_OGT,      // True if ordered and greater than
    FCMP_OGE = llvm::CmpInst::FCMP_OGE,      // True if ordered and greater than or equal
    FCMP_OLT = llvm::CmpInst::FCMP_OLT,      // True if ordered and less than
    FCMP_OLE = llvm::CmpInst::FCMP_OLE,      // True if ordered and less than or equal
    FCMP_ONE = llvm::CmpInst::FCMP_ONE,      // True if ordered and operands are unequal
    FCMP_ORD = llvm::CmpInst::FCMP_ORD,      // True if ordered (no nans)
    FCMP_UNO = llvm::CmpInst::FCMP_UNO,      // True if unordered: isnan(X) | isnan(Y)
    FCMP_UEQ = llvm::CmpInst::FCMP_UEQ,      // True if unordered or equal
    FCMP_UGT = llvm::CmpInst::FCMP_UGT,      // True if unordered or greater than
    FCMP_UGE = llvm::CmpInst::FCMP_UGE,      // True if unordered, greater than, or equal
    FCMP_ULT = llvm::CmpInst::FCMP_ULT,      // True if unordered or less than
    FCMP_ULE = llvm::CmpInst::FCMP_ULE,      // True if unordered, less than, or equal
    FCMP_UNE = llvm::CmpInst::FCMP_UNE,      // True if unordered or not equal
    FCMP_TRUE = llvm::CmpInst::FCMP_TRUE,    // Always true (always folded)
};

/**
 * Always return a pointer to a singleton object.
 * User should never delete the pointer.
 * Type equivalence can be tested by simple pointer comparision.
 * The same type always have the same pointer.
 */
class TypeFactory{
public:
    static llvm::Type * make_int();
    static llvm::Type * make_int(unsigned int bit);
    static llvm::Type * make_float();
    static llvm::Type * make_double();
    static llvm::Type * make_void();
    static llvm::Type * make_pointer(llvm::Type * elemty);
    static llvm::Type * make_vector(llvm::Type * elemty, unsigned int elemct);
};

class ConstantFactory{
public:
    static llvm::Value * make_int(llvm::Type * ty, unsigned long long val);
    static llvm::Value * make_int_signed(llvm::Type * ty, unsigned long long val);
    static llvm::Value * make_real(llvm::Type * ty, double val);
    static llvm::Value * make_undef(llvm::Type * ty);
};


class FunctionAdaptor{
public:
    FunctionAdaptor(llvm::Function * fp);
    const char* name() const;
    bool valid() const;
    operator bool () const;
    std::string dump() const;
    llvm::Function * get_function() const ;
    llvm::BasicBlock * append_basic_block(const char name[]);
    std::vector<llvm::Value*> arguments() const;
    unsigned int arg_size() const;
    bool verify() const;
private:
    llvm::Function * const func_;
};

class JITEngine{
public:
    JITEngine(std::string modname, int optlevel=3, bool vectorize=true);
    ~JITEngine();

    std::string dump();

    /**
     * @returns A FunctionAdaptor object which maybe invalid if the name
     *          of the function is already defined (with a body). Or,
     *          defining a extern function declaration but has a different
     *          number of arguments.
     */
    FunctionAdaptor make_function(const char name[],
                                  llvm::Type *result,
                                  std::vector<llvm::Type*> params);
    const char * last_error() const;
    /**
     * Verify the module.
     */
    bool verify() const;
    /**
     * Optimize the module.
     */
    void optimize();
    /**
     * Optimize the function
     */
    void optimize_function(FunctionAdaptor fn) const;

    void * get_pointer_to_function(FunctionAdaptor fn);

    std::string dump_asm(FunctionAdaptor fn);

    // Are these 3 functions necessary? Can I just use lock in ExecutionEngine?
    void start_multithreaded();
    void stop_multithreaded();
    bool is_multithreaded();

    /**
     * @return registered passes.
     */
    std::string dump_passes();

private:
    JITEngine(const JITEngine&);                 //no impl
    JITEngine & operator = (const JITEngine&);   //no impl
private:
    llvm::Module * module_;
    static llvm::ExecutionEngine * the_exec_engine_; //class-member singleton
    llvm::FunctionPassManager * fpm_; // run after function generation to reduce function in memory (as documented in LLVM)
    llvm::PassManager * mpm_;   // the primary pass manager

    std::string last_error_;
};



class Builder {
public:
    Builder();

    /**
     * Set inserter position at the end of the basic-block.
     */
    void insert_at(llvm::BasicBlock * bb);

    llvm::BasicBlock * get_basic_block() const;

    llvm::Value * phi(llvm::Type * type, std::vector<llvm::BasicBlock*> in_blocks, std::vector<llvm::Value*> in_values, const char* name="");

    // bitwise operations
    llvm::Value * bitwise_and(llvm::Value * lhs, llvm::Value * rhs, const char * name="");

    llvm::Value * bitwise_or(llvm::Value * lhs, llvm::Value * rhs, const char * name="");

    llvm::Value * bitwise_neg(llvm::Value * value, const char * name="");
    // integer operations

    llvm::Value * add(llvm::Value * lhs, llvm::Value * rhs, const char * name="");

    llvm::Value * sub(llvm::Value * lhs, llvm::Value * rhs, const char * name="");

    llvm::Value * mul(llvm::Value * lhs, llvm::Value * rhs, const char * name="");

    llvm::Value * sdiv(llvm::Value * lhs, llvm::Value * rhs, const char * name="");

    llvm::Value * udiv(llvm::Value * lhs, llvm::Value * rhs, const char * name="");

    llvm::Value * umod(llvm::Value * lhs, llvm::Value * rhs, const char * name="");

    llvm::Value * smod(llvm::Value * lhs, llvm::Value * rhs, const char * name="");

    llvm::Value * icmp(int op, llvm::Value * lhs, llvm::Value * rhs, const char * name="");

    // float operations

    llvm::Value * fadd(llvm::Value * lhs, llvm::Value * rhs, const char * name="");

    llvm::Value * fsub(llvm::Value * lhs, llvm::Value * rhs, const char * name="");

    llvm::Value * fmul(llvm::Value * lhs, llvm::Value * rhs, const char * name="");

    llvm::Value * fdiv(llvm::Value * lhs, llvm::Value * rhs, const char * name="");

    llvm::Value * fmod(llvm::Value * lhs, llvm::Value * rhs, const char * name="");

    llvm::Value * fcmp(int op, llvm::Value * lhs, llvm::Value * rhs, const char * name="");

    // casting operations

    llvm::Value * icast(llvm::Value * val, llvm::Type * ty, bool is_signed, const char * name="");

    llvm::Value * fcast(llvm::Value * val, llvm::Type * ty, const char * name="");

    llvm::Value * sitofp(llvm::Value * val, llvm::Type * ty, const char * name="");

    llvm::Value * fptosi(llvm::Value * val, llvm::Type * ty, const char * name="");

    llvm::Value * uitofp(llvm::Value * val, llvm::Type * ty, const char * name="");

    llvm::Value * fptoui(llvm::Value * val, llvm::Type * ty, const char * name="");

    // control-flow operations

    void ret(llvm::Value * retval);

    void ret_void();

    void branch(llvm::BasicBlock * bb);

    void cond_branch(llvm::Value * Cond, llvm::BasicBlock * bb_true, llvm::BasicBlock * bb_false);

    llvm::Value * call(FunctionAdaptor func, std::vector<llvm::Value*> args, const char * name="");

    void unreachable();

    llvm::Value * alloc(llvm::Type * ty, const char * name="");

    llvm::Value * alloc_array(llvm::Type * ty, llvm::Value * ct, const char * name="");

    llvm::Value * load(llvm::Value * ptr, const char * name="");

    llvm::Value * store(llvm::Value * val, llvm::Value * ptr);


    // pointer

    llvm::Value * gep(llvm::Value * ptr, llvm::Value * idx, const char * name="");
    llvm::Value * gep2(llvm::Value * ptr, std::vector<llvm::Value*> indices, const char * name="");

    // vector function

    llvm::Value * extract_element(llvm::Value * vector, llvm::Value * idx, const char * name="");

    llvm::Value * insert_element(llvm::Value * vector, llvm::Value * newvalue, llvm::Value * idx, const char * name="");

    // helper

    /**
     * @return True if the block is well formed (closed with control-float instruction).
     */
    bool is_block_closed();

private:
    Builder(const Builder&);                //no impl
    Builder & operator = (const Builder&);    //no impl
private:
    llvm::IRBuilder<> builder_;
};

