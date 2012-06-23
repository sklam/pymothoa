from pymothoa.llvm_backend.module import LLVMModuleManager

USE_THESE_PASSES = '''
targetlibinfo
no-aa
tbaa
basicaa
preverify
domtree
verify
globalopt
ipsccp
deadargelim
instcombine
simplifycfg
basiccg
prune-eh
inline
functionattrs
argpromotion
scalarrepl-ssa
domtree
early-cse
simplify-libcalls
lazy-value-info
jump-threading
correlated-propagation
simplifycfg
instcombine
tailcallelim
simplifycfg
reassociate
domtree
loops
loop-simplify
lcssa
loop-rotate
licm
lcssa
loop-unswitch
instcombine
scalar-evolution
loop-simplify
lcssa
indvars
loop-idiom
loop-deletion
loop-unroll
memdep
gvn
memdep
memcpyopt
sccp
instcombine
lazy-value-info
jump-threading
correlated-propagation
domtree
memdep
dse
loops
scalar-evolution
bb-vectorize
instcombine
early-cse
adce
simplifycfg
instcombine
strip-dead-prototypes
globaldce
constmerge
globalopt
ipsccp
deadargelim
instcombine
simplifycfg
basiccg
prune-eh
inline
functionattrs
argpromotion
scalarrepl-ssa
domtree
early-cse
simplify-libcalls
lazy-value-info
jump-threading
correlated-propagation
simplifycfg
instcombine
tailcallelim
simplifycfg
reassociate
domtree
loops
loop-simplify
lcssa
loop-rotate
licm
lcssa
loop-unswitch
instcombine
scalar-evolution
loop-simplify
lcssa
indvars
loop-idiom
loop-deletion
loop-unroll
memdep
gvn
memdep
memcpyopt
sccp
instcombine
lazy-value-info
jump-threading
correlated-propagation
domtree
memdep
dse
loops
scalar-evolution
bb-vectorize
instcombine
early-cse
adce
simplifycfg
instcombine
strip-dead-prototypes
globaldce
constmerge
preverify
domtree
verify
'''

import unittest

class Test(unittest.TestCase):
    def test_passes(self):
        do_strip = lambda S : S.strip()

        include_passes = filter(bool, map(do_strip, USE_THESE_PASSES.splitlines()))

        manager = LLVMModuleManager()
        passes = manager.jit_engine.dump_passes()

        mapping = dict(map(do_strip, line.split(':'))
                           for line in passes.splitlines())
        for p in include_passes:
            self.assertIn(p, mapping)

if __name__ == '__main__':
    unittest.main()
