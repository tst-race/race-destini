/*
 * Python to C++ IOManager wrappers
 */
%module IOManager
%include "std_string.i"
// https://stackoverflow.com/questions/40959436/swig-python-detected-a-memory-leak-of-type-uint32-t-no-destructor-found
%include "stdint.i"
// https://stackoverflow.com/questions/51466189/swig-c-to-python-vector-problems
%include "std_vector.i"
%{
#include "IOManager.h"

#include "IOManager_SWIG.cxx"

extern "C" void SetDiagPrint (PyObject *func);
%}

// http://www.swig.org/Doc1.3/Python.html#Python_nn20

%include "IOManager.h"
%include "CLICodec.h"

extern "C" void SetDiagPrint (PyObject *func);


/*
 * Build
 * -----
 * bash pyrace.mak
 *
 * Python API
 * ------ ---
 * python3 -i
 *
 * from IOManager import *
 *
 * Required initialization:
 *
 * <status> = IOManager.SetHostIP         (<hostname>)
 * <status> = IOManager.SetProcessMsg     (<process callback> [, <msg type>])
 * <status> = IOManager.SetSendMsg        (<send callback>    [, <chan type>])
 *
 * where
 *   <process callback> has arguments (            <refcon>, <bytes>)
 *   <send callback>    has arguments (<int toIP>, <refcon>, <bytes>, <msg type>)
 *
 * Decoding/encoding:
 *
 * <status> = IOManager.Examine           (<bytes>, <channel type> [, <int fromIP> [, <refcon>]])
 * <status> = IOManager.Send              (<bytes>, <str toIP>    , <channel type> [, <refcon> [, <input image bytes>]])
 * <status> = IOManager.Broadcast         (<bytes>, <str toGroup> , <channel type> [, <refcon> [, <input image bytes>]])
 *
 * Message packing:
 *
 * <msgWrapper>      = MessageWrapper ()
 * <int wrapped>     = MessageWrapper.WrappedSize (<int raw>)
 *                     <msgWrapper>.wrap (<bytes>, <msg type>, (<str toHost> | <int toIP>))
 * <status>, <bytes> = <msgWrapper>.close ()
 *
 * Utility/test:
 *
 * <bytes> = IOManager.RandomImage ()  
 *
 */
