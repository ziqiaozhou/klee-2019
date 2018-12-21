cmake \
	-DCMAKE_BUILD_TYPE=Release \
	-DENABLE_SOLVER_STP=ON \
	-ENABLE_SOLVER_Z3=ON\
	-ENABLE_TCMALLOC=ON\
	-ENABLE_ZLIB=ON\
	-DENABLE_POSIX_RUNTIME=ON \
	-DENABLE_KLEE_UCLIBC=ON \
	-DKLEE_UCLIBC_PATH=/playpen/ziqiao/thesis/codes/klee-all/klee-uclibc \
	-DENABLE_SYSTEM_TESTS=OFF \
	-DENABLE_UNIT_TESTS=OFF \
	-USE_CMAKE_FIND_PACKAGE_LLVM=OFF \
	-DLLVM_CONFIG_BINARY=/usr/lib/llvm-3.5.0/bin/llvm-config \
	-DLLVMCC=/usr/lib/llvm-3.5.0/bin/clang \
	-DLLVMCXX=/usr/lib/llvm-3.5.0/bin/clang++ \
/playpen/ziqiao/thesis/codes/klee-all/klee

