// https://stackoverflow.com/questions/510406/is-there-a-way-to-get-the-current-ref-count-of-an-object-in-python

#define PY_SSIZE_T_CLEAN
#include <Python.h>

#include <functional>
#include <iostream>
#include <string>
#include <utility>
#include <vector>

SWIGINTERNINLINE PyObject *SWIG_From_int              (int value);
SWIGINTERN       int       SWIG_AsPtr_std_string      (PyObject *obj, std::string **val);
SWIGINTERN       int       SWIG_AsVal_int             (PyObject *obj, int *val);
SWIGINTERN       int       SWIG_AsVal_unsigned_SS_int (PyObject *obj, unsigned int *val);

#if defined (SWIGTYPE_p_uint32_t)
  #define _SWIGTYPE_p_uint32_t SWIGTYPE_p_uint32_t
#else
  #define _SWIGTYPE_p_uint32_t swig_types[22]
#endif


#ifdef __cplusplus
extern "C" {
#endif


  static std::string
_PyStringToString (PyObject *pyString)
{
  std::string *pString = nullptr;
  std::string  cString;
  int          res     = SWIG_AsPtr_std_string (pyString, &pString);

  if (SWIG_IsOK (res)) {
    if (pString /* != nullptr */) {
      cString = *pString;

      if (SWIG_IsNewObj (res)) delete pString;

      return cString;
    }
  }
  else {
    SWIG_exception_fail (SWIG_ArgError ((pString ? res : SWIG_TypeError)),
                         "_PyStringToString () requires argument of type 'string'");
  fail:
    return "";
  }
  return "";
}

// https://gist.github.com/rjzak/5681680

// PyObject -> Vector

  static std::vector<std::string>
_listTupleToVector_String (PyObject *incoming)
{
  std::vector<std::string> data;

  if      (PyTuple_Check (incoming)) {
    for (Py_ssize_t i = 0; i < PyTuple_Size (incoming); i++) {
      PyObject *value = PyTuple_GetItem (incoming, i);

      data.push_back (_PyStringToString (value));
    }
  }
  else if (PyList_Check  (incoming)) {
    for (Py_ssize_t i = 0; i < PyList_Size (incoming); i++) {
      PyObject *value = PyList_GetItem (incoming, i);

      data.push_back (_PyStringToString (value));
    }
  }
  else
    SWIG_exception_fail (SWIG_ArgError (SWIG_TypeError),
                         "_listTupleToVector_String (): passed PyObject pointer was not a list or tuple!"
);

 fail:

  return data;
}


SWIGINTERN PyObject *_wrap_IOManager_Examine (PyObject *SWIGUNUSEDPARM (self), PyObject *args) {

  Py_ssize_t  argc;
  void       *pMsgIn   = nullptr;
  size_t      nMsgIn   = 0UL;
  int         _cType;
  uint32_t    fromIP   = 0UL;
  PyObject   *pyRefcon = Py_None;

  // Check for tuple argument

  if (!PyTuple_Check (args)) SWIG_fail;

  // Check the number of arguments

  argc = args ? PyObject_Length (args) : 0;

  if (argc < 2 || argc > 4) SWIG_fail;

  // Parse the argument tuple

  {
    std::string  _fmts  = "y#ikO";
    std::string  tmpStr = _fmts.substr (0, argc + 1) + ":IOManager_Examine";
    char        *_fmt   = const_cast <char *> (tmpStr.c_str ());

    if (!PyArg_ParseTuple (args, _fmt, &pMsgIn, &nMsgIn, &_cType, &fromIP, &pyRefcon)) SWIG_fail;
  }

  // Increment refcon reference count

  Py_XINCREF (pyRefcon);

  // Invoke Examine ()

  {
    IOM_msg_type  cType = static_cast <IOM_msg_type> (_cType);
    int           result;
    PyObject     *resultobj;

    result    = (int) IOManager::Examine (pMsgIn, nMsgIn, cType, fromIP, pyRefcon);
    resultobj = SWIG_From_int (static_cast <int> (result));

    return resultobj;
  }
  
fail:

  SWIG_SetErrorMsg (PyExc_NotImplementedError, "Wrong number or type of arguments for overloaded function 'IOManager_Examine'.\n"
    "  Possible C/C++ prototypes are:\n"
    "    IOManager::Examine(void *,size_t,uint32_t[,uint32_t[,void *]])\n");

  return 0;
}


SWIGINTERN PyObject *_wrap_IOManager_Send (PyObject *self, PyObject *args) {

  Py_ssize_t   argc;
  void        *pMsgOut  = nullptr;
  size_t       nMsgOut  = 0UL;
  PyObject    *pyToIP   = nullptr;
  int          cType;
  PyObject    *pyRefcon = Py_None;
  int          mType    = IOM_MT_CT_COPY;
  PyObject    *pyMedia  = Py_None;
  std::string *pToHost  = nullptr;
  std::string  toHost;
  uint32_t     toIP     = 0UL;

  std::string _fmts[] = {
    "y#Oi",
    "y#OiO",
    "y#OiOi",
    "y#OiOiO"
  };

  // Check for tuple argument

  if (!PyTuple_Check (args)) SWIG_fail;

  // Check the number of arguments

  argc = args ? PyObject_Length (args) : 0;

  if (argc < 3 || argc > 6) SWIG_fail;

  // Parse the argument tuple

  {
    std::string  tmpStr = _fmts[argc - 3] + ":IOManager_Send";
    char        *_fmt   = const_cast <char *> (tmpStr.c_str ());

    if (!PyArg_ParseTuple (args, _fmt, &pMsgOut, &nMsgOut, &pyToIP, &cType, &pyRefcon, &mType, &pyMedia)) SWIG_fail;
  }

  if (pyToIP /* != nullptr */) {
    do {
      int   res2;
      void *argp2;

      /* toIP (uint32_t) */

      res2 = SWIG_ConvertPtr (pyToIP, &argp2, _SWIGTYPE_p_uint32_t, 0 | 0);
      if (SWIG_IsOK (res2)) {
        if (argp2 /* != nullptr */) {
          uint32_t *temp = reinterpret_cast <uint32_t *> (argp2);

          toIP = *temp;

          if (SWIG_IsNewObj (res2)) delete temp;

          break;
        }
        else
          SWIG_exception_fail (SWIG_ValueError,
                               "invalid null reference in method 'IOManager_Send', argument 2 of type 'uint32_t'");
      }

      /* toHost (std::string) */

      res2 = SWIG_AsPtr_std_string (pyToIP, &pToHost);
      if (SWIG_IsOK (res2)) {
        if (pToHost /* != nullptr */) {
          toHost = *pToHost;

          if (SWIG_IsNewObj (res2)) delete pToHost;

          pToHost = &toHost;

          break;
        }
        else
          SWIG_exception_fail (SWIG_ArgError ((pToHost ? res2 : SWIG_TypeError)),
                               "in method 'IOManager_Send', argument 2 of type 'std::string'");
      }

      SWIG_fail;
    } while (0);
  }

  Py_XINCREF (pyRefcon);        // Increment refcon reference count

  int           result;
  PyObject     *resultobj;
  IOM_msg_type  iomCType;   iomCType = static_cast <IOM_msg_type> (cType);
  IOM_msg_type  iomMType;   iomMType = static_cast <IOM_msg_type> (mType != IOM_MT_CT_COPY ? mType : cType);
  MediaPathPtr  pMedia;     pMedia   = nullptr;

  if (argc == 6) {
    void *pVoid    = nullptr;
    int   resMedia = SWIG_ConvertPtr (pyMedia, &pVoid, SWIGTYPE_p_MediaPath, 0 | 0);

    if (!SWIG_IsOK (resMedia)) {
      SWIG_exception_fail (SWIG_ArgError (resMedia),
                           "in method '" "IOManager_Send" "', argument " "6"
                           " of type '" "MediaPathPtr""'"); 
    }

    pMedia = reinterpret_cast <MediaPathPtr> (pVoid);
  }

  if (pToHost /* != nullptr */)
    result = (int) IOManager::Send (pMsgOut, nMsgOut, toHost, iomCType, pyRefcon, iomMType, pMedia);
  else
    result = (int) IOManager::Send (pMsgOut, nMsgOut, toIP,   iomCType, pyRefcon, iomMType, pMedia);

  resultobj = SWIG_From_int (static_cast <int> (result));

  return resultobj;

fail:

  SWIG_SetErrorMsg (PyExc_NotImplementedError, "Wrong number or type of arguments for overloaded function 'IOManager_Send'.\n"
    "  Possible C/C++ prototypes are:\n"
    "    IOManager::Send(void *,size_t,std::string,IOM_msg_type[,void *[,IOM_msg_type[,MediaPathPtr]]])\n"
    "    IOManager::Send(void *,size_t,uint32_t,IOM_msg_type[,void *[,IOM_msg_type[,MediaPathPtr]]])\n");

  return 0;
}


SWIGINTERN PyObject *_wrap_IOManager_Broadcast (PyObject *self, PyObject *args) {

  Py_ssize_t   argc;
  void        *pMsgOut  = nullptr;
  size_t       nMsgOut  = 0UL;
  PyObject    *pyToIP   = nullptr;
  int          cType;
  PyObject    *pyRefcon = Py_None;
  int          mType    = IOM_MT_CT_COPY;
  PyObject    *pyMedia  = Py_None;
  std::string *pToHost  = nullptr;
  std::string  toHost;
  uint32_t     toIP     = 0UL;

  std::string _fmts[] = {
    "y#Oi",
    "y#OiO",
    "y#OiOi"
    "y#OiOiO"
  };

  // Check for tuple argument

  if (!PyTuple_Check (args)) SWIG_fail;

  // Check the number of arguments

  argc = args ? PyObject_Length (args) : 0;

  if (argc < 3 || argc > 6) SWIG_fail;

  // Parse the argument tuple

  {
    std::string  tmpStr = _fmts[argc - 2] + ":IOManager_Broadcast";
    char        *_fmt   = const_cast <char *> (tmpStr.c_str ());

    if (!PyArg_ParseTuple (args, _fmt, &pMsgOut, &nMsgOut, &pyToIP, &cType, &pyRefcon, &mType, &pyMedia)) SWIG_fail;
  }

  if (pyToIP /* != nullptr */) {
    do {
      int   res2;
      void *argp2;

      /* toIP (uint32_t) */

      res2 = SWIG_ConvertPtr (pyToIP, &argp2, _SWIGTYPE_p_uint32_t, 0 | 0);
      if (SWIG_IsOK (res2)) {
        if (argp2 /* != nullptr */) {
          uint32_t *temp = reinterpret_cast <uint32_t *> (argp2);

          toIP = *temp;

          if (SWIG_IsNewObj (res2)) delete temp;

          break;
        }
        else
          SWIG_exception_fail (SWIG_ValueError,
                               "invalid null reference in method 'IOManager_Broadcast', argument 2 of type 'uint32_t'");
      }

      /* toHost (std::string) */

      res2 = SWIG_AsPtr_std_string (pyToIP, &pToHost);
      if (SWIG_IsOK (res2)) {
        if (pToHost /* != nullptr */) {
          toHost = *pToHost;

          if (SWIG_IsNewObj (res2)) delete pToHost;

          pToHost = &toHost;

          break;
        }
        else
          SWIG_exception_fail (SWIG_ArgError ((pToHost ? res2 : SWIG_TypeError)),
                               "in method 'IOManager_Broadcast', argument 2 of type 'std::string'");
      }

      SWIG_fail;
    } while (0);
  }

  Py_XINCREF (pyRefcon);        // Increment refcon reference count

  int           result;
  PyObject     *resultobj;
  IOM_msg_type  iomCType;   iomCType = static_cast <IOM_msg_type> (cType);
  IOM_msg_type  iomMType;   iomMType = static_cast <IOM_msg_type> (mType != IOM_MT_CT_COPY ? mType : cType);
  MediaPathPtr  pMedia;     pMedia   = nullptr;

  if (argc == 6) {
    void *pVoid    = nullptr;
    int   resMedia = SWIG_ConvertPtr (pyMedia, &pVoid, SWIGTYPE_p_MediaPath, 0 | 0);

    if (!SWIG_IsOK (resMedia)) {
      SWIG_exception_fail (SWIG_ArgError (resMedia),
                           "in method '" "IOManager_Broadcast" "', argument " "6"
                           " of type '" "MediaPathPtr""'"); 
    }

    pMedia = reinterpret_cast <MediaPathPtr> (pVoid);
  }

  if (pToHost /* != nullptr */)
    result = (int) IOManager::Broadcast (pMsgOut, nMsgOut, toHost, iomCType, pyRefcon, iomMType, pMedia);
  else
    result = (int) IOManager::Broadcast (pMsgOut, nMsgOut, toIP,   iomCType, pyRefcon, iomMType, pMedia);

  resultobj = SWIG_From_int (static_cast <int> (result));

  return resultobj;

fail:

  SWIG_SetErrorMsg (PyExc_NotImplementedError, "Wrong number or type of arguments for overloaded function 'IOManager_Broadcast'.\n"
    "  Possible C/C++ prototypes are:\n"
    "    IOManager::Broadcast(void *,size_t,std::string,IOM_msg_type[,void *[,IOM_msg_type[,MediaPathPtr]]])\n"
    "    IOManager::Broadcast(void *,size_t,uint32_t,IOM_msg_type[,void *[,IOM_msg_type[,MediaPathPtr]]])\n");

  return 0;
}

// https://stackoverflow.com/questions/28746744/passing-capturing-lambda-as-function-pointer

struct _ReceiveMsg
{
  _ReceiveMsg (RecvMsgFn recv) : _recv {std::move (recv)} {}
  RecvMsgFn _recv;
};

struct _SendMsg
{
  _SendMsg (SendMsgFn send) : _send {std::move (send)} {}
  SendMsgFn _send;
};


  static auto
_makeRecvFn (PyObject *pyFunc)
{
  _ReceiveMsg _newFn {
    [pyFunc] (uint32_t fromIP, void *refcon, uint8_t *pMsgIn, size_t nMsgIn) {
      
      // Invoke pyFunc

      (void) PyObject_CallFunction (pyFunc, (char *) "kOy#", fromIP, static_cast <PyObject *> (refcon), pMsgIn, nMsgIn);
    }
  };

  return _newFn._recv;
}

  static auto
_makeSendFn (PyObject *pyFunc)
{
  _SendMsg _newFn {
    [pyFunc] (uint32_t toIP, void *refcon, uint8_t *pMsgIn, size_t nMsgIn, IOM_msg_type cType) {
      PyObject *pyResult;
      
      // Invoke pyFunc

      pyResult = PyObject_CallFunction (pyFunc, (char *) "kOy#i", toIP, static_cast <PyObject *> (refcon), pMsgIn, nMsgIn, cType);

      if (!PyLong_Check (pyResult)) {
        (void) PyErr_Format (PyExc_TypeError,
                             "Bad return type (%s) from 'IOManager_SetSendMsg' callback.",
                             Py_TYPE (pyResult)->tp_name);
        return -1;
      }
      else
        return (int) PyLong_AsLong (pyResult);
    }
  };

  return _newFn._send;
}

SWIGINTERN PyObject *_wrap_IOManager_SetProcessMsg (PyObject *SWIGUNUSEDPARM (self), PyObject *args) {

  Py_ssize_t  argc;
  PyObject   *pyFunc = nullptr;
  int         mType  = IOM_MT_GENERAL;

  // Check for tuple argument

  if (!PyTuple_Check (args)) SWIG_fail;

  // Check the number of arguments

  argc = args ? PyObject_Length (args) : 0;

  if (argc < 1 || argc > 2) SWIG_fail;

  // Parse the argument tuple

  {
    std::string  _fmts  = "Oi";
    std::string  tmpStr = _fmts.substr (0, argc) + ":IOManager_SetProcessMsg";
    char        *_fmt   = const_cast <char *> (tmpStr.c_str ());

    if (!PyArg_ParseTuple (args, _fmt, &pyFunc, &mType)) SWIG_fail;

    if (!pyFunc || !PyCallable_Check (pyFunc)) SWIG_fail;
  }
  
  // Register the callback
  
  Py_XINCREF (pyFunc);

  {
    RecvMsgFn    _recv    = _makeRecvFn (pyFunc);
    IOM_msg_type iomMType = static_cast <IOM_msg_type> (mType);

    IOManager::SetProcessMsg (_recv, iomMType);

    return SWIG_Py_Void ();
  }

fail:

  SWIG_SetErrorMsg (PyExc_NotImplementedError, "Wrong number or type of arguments for overloaded function 'IOManager_SetProcessMsg'.\n"
    "  Possible C/C++ prototypes are:\n"
    "    IOManager::SetProcessMsg(RecvMsgCB[,IOM_msg_type])\n"
    "    IOManager::SetProcessMsg(RecvMsgFn[,IOM_msg_type])\n");

  return NULL;
}

SWIGINTERN PyObject *_wrap_IOManager_SetSendMsg (PyObject *SWIGUNUSEDPARM (self), PyObject *args) {

  Py_ssize_t  argc;
  PyObject   *pyFunc = nullptr;
  int         cType  = IOM_MT_GENERAL;

  // Check for tuple argument

  if (!PyTuple_Check (args)) SWIG_fail;

  // Check the number of arguments

  argc = args ? PyObject_Length (args) : 0;

  if (argc <  1 || argc > 2) SWIG_fail;

  // Parse the argument tuple

  {
    std::string  _fmts  = "Oi";
    std::string  tmpStr = _fmts.substr (0, argc) + ":IOManager_SetSendMsg";
    char        *_fmt   = const_cast <char *> (tmpStr.c_str ());

    if (!PyArg_ParseTuple (args, _fmt, &pyFunc, &cType)) SWIG_fail;

    if (!pyFunc || !PyFunction_Check (pyFunc)) SWIG_fail;
  }
  
  // Register the callback

  Py_XINCREF (pyFunc);

  {
    SendMsgFn    _send    = _makeSendFn (pyFunc);
    IOM_msg_type iomCType = static_cast <IOM_msg_type> (cType);

    IOManager::SetSendMsg (_send, iomCType);

    return SWIG_Py_Void ();
  }

fail:

  SWIG_SetErrorMsg (PyExc_NotImplementedError, "Wrong number or type of arguments for overloaded function 'IOManager_SetSendMsg'.\n"
    "  Possible C/C++ prototypes are:\n"
    "    IOManager::SetSendMsg(SendMsgCB[,IOM_msg_type])\n"
    "    IOManager::SetSendMsg(SendMsgFn[,IOM_msg_type])\n");

  return NULL;
}


SWIGINTERN PyObject *_wrap_MessageWrapper_wrap (PyObject *SWIGUNUSEDPARM (self), PyObject *args)
{
  Py_ssize_t      argc;
  MessageWrapper *msgWrapper = nullptr;
  PyObject       *arg0       = nullptr;
  void           *arg1       = nullptr;
  Py_ssize_t      arg2       = 0;
  IOM_msg_type   arg3;
  std::string    *pToHost    = nullptr;
  std::string     toHost;
  uint32_t        toIP;
  void           *argp0      = nullptr;
  int             ecode0     = 0;
  PyObject       *obj4       = nullptr;
  PyObject       *resultobj  = nullptr;

  // Check for tuple argument

  if (!PyTuple_Check (args)) SWIG_fail;

  // Check the number of arguments

  argc = args ? PyObject_Length (args) : 0;

  if (argc != 4) SWIG_fail;

  // Parse the argument tuple
  
  if (!PyArg_ParseTuple (args, (char *) "Oy#iO:MessageWrapper_wrap", &arg0, &arg1, &arg2, &arg3, &obj4)) SWIG_fail;

  ecode0 = SWIG_ConvertPtr (arg0, &argp0, SWIGTYPE_p_MessageWrapper, 0 | 0);
  if (!SWIG_IsOK (ecode0))
    SWIG_exception_fail (SWIG_ArgError (ecode0), "in method 'MessageWrapper_wrap', self of type 'MessageWrapper *'");
  msgWrapper = reinterpret_cast <MessageWrapper *> (argp0);

  //  printf ("Post msgWrapper cast (%p)\n", msgWrapper);
  //  fflush (stdout);

  do {
    int   res4;
    void *argp4;

    /* toIP (uint32_t) */

    res4 = SWIG_ConvertPtr (obj4, &argp4, _SWIGTYPE_p_uint32_t, 0 | 0);
    if (SWIG_IsOK (res4)) {
      if (argp4 /* != nullptr */) {
        uint32_t *temp = reinterpret_cast <uint32_t *> (argp4);

        toIP = *temp;

        if (SWIG_IsNewObj (res4)) delete temp;

        break;
      }
      else
        SWIG_exception_fail (SWIG_ValueError,
                             "invalid null reference in method 'IOManager_Send', argument 4 of type 'uint32_t'");
    }

    /* toHost (std::string) */

    res4 = SWIG_AsPtr_std_string (obj4, &pToHost);
    if (SWIG_IsOK (res4)) {
      if (pToHost /* != nullptr */) {
        toHost = *pToHost;

        if (SWIG_IsNewObj (res4)) delete pToHost;

        pToHost = &toHost;

        break;
      }
      else
        SWIG_exception_fail (SWIG_ArgError ((pToHost ? res4 : SWIG_TypeError)),
                             "in method 'IOManager_Send', argument 5 of type 'std::string'");
    }

    SWIG_fail;

  } while (0);

  //  printf ("Post toHost/toIP: %p, %d\n", pToHost, toIP);
  //  fflush (stdout);

  //  printf ("Before msgWrapper->wrap (%p, %ld, %d, %s)\n", arg1, arg2, arg3, toHost.c_str ());
  //  fflush (stdout);

  if (pToHost /* != nullptr */)
    msgWrapper->wrap (arg1, arg2, arg3, toHost);
  else
    msgWrapper->wrap (arg1, arg2, arg3, toIP);

  resultobj = SWIG_Py_Void ();

  return resultobj;

fail:

  SWIG_SetErrorMsg (PyExc_NotImplementedError, "Wrong number or type of arguments for overloaded function 'MessageWrapper_wrap'.\n"
    "  Possible C/C++ prototypes are:\n"
        "    MessageWrapper::wrap(void **,size_t*,IOM_msg_type,std::string)\n"
        "    MessageWrapper::wrap(void **,size_t*,IOM_msg_type,uint32_t)\n");

  return nullptr;
}

SWIGINTERN PyObject *_wrap_MessageWrapper_close (PyObject *SWIGUNUSEDPARM (self), PyObject *args)
{
  Py_ssize_t      argc;
  PyObject       *arg0;
  PyObject       *_unused_arg1;
  PyObject       *_unused_arg2;
  MessageWrapper *pMsgWrapper = nullptr;
  void           *pData       = nullptr;
  size_t          nData       = 0UL;

  // Check for tuple argument

  if (!PyTuple_Check (args)) SWIG_fail;

  // Check the number of arguments

  argc = args ? PyObject_Length (args) : 0;

  if (argc != 3) SWIG_fail;

  // Parse the argument tuple
  
  if (!PyArg_ParseTuple (args, (char *) "OOO:MessageWrapper_close", &arg0, &_unused_arg1, &_unused_arg2)) SWIG_fail;

  void *argp0;
  int   result;

  result = SWIG_ConvertPtr (arg0, &argp0, SWIGTYPE_p_MessageWrapper, 0 | 0);
  if (!SWIG_IsOK (result))
    SWIG_exception_fail (SWIG_ArgError (result), "in method 'MessageWrapper_close', self of type 'MessageWrapper *'");
  pMsgWrapper = reinterpret_cast <MessageWrapper *> (argp0);

  PyObject *resultobj;
  PyObject *pyData;

  result    = pMsgWrapper->close (&pData, &nData);
  resultobj = SWIG_From_int (static_cast <int> (result));

  if (result == 0) {
    pyData = Py_BuildValue ((char *) "y#", pData, nData);
    (void) memset (pData, 0, nData);
    (void) free (pData);
  }
  else
    pyData = Py_None;

  resultobj = SWIG_Python_AppendOutput (resultobj, pyData);

  return resultobj;

fail:

  SWIG_SetErrorMsg (PyExc_NotImplementedError, "Wrong number or type of arguments for overloaded function 'MessageWrapper_close'.\n"
    "  Possible C/C++ prototypes are:\n"
    "    MessageWrapper::close(void **,size_t*)\n");

  return nullptr;
}


static PyObject *_pyDiagPrint = nullptr;

void SetDiagPrint (PyObject *_func)
{
  _pyDiagPrint = _func;
}

  void
diagPrint (char *pMsg)
{
  if (_pyDiagPrint /* != nullptr */)
    (void) PyObject_CallFunction (_pyDiagPrint, "s", pMsg);
}

#ifdef __cplusplus
}
#endif
