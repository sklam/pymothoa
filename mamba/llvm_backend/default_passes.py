DEFAULT_PASSES = filter(lambda S: S[0]!='#', filter(bool, '''
mem2reg
basicaa
instcombine
reassociate
gvn
simplifycfg
memdep
indvars
lda
lcssa
licm
loops
loop-simplify
loop-rotate
loop-unswitch
loop-unroll
memdep
scalar-evolution
bb-vectorize
simplifycfg
tailcallelim
'''.splitlines()))

#DEFAULT_PASSES = filter(lambda S: S[0]!='#', filter(bool, '''
#no-aa
#tbaa
#basicaa
#deadargelim
#instcombine
#simplifycfg
#basiccg
#scalarrepl-ssa
#domtree
#early-cse
#simplify-libcalls
#lazy-value-info
#jump-threading
#correlated-propagation
#simplifycfg
#instcombine
#tailcallelim
#simplifycfg
#reassociate
#domtree
#loops
#loop-simplify
#lcssa
#loop-rotate
#licm
#lcssa
#loop-unswitch
#instcombine
#scalar-evolution
#loop-simplify
#lcssa
#indvars
#loop-idiom
#loop-deletion
#loop-unroll
#memdep
#gvn
#memdep
#memcpyopt
#sccp
#instcombine
#lazy-value-info
#jump-threading
#correlated-propagation
#domtree
#memdep
#dse
#loops
#scalar-evolution
#bb-vectorize
#instcombine
#early-cse
#adce
#simplifycfg
#instcombine
#domtree
#loops
#scalar-evolution
#bb-vectorize
#preverify
#verify
#deadargelim
#instcombine
#simplifycfg
#basiccg
#scalarrepl-ssa
#domtree
#early-cse
#simplify-libcalls
#lazy-value-info
#jump-threading
#correlated-propagation
#simplifycfg
#instcombine
#tailcallelim
#simplifycfg
#reassociate
#domtree
#loops
#loop-simplify
#lcssa
#loop-rotate
#licm
#lcssa
#loop-unswitch
#instcombine
#scalar-evolution
#loop-simplify
#lcssa
#indvars
#loop-idiom
#loop-deletion
#loop-unroll
#memdep
#gvn
#memdep
#memcpyopt
#sccp
#instcombine
#lazy-value-info
#jump-threading
#correlated-propagation
#domtree
#memdep
#dse
#loops
#scalar-evolution
#bb-vectorize
#instcombine
#early-cse
#adce
#simplifycfg
#instcombine
#preverify
#domtree
#verify
#'''.splitlines()))


