/*
 * Python to C++ CLICodec wrappers
 */
%module CLICodec
%include "std_string.i"
// https://stackoverflow.com/questions/40959436/swig-python-detected-a-memory-leak-of-type-uint32-t-no-destructor-found
%include "stdint.i"
%{
#include "CLICodec.h"
%}

// http://www.swig.org/Doc1.3/Python.html#Python_nn20

%include "CLICodec.h"


/*
 * Build
 * -----
 * bash pyrace.mak
 *
 * Python API
 * ------ ---
 * python3 -i
 *
 *
 */
