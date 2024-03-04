#include <algorithm>
#include <cctype>
#include <cerrno>
#include <cmath>
#include <cstdint>
#include <fstream>
#include <iostream>
#include <limits>
#include <unordered_map>
#include <sstream>
#include <string>
#include <vector>

#include <libgen.h>     /* dirname */
#include <netdb.h>
#include <stdlib.h>     /* atoi, lrand48 */
#include <stdio.h>
#include <string.h>
#include <sys/ioctl.h>
#include <sys/stat.h>   /* stat, chmod */
#include <sys/wait.h>

#include <event2/event.h>

#include "StringUtility.h"
#include "CLICodec.h"

#if defined (USE_FORK)
#include "popenRWE.c"
#else
#include "popenPSpawn.c"
#endif

// https://stackoverflow.com/questions/1486904/how-do-i-best-silence-a-warning-about-unused-variables
#define _UNUSED(expr) do {(void) (expr);} while (0)

extern "C" void diagPrint (char *);
 
static int         _needLPath = 1;
static std::string _logPath   = "";

  static void
_diagPrint (const std::string &_sStr)
{
  if (_needLPath /* != 0 */) {
    std::string _dirs[] = {"/log", "/tmp", ""};

    _needLPath = 0;

    for (auto _idx = 0; _dirs[_idx].length () /* > 0 */; ++_idx) {
      std::string _pDir = _dirs[_idx];
      struct stat stat_buf;
      if (stat (_pDir.c_str (), &stat_buf) == 0 && S_ISDIR (stat_buf.st_mode)) {
        _logPath = _pDir + "/destini.log";
        break;
      }
    }
  }

  if (_logPath.length () /* > 0 */) {
    std::ofstream _diagOut;

    _diagOut.open (_logPath, std::ios_base::app);
    _diagOut << _sStr << std::endl;

    _diagOut.close ();
  }
}

// NOLINTNEXTLINE(bugprone-macro-parentheses)
#define _STR_PTR(_str)          const_cast <char *> ((_str).c_str ())

#if 0
#define _SS_DIAGPRINT(_sExpr) {         \
  std::stringstream _ss;                \
                                        \
  _ss << _sExpr;                        \
                                        \
  diagPrint (_STR_PTR (_ss.str ()));    \
}
#else
// Per https://stackoverflow.com/questions/61031309/disable-clang-tidy-warning-for-a-specific-macro
// and https://youtrack.jetbrains.com/issue/RSCPP-29029/Suppressing-bugprone-macro-parentheses-needs-to-use-comments-inside-the-macro
#if 0
// NOLINTNEXTLINE(bugprone-macro-parentheses)
#define _SS_DIAGPRINT(_sExpr) {std::stringstream _ss; _ss << _sExpr; diagPrint (_STR_PTR (_ss.str ()));}
#else
// NOLINTNEXTLINE(bugprone-macro-parentheses)
#define _SS_DIAGPRINT(_sExpr) {std::stringstream _ss; _ss << _sExpr; _diagPrint (_ss.str ());}
#endif
#endif

#if 01
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

  bool
fileExists (std::string path)
{
  auto pPath = _STR_PTR (path);

  //  _SS_DIAGPRINT ("In fileExists (\"" << pPath << "\", " << strlen (pPath) << ")");

  if (pPath /* != nullptr */) {
    struct stat stat_buf;

    return stat (pPath, &stat_buf) == 0;
  }
  else
    return false;
}


// NOLINTNEXTLINE(passedByValue)
MediaPath::MediaPath (const std::string &path, size_t capacity): _mediaPath (path), _capacity (capacity)
{
  //  _SS_DIAGPRINT ("MediaPath::MediaPath (\"" << path << "\", " << capacity << "\")");
}


MediaPaths::MediaPaths (const std::string &mediaCapacities, size_t maxCapacity)
{
  _minCapacity   = maxCapacity;
  _maxCapacity   = 0;

  if (fileExists (mediaCapacities)) {

    // https://www.tutorialspoint.com/read-file-line-by-line-using-cplusplus

    std::ifstream inFile;

    inFile.open (mediaCapacities);

    if (inFile.is_open ()) {
      double _sumCapacity   = 0.0;
      double _sumSqCapacity = 0.0;
      double _numLines      = 0.0;
      std::string tp;
      #define     _TAB_CSEP "\t"

      while (getline (inFile, tp)) {
        auto    cStr     = strdup (tp.c_str ());
        auto    current  = strtok (cStr, _TAB_CSEP);
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

        if (!fileExists (path))
          path = CLICodec::DirFilename (path);

        if (fileExists (path) && capacity /* > 0 */) {
          ++_numLines;

          if (maxCapacity /* > 0 */ && capacity > maxCapacity)
            capacity = maxCapacity;

          if (_minCapacity /* > 0 */ && capacity < _minCapacity)
              _minCapacity = capacity;

          if (capacity > _maxCapacity)
                  _maxCapacity = capacity;

          _sumCapacity   += capacity;
          _sumSqCapacity += static_cast <double> (capacity * capacity);

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

      if (_numLines > 0.0) {
        _avgCapacity    = _sumCapacity / _numLines;
        _stdDevCapacity = std::sqrt (_sumSqCapacity / _numLines - _avgCapacity * _avgCapacity);

        _SS_DIAGPRINT ("MediaPaths () count: " << static_cast <size_t> (_numLines) <<
                       " min/max: " << _minCapacity << "/" << _maxCapacity <<
                       " avg/std: " << _avgCapacity << "/" << _stdDevCapacity);
      }

      #if defined (_TIME_LSEED48_)
      srand48 (time (nullptr));   // impacts MediaPaths::getRandom () lrand48 () calls
      #endif
    }
  }
}

  MediaPathPtr
MediaPaths::getRandom ()
{
  auto numActive = size ();

  if (numActive /* > 0 */) {
    auto idx       = static_cast <unsigned long> (lrand48 () % numActive);
    auto media_ptr = _activeMediaPaths.at (idx);

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
  const char *_pMsgIn;
  size_t      _nMsgIn;

  char      **_pMsgOut;
  size_t     *_nMsgOut;
  size_t      _nextOut;
  size_t      _capOut;

  char       *_pError;
  size_t      _nError;
  size_t      _nextErr;
  size_t      _capError;

  int         _rwepipe[3];
  int         _pid;

  int         _status;
  int         _pidStatus;

  struct event *_evIn;
  struct event *_evOut;
  struct event *_evErr;

  void _freeEVIn ();
  void _endLibevent ();

 public:
  explicit _RunCodec ();
  ~_RunCodec ();

  int run (std::string codecPath, std::string args,
           const void  *pMsgIn,  size_t  nMsgIn,
           void        *pMsgOut, size_t *nMsgOut);

  std::string error ();
};

_RunCodec::_RunCodec ():
  _pMsgIn (nullptr),
  _nMsgIn (0),
  _pMsgOut (nullptr),
  _nMsgOut (nullptr),
  _nextOut (0),
  _capOut (0),
  _pError (nullptr),
  _nError (0),
  _nextErr (0),
  _capError (0),
  _rwepipe {0, 0, 0},
  _pid (0),
  _status (0),
  _pidStatus (0),
  _evIn (nullptr),
  _evOut (nullptr),
  _evErr (nullptr)
{
}

  void
_RunCodec::EventOutCB (evutil_socket_t evFD, short what, void *arg)
{
  auto fd       = static_cast <int> (evFD);
  auto runCodec = static_cast <_RunCodec *> (arg);
  auto nWrite   = write (fd, runCodec->_pMsgIn, runCodec->_nMsgIn);

  _UNUSED (what);

  if (nWrite >= 0) {
    auto nAdd = static_cast <size_t> (nWrite);

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
  auto runCodec = static_cast <_RunCodec *> (arg);

  _UNUSED (what);

  _RunCodec::_EventInFn (runCodec, fd,
                         runCodec->_pMsgOut,  runCodec->_nMsgOut,
                         &runCodec->_nextOut, &runCodec->_capOut);
}

  void
_RunCodec::EventInErrCB (evutil_socket_t fd, short what, void *arg)
{
  auto runCodec = static_cast <_RunCodec *> (arg);

  _UNUSED (what);

  _RunCodec::_EventInFn (runCodec, fd,
                         &runCodec->_pError,  &runCodec->_nError,
                         &runCodec->_nextErr, &runCodec->_capError);
}

  void
_RunCodec::_EventInFn (_RunCodec *runCodec, evutil_socket_t evFD,
                       char **pIn, size_t *nIn, size_t *nextIn, size_t *capIn)
{
  auto fd     = static_cast <int> (evFD);
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

  auto nHave = read (fd, *pIn + *nextIn, static_cast <size_t> (nRead));

  if (nHave > 0) {
    auto nAdd = static_cast <size_t> (nHave);

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
                const void  *pMsgIn,  size_t  nMsgIn,
                void        *pMsgOut, size_t *nMsgOut)
{
  _pMsgIn   = static_cast <const char *> (pMsgIn);
  _nMsgIn   = nMsgIn;
  _pMsgOut  = static_cast <char **> (pMsgOut);
  _nMsgOut  = nMsgOut;
  _nextOut  = 0;
  _capOut   = 0;
  _pError   = nullptr;
  _nError   = 0;
  _nextErr  = 0;
  _capError = 0;

  *_pMsgOut = nullptr;
  *_nMsgOut = 0;

  _status   = 0;

  _SS_DIAGPRINT ("::run (" << codecPath << ", \"" << args << "\")");

  auto tokens = StringUtility::tokenize (args.c_str (), " ");

  _SS_DIAGPRINT ("::run calling popenRWE");

  for (auto _pToks = tokens; *_pToks /* != (char *) NULL */; ++_pToks)
    _SS_DIAGPRINT ("::run argument token: \"" << *_pToks << "\"");

  _pid = popenRWE (_rwepipe, codecPath.c_str (), tokens);

  _SS_DIAGPRINT ("::run after popenRWE, pid = " << _pid);

  if      (_pid < 0)   /* fork () failed */
    return _pid;

  else if (_pid > 0) { /* parent */

    _SS_DIAGPRINT ("::run before calling releaseTokens");

    StringUtility::releaseTokens (tokens);

    _SS_DIAGPRINT ("::run released tokens");

    // http://www.wangafu.net/~nickm/libevent-book/

    auto _evBase = event_base_new ();

    _evIn  = event_new (_evBase, _rwepipe[0], EV_WRITE | EV_PERSIST, EventOutCB,   this);
    _evOut = event_new (_evBase, _rwepipe[1], EV_READ  | EV_PERSIST, EventInOutCB, this);
    _evErr = event_new (_evBase, _rwepipe[2], EV_READ  | EV_PERSIST, EventInErrCB, this);

    event_add (_evIn,  nullptr);
    event_add (_evOut, nullptr);
    event_add (_evErr, nullptr);

    event_base_dispatch (_evBase);
    event_base_free     (_evBase);

    if (_status /* != 0 */)
      _SS_DIAGPRINT ("::run (" << codecPath << "): base " << _status << ", _nMsgOut = " << *_nMsgOut);

    _status = WIFEXITED (_pidStatus) ? WEXITSTATUS (_pidStatus) : -1;

    if (_status /* != 0 */) {
      if (*_pMsgOut /* != (char *) NULL */) {
        free (*_pMsgOut);
        *_pMsgOut = nullptr;
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
    _SS_DIAGPRINT ("ERROR: " << codecPath << "(pid == 0)!");
  }

  return -1;
}

  struct event *
_RunCodec::_freeEvent (struct event *pEvent)
{
  if (pEvent /* != (struct event *) NULL */)
    event_free (pEvent);

  return nullptr;
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
    _pError = nullptr;
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
  int _passThru (const void *pMsgIn, size_t nMsgIn, void **pMsgOut, size_t *nMsgOut) {
    auto pCMsgOut = reinterpret_cast <char **> (pMsgOut);
    auto dfp      = open_memstream (pCMsgOut, nMsgOut);
    auto nWrite   = fwrite (pMsgIn, nMsgIn, 1, dfp);
    int  retVal   = nWrite == 1 ? 0 : -1;

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

  int encode (const void *pMsgIn, size_t nMsgIn, void **pMsgOut, size_t *nMsgOut, MediaPathPtr mediaPtr = nullptr) override {
    std::ignore = mediaPtr;

    //    _SS_DIAGPRINT ("_PassThru::encode (" << nMsgIn << ")");
    return _passThru (pMsgIn, nMsgIn, pMsgOut, nMsgOut);
  }
  int decode (const void *pMsgIn, size_t nMsgIn, void **pMsgOut, size_t *nMsgOut) override {
    //    _SS_DIAGPRINT ("_PassThru::decode (" << nMsgIn << ")");
    return _passThru (pMsgIn, nMsgIn, pMsgOut, nMsgOut);
  }
};


#define _CODEC_FORMAT_KEY       ".format"
#define _CODEC_DECOMP_VAL         "Decomposed-COMMS"
#define _CODEC_MEDIA_KEY        "media"
#define _CODEC_CAPACITY_KEY       "capacities"
#define _CODEC_MAX_CAP_KEY        "maximum"
#define _CODEC_MIME_TYPE_KEY    "mime-type"
#define _CODEC_ENC_TIME_KEY     "encodingTime"
#define _CODEC_PATH_KEY         "path"
#define _CODEC_AND_PATH_KEY     "android_path"
#define _CODEC_INIT_CMD_KEY     "initCommand"
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
  auto _obj = root.get (pKey, Json::Value::null);

  if (_obj.type () == Json::objectValue)
    return _obj;
  else
    return Json::Value::null;
}

  static std::string
_getJSONString (const Json::Value &root, const char *pKey, std::string _default = "")
{
  auto _obj = root.get (pKey, Json::Value::null);

  if (_obj.type () == Json::stringValue)
    return _obj.asString ();
  else
    return _default;
}

  static int
_getJSONInt (const Json::Value &root, const char *pKey, int defaultValue)
{
  auto _obj  = root.get (pKey, Json::Value::null);
  auto _type = _obj.type ();

  if (_type == Json::intValue || _type == Json::uintValue)
    return _obj.asInt ();
  else
    return defaultValue;
}

  static double
_getJSONDouble (const Json::Value &root, const char *pKey, double defaultValue)
{
  auto _obj  = root.get (pKey, Json::Value::null);
  auto _type = _obj.type ();

  if (_type == Json::realValue || _type == Json::intValue || _type == Json::uintValue)
    return _obj.asDouble ();
  else
    return defaultValue;
}


static Json::Value jCodecs;
static std::vector <std::string> _codecNames;

std::string CLICodec::_dirName = "";


  void
CLICodec::SetDirname (const std::string &dirName)
{
  _SS_DIAGPRINT ("CLICodec:SetDirname (\"" << dirName << "\")");
  CLICodec::_dirName = dirName;
}

  std::string
CLICodec::DirFilename (const std::string &subPath)
{
  // TODO: https://stackoverflow.com/questions/6297738/how-to-build-a-full-path-string-safely-from-separate-strings

  if (subPath.length () /* > 0 */ && CLICodec::_dirName.length () /* > 0 */) {
    std::string altPath = CLICodec::_dirName + "/" + subPath;
        if (fileExists (altPath))
          return altPath;
  }

  return subPath;
}

  bool
CLICodec::SetCodecsSpec (const std::string &codecsSpec)
{
  bool _isLGood = true;

  do {        // "Do once" loop to expedite graceful error exit

    Json::Reader jReader;

    _isLGood = jReader.parse (codecsSpec, jCodecs);

    if (!_isLGood) {
      _SS_DIAGPRINT ("CLICodec::SetCodecsSpec () ERROR: failed to parse codecs JSON (\"" << codecsSpec << "\").");
      break;
    }

    _isLGood = jCodecs.type () == Json::objectValue;

    if (!_isLGood) {
      _SS_DIAGPRINT ("CLICodec::SetCodecsSpec () ERROR: expecting a top-level map and not \"" << codecsSpec << "\".");
      break;
    }

    // Create a list of codec names

    for (Json::ValueIterator itr = jCodecs.begin (); itr != jCodecs.end (); itr++)
      _codecNames.push_back (itr.key ().asString ());

  } while (false);

  return _isLGood;
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

    auto jCodecSpec = _getJSONMap (jCodecs, codecName.c_str ());

    if (jCodecSpec == Json::Value::null) {
      _SS_DIAGPRINT ("CLICodec::GetNamedCodec () ERROR: no codec named (\"" << codecName << "\").");
      break;
    }

    //    _SS_DIAGPRINT ("CLICodec::GetNamedCodec (" << codecName << ")");

    #if 0
    {
      Json::StyledWriter styledWriter;
      auto jSpecStr = styledWriter.write (jCodecSpec);

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

  CLICodec *
CLICodec::GetCodecFromStream (std::istream &is)
{
  do {        // "Do once" loop to expedite graceful error exit

    // https://netxgate.wordpress.com/2018/05/20/how-to-install-and-use-jsoncpp-library-on-linux-ubuntu/

    Json::Reader jReader;
    Json::Value  jRoot;

    if (!jReader.parse (is, jRoot, false)) {
      _SS_DIAGPRINT ("CLICodec () ERROR: failed to parse JSON stream.");

      break;
    }

    if (jRoot.type () != Json::objectValue) {
      _SS_DIAGPRINT ("CLICodec::GetCodecFromSpec () ERROR: expecting a map and not \"" << jRoot.asString () << "\".");

      break;
    }

    return new CLICodec (jRoot);

  } while (false);

  return nullptr;
}

CLICodec::CLICodec (Json::Value jRoot):
  _mediaPaths (nullptr),
  _mimeType (""),
  _encodingTime (0),
  _secret (0),
  _lastMediaPtr (nullptr)
{
  do {        // "Do once" loop to expedite graceful error exit

    _isGood = jRoot.type () == Json::objectValue;

    if (!_isGood) {
      Json::StyledWriter styledWriter;

      _SS_DIAGPRINT ("CLICodec::CLICodec () ERROR: JSON object is not a map (\"" << styledWriter.write (jRoot) << "\").");
    }

    // ".format"

    auto _isDecomposedCOMMS = _getJSONString (jRoot, _CODEC_FORMAT_KEY) == _CODEC_DECOMP_VAL;

    // "initCommand"

    auto        _initCmd  = _getJSONString (jRoot, _CODEC_INIT_CMD_KEY);
    auto        _initToks = StringUtility::tokenize (_initCmd.c_str (), " ");
    auto        _initPath = DirFilename (std::string (*_initToks));
    std::string _initArgs = "";

    /* DirFilename () condition the arguments */

    if (_initPath.length () /* > 0 */) {
      for (auto _pToks = _initToks + 1; *_pToks /* != (char *) NULL */; ++_pToks) {
        auto _pTok = *_pToks;

        if (strlen (_pTok) /* > 0 */) {
          if (_initArgs.length () /* > 0 */)
            _initArgs += " ";

          std::string _pTokStr = std::string (_pTok);
          std::string _pArgStr = DirFilename (_pTokStr);
#if 0
          // Provisionally make argument executable

          if (_pTokStr != _pArgStr) {
            auto _cRetVal = chmod (_pArgStr.c_str (),
                                   S_IRUSR | S_IWUSR | S_IXUSR | S_IRGRP | S_IXGRP | S_IROTH | S_IXOTH);
            if (_cRetVal /* != 0 */)
              _SS_DIAGPRINT ("CLICodec::CLICodec (): chmod (\"" << _pArgStr << "\"): " << errno);
          }
#endif
          _initArgs += _pArgStr;
        }
      }
    }

    _SS_DIAGPRINT ("CLICodec::CLICodec (): Before releaseTokens ");
    StringUtility::releaseTokens (_initToks);

    _SS_DIAGPRINT ("CLICodec::CLICodec (): "
                   << _CODEC_INIT_CMD_KEY << ": \"" << _initCmd << "\" \""
                   << _initPath << "\" \"" << _initArgs << "\"");

    if (_initPath.length () /* > 0 */) {
      _RunCodec  runCodec;
      auto       pMsgOut = static_cast <void *> (NULL);
      size_t     nMsgOut;
      auto       retVal  = runCodec.run (_initPath, _initArgs, "", 0, &pMsgOut, &nMsgOut);

      _SS_DIAGPRINT ("HELLO: 1 (" << retVal << ")\n")

      _isGood = retVal == 0;

      if (_isGood && nMsgOut /* > 0 */) {
        void *_pMsgOut = realloc (pMsgOut, nMsgOut + 1);

        if (_pMsgOut /* != (void *) NULL */) {
          pMsgOut = _pMsgOut;
          char *pMsg = static_cast <char *> (pMsgOut);
          *(pMsg + nMsgOut) = '\0';             // NULL terminate string

          _SS_DIAGPRINT ("CLICodec::CLICodec () INFO: " << _initPath
                                             << " returned \"" << pMsg << "\"");
        }
      }

      _SS_DIAGPRINT ("HELLO: 2\n")
 
      if (nMsgOut /* > 0 */)
        free (pMsgOut);

      if (!_isGood) {
        _SS_DIAGPRINT ("CLICodec::CLICodec () ERROR: " << _initPath
                       << " returned " << retVal << " (" << runCodec.error () << ")");
        break;
      }
    }

    // "path"
    _SS_DIAGPRINT ("HELLO: 3\n")

    _codecPath = DirFilename (_getJSONString (jRoot, _CODEC_PATH_KEY));

    _isGood    = fileExists (_codecPath);

    if (!_isGood) {
      _SS_DIAGPRINT ("CLICodec::CLICodec () ERROR: missing or non-existent wrapper (\""
                      << (_codecPath.length () /* > 0 */ ? _codecPath : "<missing>") << "\").");
      break;
    }

    // Check if "android_path" was specified and differs from "path"

    _SS_DIAGPRINT ("HELLO: 4\n")

    auto _a_path = DirFilename (_getJSONString (jRoot, _CODEC_AND_PATH_KEY));

    _isAndroid = _a_path.length () /* > 0 */ && _a_path.compare (_codecPath) == 0;

    // "args"

    _SS_DIAGPRINT ("HELLO: 5\n")

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

    _SS_DIAGPRINT ("HELLO: 6\n")

    // "args":"common"

    _commonArgs = _getJSONString (jArgs, _CODEC_ARGS_COM_KEY);

    // "args":"encode"

    _encodeArgs = _getJSONString (jArgs, _CODEC_ARGS_ENC_KEY);

    _isGood = _encodeArgs.find (_CODEC_COVER_FILE_SYM) != std::string::npos;

    if (!_isGood) {
      _SS_DIAGPRINT ("CLICodec::CLICodec () ERROR: \"args\":\"encode\" (\"%s\") does not contain \""
                     _CODEC_COVER_FILE_SYM "."
                     << (_encodeArgs.length () /* > 0 */ ? _encodeArgs : "<missing>"));

      break;
    }

    _SS_DIAGPRINT ("HELLO: 7\n")

    // "args":"decode"

    _decodeArgs = _getJSONString (jArgs, _CODEC_ARGS_DEC_KEY);

    // "media"

    Json::Value jMedia = _getJSONMap (jRoot, _CODEC_MEDIA_KEY);

    _isGood = jMedia != Json::Value::null;

    _SS_DIAGPRINT ("HELLO: 8\n")

    if (!_isGood) {
      Json::StyledWriter styledWriter;
      std::string        jsonMedia = jMedia != Json::Value::null
                                       ? styledWriter.write (jArgs)
                                       : "<missing>";

      _SS_DIAGPRINT ("CLICodec::CLICodec () ERROR: expecting a map for \"media\" but have \"" << jsonMedia << "\".");

      break;
    }

    _SS_DIAGPRINT ("HELLO: 9\n")

    // "media":{"capacities", "maximum"}

    auto capacitiesPath = DirFilename (_getJSONString (jMedia, _CODEC_CAPACITY_KEY));
    auto maxCapacity    = static_cast <size_t> (_getJSONInt (jMedia, _CODEC_MAX_CAP_KEY, 0));

    _mediaPaths = new MediaPaths (capacitiesPath, maxCapacity);

    _isGood     = _mediaPaths->isGood ();

    if (!_isGood) {
      _SS_DIAGPRINT ("CLICodec::CLICodec () ERROR: bad or empty capacities file: \""
                     << (capacitiesPath.length () /* > 0 */ ? capacitiesPath : "<missing>")
                     << "\".");

      break;
    }

    _SS_DIAGPRINT ("HELLO: 10\n")

    // Decomposed COMMS

    if (_isDecomposedCOMMS) {

      // "mime-type"

      _mimeType = _getJSONString (jRoot, _CODEC_MIME_TYPE_KEY);

      _isGood   = _mimeType.length () > 0;

      if (!_isGood) {
        _SS_DIAGPRINT ("CLICodec::CLICodec () ERROR: missing \"mime-type\".");

        break;
      }

      _SS_DIAGPRINT ("HELLO: 11\n")

      // "encodingTime"

      _encodingTime = _getJSONDouble (jRoot, _CODEC_ENC_TIME_KEY, 0);

      _isGood       = _encodingTime != 0.0;

      if (!_isGood) {
        _SS_DIAGPRINT ("CLICodec::CLICodec () ERROR: missing \"encodingTime\".");

        break;
      }

      _SS_DIAGPRINT ("CLICodec::CLICodec (): "
                     << _CODEC_MIME_TYPE_KEY << ": \"" << _mimeType << ", "
                     << _CODEC_ENC_TIME_KEY  << ": \"" << _encodingTime << ".");
    }

  } while (false);

  _SS_DIAGPRINT ("CLICodec::CLICodec () returning");
}

  MediaPathPtr
CLICodec::getRandomMedia ()
{
  _lastMediaPtr = _mediaPaths->getRandom ();

  return _lastMediaPtr;
}

  uint32_t
CLICodec::ipv4FromHost (const std::string &ipStr)
{
  auto he = gethostbyname (ipStr.c_str ());
  if (he == nullptr)
    return 0UL;

  auto     ip_len = static_cast<size_t> (he->h_length);
  uint32_t ipV4   = 0UL;

  /* copy the network address to sockaddr_in structure */
  if (ip_len == 4)
    (void) memcpy (&ipV4, he->h_addr_list[0], ip_len);

  return ipV4;
}

  int
CLICodec::encode (const void *message, size_t message_length, void **pMsgOut, size_t *nMsgOut,
                  MediaPathPtr mediaPtr)
{
  _SS_DIAGPRINT ("CLICodec::encode (): " << message_length);

  if (_mediaPaths->isGood () || mediaPtr /* != nullptr */) {
    if (mediaPtr == nullptr)
      mediaPtr = _lastMediaPtr /* != nullptr */ ? _lastMediaPtr : _mediaPaths->getRandom ();

    _lastMediaPtr = nullptr;

    // encode!

    StringList  sList {_commonArgs, _encodeArgs};
    ReplaceMap  rMap  {{_CODEC_SECRET_SYM,     std::to_string (_secret)},
                       {_CODEC_COVER_FILE_SYM, mediaPtr->path ()}};
    auto        rList = _replaceStrings (sList, rMap);
    std::string _aArg = _isAndroid ? _codecPath : "";
    auto        args  = StringUtility::joinStrings (" ",
                                                    "_encoder_",
                                                    _aArg.c_str (),
                                                    "encode",
                                                    rList[0].c_str (),
                                                    rList[1].c_str (),
                                                    nullptr);

    _SS_DIAGPRINT ("Before " << _codecPath << ", " << message_length);

    _RunCodec runCodec;
    auto      retVal  = runCodec.run (_isAndroid ? _CODEC_AND_MKSH : _codecPath, args, message, message_length, pMsgOut, nMsgOut);

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
CLICodec::decode (const void *pMsgIn, size_t nMsgIn, void **pMsgOut, size_t *nMsgOut)
{
  _SS_DIAGPRINT ("CLICodec::decode (): " << nMsgIn);

  StringList  sList {_commonArgs, _decodeArgs};
  ReplaceMap  rMap  {{_CODEC_SECRET_SYM, std::to_string (_secret)}};
  auto        rList = _replaceStrings (sList, rMap);
  std::string _aArg = _isAndroid ? _codecPath : "";
  auto        args  = StringUtility::joinStrings (" ",
                                                  "_decoder_",
                                                  _aArg.c_str (),
                                                  "decode",
                                                  rList[0].c_str (),
                                                  rList[1].c_str (),
                                                  nullptr);
  /*
   * decode!
   */
  _RunCodec runCodec;
  auto      retVal  = runCodec.run (_isAndroid ? _CODEC_AND_MKSH : _codecPath, args, pMsgIn, nMsgIn, pMsgOut, nMsgOut);

#if defined (_DIAGPRINT_)
  if (retVal /* != 0 */) {
    _SS_DIAGPRINT (_codecPath << " decode failed: " << retVal);
    _SS_DIAGPRINT (runCodec.error ());
  }
#endif

  return retVal;
}


#define _KEY_EXPR(_h, _i1, _i2, _i3, _i4)   \
  static_cast <uint32_t> ((((_h).u_int_8[(_i1)] << 8) | (_h).u_int_8[(_i2)]) ^ (((_h).u_int_8[(_i3)] << 8) | (_h).u_int_8[(_i4)]))

#define _KEY_EXPR_H(_h, _i1, _i2, _i3, _i4) _KEY_EXPR(_uhost##_h, _i1, _i2, _i3, _i4)

  uint32_t
CLICodec::makeSecret (uint32_t ip1, uint32_t ip2)
{
  _FourByteUnion _uhost1;
  _FourByteUnion _uhost2;
  uint32_t       seed;

  _uhost1.u_int_32 = ip1;
  _uhost2.u_int_32 = ip2;

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
CLICodec::setSecret (const std::string &host1, const std::string &host2)
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

#if defined (_TEST_MAIN_)

  int
main (int argc, char **arg)
{
  _diagPrint ("A test.");

  return 0;
}

#endif
