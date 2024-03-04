#include <algorithm>
#include <cctype>
#include <cerrno>
#include <cstdint>
#include <fstream>
#include <iostream>
#include <limits>
#include <unordered_map>
#include <sstream>
#include <string>
#include <vector>
#include "sha256.h"

#include <libgen.h>     /* dirname */
#include <netdb.h>
#include <stdlib.h>     /* atoi, lrand48 */
#include <stdio.h>
#include <string.h>
#include <sys/ioctl.h>
#include <sys/stat.h>
#include <sys/wait.h>

#include <jsoncpp/json/json.h>
#include <event2/event.h>

#include "StringUtility.h"

// https://github.com/sni/mod_gearman/blob/master/common/popenRWE.c
// https://github.com/sni/mod_gearman/blob/master/include/popenRWE.h
#include "popenRWE.h"

#include "CLICodec.h"

// https://stackoverflow.com/questions/1486904/how-do-i-best-silence-a-warning-about-unused-variables
#define _UNUSED(expr) do {(void) (expr);} while (0)

extern "C" void diagPrint (char *);

#define _STR_PTR(_str)          const_cast <char *> ((_str).c_str ())

#define _SS_DIAGPRINT(_sExpr) {         \
  std::stringstream _ss;                \
                                        \
  _ss << _sExpr;                        \
                                        \
  diagPrint (_STR_PTR (_ss.str ()));    \
}

#if 0
  #define _DIAGPRINT_
#endif

#if 01
  #define _TIME_LSEED48_          // if #defined, calls srand48 (time (nullptr)); impacts ImagePath::getRandom ()
#endif


typedef std::vector<std::string>                      StringList;
typedef std::unordered_map<const char *, std::string> ReplaceMap;

typedef union {
  uint32_t u_int_32;
  u_int8_t u_int_8[4];

} _FourByteUnion;


  static bool
_fileExists (std::string path)
{
  char *pPath = _STR_PTR (path);

  //  _SS_DIAGPRINT ("In _fileExists (\"" << pPath << "\", " << strlen (pPath) << ")");

  if (pPath /* != nullptr */) {
    struct stat stat_buf;

    return stat (pPath, &stat_buf) == 0;
  }
  else
    return false;
}


MediaPath::MediaPath (std::string path, size_t capacity)
{
  //  _SS_DIAGPRINT ("MediaPath::MediaPath (\"" << path << "\", " << capacity << "\")");

  _mediaPath = path;
  _capacity  = capacity;
}


MediaPaths::MediaPaths (const std::string &mediaCapacities, size_t maxCapacity)
{
  if (_fileExists (mediaCapacities)) {

    // https://www.tutorialspoint.com/read-file-line-by-line-using-cplusplus

    std::ifstream inFile;

    inFile.open (mediaCapacities);

    if (inFile.is_open ()) {
      std::string dirName = dirname (_STR_PTR (mediaCapacities));
      std::string tp;
      #define     _TAB_CSEP "\t"

      //      _SS_DIAGPRINT ("MediaPaths::MediaPaths (): dirName (" << dirName << ")");

      while (getline (inFile, tp)) {
        char   *cStr     = strdup (tp.c_str ());
        char   *current  = strtok (cStr, _TAB_CSEP);
        char   *pPath    = nullptr;
        size_t  capacity = 0;
        std::string path;

        while (current /* != NULL */) {
          if (pPath == nullptr) {
            pPath = current;
            path  = std::string (pPath);
          }
          else {
            capacity = static_cast <size_t> (atoi (current));
            break;
          }

          current = strtok (nullptr, _TAB_CSEP);
        }

        if (!_fileExists (path))
          path = dirName + "/" + path;

        if (_fileExists (path) && capacity /* > 0 */) {
          if (maxCapacity /* > 0 */ && capacity > maxCapacity)
            capacity = maxCapacity;

          _activeMediaPaths.push_back (new MediaPath (path, capacity));
        }
#if defined (_DIAGPRINT_)
        else {
          _SS_DIAGPRINT ("MediaPaths (): \"" << path << "\" not found"
                         " or bad or missing capacity (" << capacity << ")");
        }
#endif
        free (cStr);
      }

      #undef _TAB_CSEP

      inFile.close ();

      #if defined (_TIME_LSEED48_)
      srand48 (time (nullptr));   // impacts MediaPaths::getRandom () lrand48 () calls
      #endif
    }
  }
}

  MediaPathPtr
MediaPaths::getRandom ()
{
  unsigned int numActive = size ();

  if (numActive /* > 0 */) {
    unsigned long idx       = static_cast <unsigned long> (lrand48 () % numActive);
    MediaPathPtr  media_ptr = _activeMediaPaths.at (idx);

    _activeMediaPaths.erase (_activeMediaPaths.begin () + static_cast <long> (idx));
    _usedMediaPaths.push_back (media_ptr);

    if (_activeMediaPaths.empty ())
      _activeMediaPaths.swap (_usedMediaPaths);

    return media_ptr;
  }

  return nullptr;
}

  static void
_cleanUp (std::vector<MediaPathPtr> mediaPaths)
{
  while (!mediaPaths.empty ()) {
    delete mediaPaths.back ();
    mediaPaths.pop_back ();
  }
}

  void
MediaPaths::cleanUp ()
{
  _cleanUp (_activeMediaPaths);
  _cleanUp (_usedMediaPaths);
}

  static StringList
_replaceStrings (StringList sList, ReplaceMap replaceMap)
{
  StringList retList;

  for (auto eStr : sList) {
    for (const auto& kv : replaceMap) {
      eStr = StringUtility::replaceAll (eStr.c_str (), kv.first, kv.second);
    }

    retList.push_back (eStr);
  }

  return retList;
}

  class
_RunCodec
{
 private:
  static struct event *_freeEvent (struct event *pEvent);

  static void EventOutCB   (evutil_socket_t fd, short what, void *arg);
  static void EventInOutCB (evutil_socket_t fd, short what, void *arg);
  static void EventInErrCB (evutil_socket_t fd, short what, void *arg);
  static void _EventInFn   (_RunCodec *runCodec, evutil_socket_t fd,
                            char **pIn, size_t *nIn, size_t *nextIn, size_t *capIn);
  char    *_pMsgIn;
  size_t   _nMsgIn;

  char   **_pMsgOut;
  size_t  *_nMsgOut;
  size_t   _nextOut;
  size_t   _capOut;

  char    *_pError;
  size_t   _nError;
  size_t   _nextErr;
  size_t   _capError;

  int      _rwepipe[3];
  int      _pid;

  int      _status;
  int      _pidStatus;

  struct event *_evIn;
  struct event *_evOut;
  struct event *_evErr;

  void _freeEVIn ();
  void _endLibevent ();

 public:
  ~_RunCodec ();

  int run (std::string codecPath, std::string args,
           void  *pMsgIn,  size_t  nMsgIn,
           void  *pMsgOut, size_t *nMsgOut);

  std::string error ();
};

  void
_RunCodec::EventOutCB (evutil_socket_t evFD, short what, void *arg)
{
  int        fd       = static_cast <int> (evFD);
  _RunCodec *runCodec = static_cast <_RunCodec *> (arg);
  ssize_t    nWrite   = write (fd, runCodec->_pMsgIn, runCodec->_nMsgIn);

  _UNUSED (what);

  if (nWrite > 0) {
    size_t nAdd = static_cast <size_t> (nWrite);

    runCodec->_pMsgIn += nAdd;
    runCodec->_nMsgIn -= nAdd;

    if (runCodec->_nMsgIn == 0) {
      (void) close (fd);
      runCodec->_freeEVIn ();
    }
  }
  else {
    runCodec->_freeEVIn ();
    runCodec->_status = -errno;
  }
}

  void
_RunCodec::EventInOutCB (evutil_socket_t fd, short what, void *arg)
{
  _RunCodec *runCodec = static_cast <_RunCodec *> (arg);

  _UNUSED (what);

  _RunCodec::_EventInFn (runCodec, fd,
                         runCodec->_pMsgOut,  runCodec->_nMsgOut,
                         &runCodec->_nextOut, &runCodec->_capOut);
}

  void
_RunCodec::EventInErrCB (evutil_socket_t fd, short what, void *arg)
{
  _RunCodec *runCodec = static_cast <_RunCodec *> (arg);

  _UNUSED (what);

  _RunCodec::_EventInFn (runCodec, fd,
                         &runCodec->_pError,  &runCodec->_nError,
                         &runCodec->_nextErr, &runCodec->_capError);
}

  void
_RunCodec::_EventInFn (_RunCodec *runCodec, evutil_socket_t evFD,
                       char **pIn, size_t *nIn, size_t *nextIn, size_t *capIn)
{
  int  fd     = static_cast <int> (evFD);
  int  nRead;
  bool fAlloc = false;

  (void) ioctl (fd, FIONREAD, &nRead);

  while (true) {
    size_t nAvail = *capIn - *nextIn;

    if (nAvail >= static_cast <size_t> (nRead))
      break;

    fAlloc = true;

    if (*capIn /* > 0 */)
      *capIn *= 2;
    else
      *capIn  = 1024;
  }

  if (fAlloc)
    *pIn = static_cast <char *> (realloc (*pIn, *capIn));

  ssize_t nHave = read (fd, *pIn + *nextIn, static_cast <size_t> (nRead));

  if (nHave > 0) {
    size_t nAdd = static_cast <size_t> (nHave);

    *nIn    += nAdd;
    *nextIn += nAdd;
  }
  else {
    if (errno != EBADF && errno != EAGAIN)
      runCodec->_status = -errno;

    runCodec->_endLibevent ();
  }
}

  int
_RunCodec::run (std::string codecPath, std::string args,
                void  *pMsgIn,  size_t  nMsgIn,
                void  *pMsgOut, size_t *nMsgOut)
{
  _pMsgIn   = static_cast <char *>  (pMsgIn);
  _nMsgIn   = nMsgIn;
  _pMsgOut  = static_cast <char **> (pMsgOut);
  _nMsgOut  = nMsgOut;
  _nextOut  = 0;
  _capOut   = 0;
  _pError   = (char *) NULL;
  _nError   = 0;
  _nextErr  = 0;
  _capError = 0;

  *_pMsgOut = (char *) NULL;
  *_nMsgOut = 0;

  _status   = 0;

  _SS_DIAGPRINT ("::run (" << codecPath << ", \"" << args << "\")");

  char **tokens = StringUtility::tokenize (args.c_str (), " ");

  _pid = popenRWE (_rwepipe, codecPath.c_str (), tokens);

  StringUtility::releaseTokens (tokens);

  if      (_pid < 0)   /* fork () failed */
    return _pid;

  else if (_pid > 0) { /* parent */

    // http://www.wangafu.net/~nickm/libevent-book/

    struct event_base *_evBase = event_base_new ();

    _evIn   = event_new (_evBase, _rwepipe[0], EV_WRITE | EV_PERSIST, EventOutCB,   this);
    _evOut  = event_new (_evBase, _rwepipe[1], EV_READ  | EV_PERSIST, EventInOutCB, this);
    _evErr  = event_new (_evBase, _rwepipe[2], EV_READ  | EV_PERSIST, EventInErrCB, this);

    event_add (_evIn,  (struct timeval *) NULL);
    event_add (_evOut, (struct timeval *) NULL);
    event_add (_evErr, (struct timeval *) NULL);

    event_base_dispatch (_evBase);
    event_base_free     (_evBase);

    if (_status /* != 0 */)
      _SS_DIAGPRINT ("::run (" << codecPath << "): base " << _status << ", _nMsgOut = " << *_nMsgOut);

    _status = WIFEXITED (_pidStatus) ? WEXITSTATUS (_pidStatus) : -1;

    if (_status /* != 0 */) {
      if (*_pMsgOut /* != (char *) NULL */) {
        free (*_pMsgOut);
        *_pMsgOut = (char *) NULL;
        *_nMsgOut = 0;
      }
    }

    _SS_DIAGPRINT ("::run (" << codecPath << "): " << _status << ", _nMsgOut = " << *_nMsgOut);

    if (_status /* != 0 */) {
      if (WIFSIGNALED (_pidStatus)) {
        _SS_DIAGPRINT (codecPath << " terminated with signal " << WTERMSIG (_pidStatus));
#ifdef WCOREDUMP
        if (WCOREDUMP (_pidStatus))
          _SS_DIAGPRINT (codecPath << " core dumped");
#endif
      }
      else if (WIFSTOPPED (_pidStatus)) {
        _SS_DIAGPRINT (codecPath << " stopped by signal " << WSTOPSIG (_pidStatus));
      }
    }

    return _status;
  }
  else if (_pid == 0) { /* child */
    // Shouldn't happen
  }

  return -1;
}

  struct event *
_RunCodec::_freeEvent (struct event *pEvent)
{
  if (pEvent /* != (struct event *) NULL */)
    event_free (pEvent);

  return (struct event *) NULL;
}

  void
_RunCodec::_freeEVIn ()
{
  _evIn = _freeEvent (_evIn);
}

  void
_RunCodec::_endLibevent ()
{
  _freeEVIn ();
  _evOut = _freeEvent (_evOut);
  _evErr = _freeEvent (_evErr);

  if (pcloseRWE2 (_pid, _rwepipe, &_pidStatus) != _pid)
    _status = -1;
}

_RunCodec::~_RunCodec ()
{
  if (_pError /* != (char *) NULL */) {
    free (_pError);
    _pError = (char *) NULL;
    _nError = 0;
  }
}

  std::string
_RunCodec::error ()
{
  if (_pError /* != (char *) NULL */)
    return std::string (_pError, _nError);
  else
    return "";
}


class _PassThruCodec: public CLICodec
{
 private:
  int _passThru (void *pMsgIn, size_t nMsgIn, void **pMsgOut, size_t *nMsgOut) {
    char   **pCMsgOut = reinterpret_cast <char **> (pMsgOut);
    FILE    *dfp      = open_memstream (pCMsgOut, nMsgOut);
    size_t   nWrite   = fwrite (pMsgIn, nMsgIn, 1, dfp);
    int      retVal   = nWrite == 1 ? 0 : -1;

    //    _SS_DIAGPRINT ("_passThru (" << nMsgIn << ").fwrite () = " << nWrite << ", retVal = " << retVal);

    if (fclose (dfp) /* != 0 */)
      retVal = -1;

    return retVal;
  }

 public:
  _PassThruCodec () {}

  MediaPathPtr getRandomMedia () override {
    _SS_DIAGPRINT ("CLICodec: getRandomMedia");
    return nullptr;
  }

  int encode (void *pMsgIn, size_t nMsgIn, void **pMsgOut, size_t *nMsgOut, MediaPathPtr mediaPtr = nullptr) override {
    std::ignore = mediaPtr;
    
    //    _SS_DIAGPRINT ("_PassThru::encode (" << nMsgIn << ")");
    return _passThru (pMsgIn, nMsgIn, pMsgOut, nMsgOut);
  }
  int decode (void *pMsgIn, size_t nMsgIn, void **pMsgOut, size_t *nMsgOut) override {
    //    _SS_DIAGPRINT ("_PassThru::decode (" << nMsgIn << ")");
    return _passThru (pMsgIn, nMsgIn, pMsgOut, nMsgOut);
  }
};


#define _CODEC_MEDIA_KEY        "media"
#define _CODEC_CAPACITY_KEY       "capacities"
#define _CODEC_MAX_CAP_KEY        "maximum"
#define _CODEC_PATH_KEY         "path"
#define _CODEC_AND_PATH_KEY     "android_path"
#define _CODEC_AND_MKSH         "/system/bin/sh"
#define _CODEC_ARGS_KEY         "args"
#define _CODEC_ARGS_COM_KEY       "common"
#define _CODEC_ARGS_ENC_KEY       "encode"
#define _CODEC_ARGS_DEC_KEY       "decode"

#define _CODEC_COVER_FILE_SYM   "<coverfile>"
#define _CODEC_SECRET_SYM       "<secret>"


  static Json::Value
_getJSONMap (const Json::Value &root, const char *pKey)
{
  Json::Value _obj = root.get (pKey, Json::Value::null);

  if (_obj.type () == Json::objectValue)
    return _obj;
  else
    return nullptr;
} 

  static std::string
_getJSONString (const Json::Value &root, const char *pKey, std::string _default = "")
{
  Json::Value _obj = root.get (pKey, Json::Value::null);

  if (_obj.type () == Json::stringValue)
    return _obj.asString ();
  else
    return _default;
} 

  static int
_getJSONInt (const Json::Value &root, const char *pKey, int defaultValue)
{
  Json::Value     _obj  = root.get (pKey, Json::Value::null);
  Json::ValueType _type = _obj.type ();

  if (_type == Json::intValue || _type == Json::uintValue)
    return _obj.asInt ();
  else
    return defaultValue;
} 


static Json::Value jCodecs;
static std::vector <std::string> _codecNames;


  bool
CLICodec::SetCodecsSpec (std::string codecsSpec)
{
  bool _isGood = true;

  do {        // "Do once" loop to expedite graceful error exit

    Json::Reader jReader;

    _isGood = jReader.parse (codecsSpec, jCodecs);

    if (!_isGood) {
      _SS_DIAGPRINT ("CLICodec::SetCodecsSpec () ERROR: failed to parse codecs JSON (\"" << codecsSpec << "\").");
      break;
    }

    _isGood = jCodecs.type () == Json::objectValue;

    if (!_isGood) {
      _SS_DIAGPRINT ("CLICodec::SetCodecsSpec () ERROR: expecting a top-level map and not \"" << codecsSpec << "\".");
      break;
    }

    // Create a list of codec names

    for (Json::ValueIterator itr = jCodecs.begin (); itr != jCodecs.end (); itr++)
      _codecNames.push_back (itr.key ().asString ());

  } while (false);

  return _isGood;
}

  std::vector <std::string>
CLICodec::GetCodecNames ()
{
  return _codecNames;
}

  CLICodec *
CLICodec::GetNamedCodec (std::string codecName)
{
  //  _SS_DIAGPRINT ("CLICodec::GetNamedCodec (" << codecName << ")");

  if (codecName == "\"__PASSTHRU__\"")
    return new _PassThruCodec ();

  do {        // "Do once" loop to expedite graceful error exit

    Json::Value jCodecSpec = _getJSONMap (jCodecs, codecName.c_str ());

    if (jCodecSpec == Json::Value::null) {
      _SS_DIAGPRINT ("CLICodec::GetNamedCodec () ERROR: no codec named (\"" << codecName << "\").");
      break;
    }

    //    _SS_DIAGPRINT ("CLICodec::GetNamedCodec (" << codecName << ")");

    #if 0
    {
      Json::StyledWriter styledWriter;
      std::string jSpecStr = styledWriter.write (jCodecSpec);

      _SS_DIAGPRINT ("Before new CLICodec (" << jSpecStr << ")");
    }
    #endif

    CLICodec *pCodec = new CLICodec (jCodecSpec);

    //    _SS_DIAGPRINT ("After new CLICodec (" "): " << pCodec);

    if (pCodec->isGood ())
      return pCodec;

    else {
      delete pCodec;
      break;
    }

  } while (false);

  return nullptr;
}

// *** Testing ***

  CLICodec *
CLICodec::GetCodecFromSpec (std::string jsonSpec)
{
  do {        // "Do once" loop to expedite graceful error exit

    // https://netxgate.wordpress.com/2018/05/20/how-to-install-and-use-jsoncpp-library-on-linux-ubuntu/

    Json::Reader jReader;
    Json::Value  jRoot;

    if (!jReader.parse (jsonSpec, jRoot)) {
      _SS_DIAGPRINT ("CLICodec () ERROR: failed to parse JSON (\"" << jsonSpec << "\").");

      break;
    }

    if (jRoot.type () != Json::objectValue) {
      _SS_DIAGPRINT ("CLICodec::GetCodecFromSpec () ERROR: expecting a map and not \"" << jsonSpec << "\".");

      break;
    }

    return new CLICodec (jRoot);

  } while (false);

  return nullptr;
}

CLICodec::CLICodec (Json::Value jRoot)
{
  _mediaPaths   = nullptr;
  _secret       = 0;
  _lastMediaPtr = nullptr;

  do {        // "Do once" loop to expedite graceful error exit

    _isGood = jRoot.type () == Json::objectValue;

    if (!_isGood) {
      Json::StyledWriter styledWriter;

      _SS_DIAGPRINT ("CLICodec::CLICodec () ERROR: JSON object is not a map (\"" << styledWriter.write (jRoot) << "\").");
    }

    // "path"

    _codecPath = _getJSONString (jRoot, _CODEC_PATH_KEY);

    _isGood = _fileExists (_codecPath);

    if (!_isGood) {
      _SS_DIAGPRINT ("CLICodec::CLICodec () ERROR: missing or non-existent wrapper (\""
                      << (_codecPath.length () /* > 0 */ ? _codecPath : "<missing>") << "\").");
      break;
    }

    // Check if "android_path" was specified and differs from "path"

    auto _a_path = _getJSONString (jRoot, _CODEC_AND_PATH_KEY);

    _isAndroid = _a_path.length () /* > 0 */ && _a_path.compare (_codecPath) == 0;

    // "args"

    Json::Value jArgs = _getJSONMap (jRoot, _CODEC_ARGS_KEY);

    _isGood = jArgs != Json::Value::null;
  
    if (!_isGood) {
      Json::StyledWriter styledWriter;
      std::string        jsonArgs = jArgs != Json::Value::null
                                      ? styledWriter.write (jArgs)
                                      : "<missing>";

      _SS_DIAGPRINT ("CLICodec::CLICodec () ERROR: expecting a map for \"args\" but have \"" << jsonArgs << "\".");

      break;
    }

    // "args":"common"

    _commonArgs = _getJSONString (jArgs, _CODEC_ARGS_COM_KEY);

    // "args":"encode"

    _encodeArgs = _getJSONString (jArgs, _CODEC_ARGS_ENC_KEY);

    _isGood = _encodeArgs.find (_CODEC_COVER_FILE_SYM) != std::string::npos;

    if (!_isGood) {
      _SS_DIAGPRINT ("CLICodec::CLICodec () ERROR: \"args\":\"encode\" (\"%s\") does not contain \""
                     _CODEC_COVER_FILE_SYM "."
                     << _encodeArgs.length () /* > 0 */ ? _encodeArgs : "<missing>");

      break;
    }

    // "args":"decode"

    _decodeArgs = _getJSONString (jArgs, _CODEC_ARGS_DEC_KEY);

    // "media"

    Json::Value jMedia = _getJSONMap (jRoot, _CODEC_MEDIA_KEY);

    _isGood = jMedia != Json::Value::null;

    if (!_isGood) {
      Json::StyledWriter styledWriter;
      std::string        jsonMedia = jMedia != Json::Value::null
                                       ? styledWriter.write (jArgs)
                                       : "<missing>";

      _SS_DIAGPRINT ("CLICodec::CLICodec () ERROR: expecting a map for \"media\" but have \"" << jsonMedia << "\".");

      break;
    }

    // "media":{"capacities", "maximum"}

    std::string capacitiesPath = _getJSONString (jMedia, _CODEC_CAPACITY_KEY);
    size_t      maxCapacity    = static_cast <size_t> (_getJSONInt (jMedia, _CODEC_MAX_CAP_KEY, 0));

    _mediaPaths = new MediaPaths (capacitiesPath, maxCapacity);

    _isGood     = _mediaPaths->isGood ();

    if (!_isGood) {
      _SS_DIAGPRINT ("CLICodec::CLICodec () ERROR: bad or empty capacities file: \""
                     << (capacitiesPath.length () /* > 0 */ ? capacitiesPath : "<missing>")
                     << "\".");
      
      break;
    }

  } while (false);
}

  MediaPathPtr
CLICodec::getRandomMedia ()
{
  _lastMediaPtr = _mediaPaths->getRandom ();

  return _lastMediaPtr;
}


  uint32_t
CLICodec::ipv4FromHostPersona (std::string ipStr)
{
  string s = sha256(ipStr.c_str()).substr(0,4);
  char * p;  
  uint32_t n = strtoul( s.c_str(), &p, 16 );

  if ( *p != 0 ) {
    _SS_DIAGPRINT ("Error in IPv4 computation");
    return 0;
  }

  _SS_DIAGPRINT ("ALERT CPP " << ipStr << " " << n << " " << ipStr.find("race-"));

  return n;
}


  uint32_t
CLICodec::ipv4FromHost (std::string ipStr)
{

  if (ipStr.find ("race-") != std::string::npos)
    return ipv4FromHostPersona (ipStr);
      
  const struct hostent *he = gethostbyname (ipStr.c_str ());
  if (he == nullptr)
    return 0UL;

  size_t ip_len = static_cast<size_t> (he->h_length);
  uint32_t ipV4 = 0UL;

  if (ip_len == 4)
    (void) memcpy (&ipV4, he->h_addr_list[0], ip_len);

  return ipV4;
}



  int
CLICodec::encode (void *message, size_t message_length, void **pMsgOut, size_t *nMsgOut,
                  MediaPathPtr mediaPtr)
{
  if (message_length /* > 0 */ && (_mediaPaths->isGood () || mediaPtr /* != nullptr */)) {
    if (mediaPtr == nullptr)
      mediaPtr = _lastMediaPtr /* != nullptr */ ? _lastMediaPtr : _mediaPaths->getRandom ();

    _lastMediaPtr = nullptr;

    // encode!

    StringList  sList {_commonArgs, _encodeArgs};
    ReplaceMap  rMap  {{_CODEC_SECRET_SYM,     std::to_string (_secret)},
                       {_CODEC_COVER_FILE_SYM, mediaPtr->path ()}};
    StringList  rList = _replaceStrings (sList, rMap);
    std::string _aArg = _isAndroid ? _codecPath : "";
    std::string args  = StringUtility::joinStrings (" ",
                                                    "_encoder_",
                                                    _aArg.c_str (),
                                                    "encode",
                                                    rList[0].c_str (),
                                                    rList[1].c_str (),
                                                    (char *) NULL);

    _SS_DIAGPRINT ("Before " << _codecPath << ", " << message_length);

    _RunCodec runCodec;
    int       retVal  = runCodec.run (_isAndroid ? _CODEC_AND_MKSH : _codecPath, args, message, message_length, pMsgOut, nMsgOut);

#if defined (_DIAGPRINT_)
  if (retVal /* != 0 */) {
    _SS_DIAGPRINT (_codecPath << " encode failed: " << retVal);
    _SS_DIAGPRINT (runCodec.error ());
  }
#endif

    return retVal;
  }
  else
    return -1;
}

  int
CLICodec::decode (void *pMsgIn, size_t nMsgIn, void **pMsgOut, size_t *nMsgOut)
{
  StringList  sList {_commonArgs, _decodeArgs};
  ReplaceMap  rMap  {{_CODEC_SECRET_SYM, std::to_string (_secret)}};
  StringList  rList = _replaceStrings (sList, rMap);
  std::string _aArg = _isAndroid ? _codecPath : "";
  std::string args  = StringUtility::joinStrings (" ",
                                                  "_decoder_",
                                                  _aArg.c_str (),
                                                  "decode",
                                                  rList[0].c_str (),
                                                  rList[1].c_str (),
                                                  (char *) NULL);
  /*
   * decode!
   */
  _RunCodec runCodec;
  int       retVal  = runCodec.run (_isAndroid ? _CODEC_AND_MKSH : _codecPath, args, pMsgIn, nMsgIn, pMsgOut, nMsgOut);

#if defined (_DIAGPRINT_)
  if (retVal /* != 0 */) {
    _SS_DIAGPRINT (_codecPath << " decode failed: " << retVal);
    _SS_DIAGPRINT (runCodec.error ());
  }
#endif

  return retVal;
}


#define _KEY_EXPR(_h, _i1, _i2, _i3, _i4)   \
    static_cast <uint32_t> (((_h.u_int_8[_i1] << 8) | _h.u_int_8[_i2]) ^ ((_h.u_int_8[_i3] << 8) | _h.u_int_8[_i4]))

#define _KEY_EXPR_H(_h, _i1, _i2, _i3, _i4) _KEY_EXPR(_uhost##_h, _i1, _i2, _i3, _i4)

  uint32_t
CLICodec::makeSecret (uint32_t ip1, uint32_t ip2)
{
  _FourByteUnion _uhost1 = {ip1};
  _FourByteUnion _uhost2 = {ip2};
  uint32_t       seed;

#if 0
  seed  = ((_uhost1.u_int_8[1] << 8) | _uhost1.u_int_8[2]) ^ ((_uhost1.u_int_8[3] << 8) | _uhost1.u_int_8[0]);
  seed ^= ((_uhost2.u_int_8[0] << 8) | _uhost2.u_int_8[1]) ^ ((_uhost2.u_int_8[2] << 8) | _uhost2.u_int_8[3]);
#else
  seed  = _KEY_EXPR_H (1, 1, 2, 3, 0);
  seed ^= _KEY_EXPR_H (2, 0, 1, 2, 3);
#endif

  return seed;
}

  void
CLICodec::setSecret (std::string host1, std::string host2)
{
  setSecret (ipv4FromHost (host1), ipv4FromHost (host2));
}

  void
CLICodec::setSecret (uint32_t ip1, uint32_t ip2)
{
  setSecret (makeSecret (ip1, ip2));
}

  void
CLICodec::setSecret (uint32_t secret)
{
  _secret = secret;
}
