#ifndef __CLICODEC_H__

#include <cstdint>
#include <string>
#include <vector>

#include <jsoncpp/json/value.h>


class MediaPath
{
 private:
  std::string _mediaPath;
  size_t      _capacity;

 public:
  MediaPath (std::string path, size_t capacity);

  std::string path ()     {return _mediaPath;};
  size_t      capacity () {return _capacity;};
};

typedef MediaPath *MediaPathPtr;


class MediaPaths
{
 private:
  std::vector<MediaPathPtr> _activeMediaPaths;
  std::vector<MediaPathPtr> _usedMediaPaths;

 protected:
  MediaPaths (const std::string &mediaCapacities, size_t maxCapacity = 0);
  void         cleanUp ();
  friend class CLICodec;

 public:
  unsigned int size () {return _activeMediaPaths.size ();};
  MediaPathPtr getRandom ();

  bool isGood () {return size () /* > 0 */;};
};

typedef MediaPaths *MediaPathsPtr;


class CLICodec
{
 protected:
  MediaPathsPtr _mediaPaths;

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

  CLICodec () { _secret = 0; _isGood = 1; }
  CLICodec (Json::Value jRoot);

 public:

  virtual ~CLICodec () {}

  static uint32_t  ipv4FromHost     (std::string ipStr);
  static uint32_t  ipv4FromHostPersona   (std::string ipStr);
  static uint32_t  makeSecret       (uint32_t ip1, uint32_t ip2);

  static bool      SetCodecsSpec    (std::string codecsSpec);
  static std::vector <std::string>
                   GetCodecNames    ();

  static CLICodec *GetNamedCodec    (std::string codecName);
  static CLICodec *GetCodecFromSpec (std::string jsonSpec);

  virtual
  MediaPathPtr getRandomMedia ();

  virtual
  int encode (void *pMsgIn, size_t nMsgIn, void **pMsgOut, size_t *nMsgOut, MediaPathPtr mediaPtr = nullptr);
  virtual
  int decode (void *pMsgIn, size_t nMsgIn, void **pMsgOut, size_t *nMsgOut);

  void setSecret (std::string host1, std::string host2);
  void setSecret (uint32_t ip1, uint32_t ip2);
  void setSecret (uint32_t secret);

  bool isGood () {return _isGood;};
};

#define __CLICODEC_H__
#endif
