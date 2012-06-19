DEFAULT_PASSES = filter(bool, '''
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
'''.splitlines())

