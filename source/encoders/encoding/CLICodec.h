#ifndef __CLICODEC_H__

#include <cstdint>
#include <string>
#include <vector>

#ifdef __ANDROID__
#include <json/json.h>
#else
#include <jsoncpp/json/json.h>
#endif

bool fileExists (std::string path);


class MediaPath
{
 private:
  std::string _mediaPath;
  size_t      _capacity;

 public:
  MediaPath (const std::string &path, size_t capacity);

  std::string path ()     {return _mediaPath;};
  size_t      capacity () {return _capacity;};
};

typedef MediaPath *MediaPathPtr;


class MediaPaths
{
 private:
  std::vector<MediaPathPtr> _activeMediaPaths;
  std::vector<MediaPathPtr> _usedMediaPaths;
  size_t                    _minCapacity;
  size_t                    _maxCapacity;
  double                    _avgCapacity;
  double                    _stdDevCapacity;

 protected:
  explicit     MediaPaths (const std::string &mediaCapacities, size_t maxCapacity = 0);
  void         cleanUp ();
  friend class CLICodec;

 public:
  unsigned int size () {return _activeMediaPaths.size ();};
  MediaPathPtr getRandom ();
  size_t       minCapacity    () {return _minCapacity;}
  size_t       maxCapacity    () {return _maxCapacity;}
  double       avgCapacity    () {return _avgCapacity;}
  double       stdDevCapacity () {return _stdDevCapacity;}

  bool isGood () {return size () /* > 0 */;};
};

typedef MediaPaths *MediaPathsPtr;


class CLICodec
{
 private:
  static std::string _dirName;
  CLICodec& operator= (const CLICodec&);  // not implemented
  CLICodec (const CLICodec&);   // not implemented

 protected:
  MediaPathsPtr _mediaPaths;

  std::string   _mimeType;
  double        _encodingTime;
  std::string   _codecPath;
  std::string   _commonArgs;
  std::string   _encodeArgs;
  std::string   _decodeArgs;

  uint32_t      _secret;
  MediaPathPtr  _lastMediaPtr;

  bool          _isGood;
  bool          _isAndroid;

  int           _runCodec (std::string args,
                           void  *pMsgIn,  size_t  nMsgIn,
                           void **pMsgOut, size_t *nMsgOut,
                           void **pError,  size_t *nError);

  CLICodec (): _mimeType ("") { _secret = 0; _isGood = 1; _isAndroid = 0; _mediaPaths = nullptr; _lastMediaPtr = nullptr; _encodingTime = 0; }
  explicit CLICodec (Json::Value jRoot);

 public:

  virtual ~CLICodec () {}

  static uint32_t  ipv4FromHost       (const std::string &ipStr);
  static uint32_t  makeSecret         (uint32_t ip1, uint32_t ip2);

  static bool      SetCodecsSpec      (const std::string &codecsSpec);
  static std::vector <std::string>
                   GetCodecNames      ();

  static void      SetDirname         (const std::string &dirName);
  static std::string
                   DirFilename        (const std::string &subPath);
  static CLICodec *GetNamedCodec      (std::string codecName);
  static CLICodec *GetCodecFromSpec   (std::string jsonSpec);
  static CLICodec *GetCodecFromStream (std::istream &is);

  virtual
  MediaPathPtr getRandomMedia ();

  size_t       minCapacity ()    {return _mediaPaths->minCapacity ();}
  size_t       maxCapacity ()    {return _mediaPaths->maxCapacity ();}
  double       avgCapacity ()    {return _mediaPaths->avgCapacity ();}
  double       stdDevCapacity () {return _mediaPaths->stdDevCapacity ();}
  std::string  mimeType ()       {return _mimeType;}
  double       encodingTime ()   {return _encodingTime;}

  virtual
  int encode (const void *pMsgIn, size_t nMsgIn, void **pMsgOut, size_t *nMsgOut, MediaPathPtr mediaPtr = nullptr);
  virtual
  int decode (const void *pMsgIn, size_t nMsgIn, void **pMsgOut, size_t *nMsgOut);

  void setSecret (const std::string &host1, const std::string &host2);
  void setSecret (uint32_t ip1, uint32_t ip2);
  void setSecret (uint32_t secret);

  bool isGood () {return _isGood;};
};

#define __CLICODEC_H__
#endif
