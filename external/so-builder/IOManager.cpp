#include <cstdint>
#include <cstdlib>
#include <cstring>
#include <ctime>
#include <errno.h>
#include <iostream>
#include <new>
#include <sstream>
#include <string>
#include <unordered_map>

#include <arpa/inet.h>
#include <netdb.h>
#include <netinet/in.h>
#include <stdlib.h>     /* lrand48 */

#include "IOManager.h"

extern "C" void diagPrint (char*);

#define _STR_PTR(_str)          const_cast <char *> ((_str).c_str ())

#define _SS_DIAGPRINT(_sExpr) {         \
  std::stringstream _ss;                \
                                        \
  _ss << _sExpr;                        \
                                        \
  diagPrint (_STR_PTR (_ss.str ()));    \
}

#if 01
  #define _DIAGPRINT_
  #define _DIAGPRINT(_str)      diagPrint (_str)
#else
  #define _DIAGPRINT(_str)
#endif


#define UNUSED(x) (void) (x)


typedef union {
  uint64_t u_int_64;
  u_int8_t u_int_8[8];

} _EightByteUnion;


  static uint64_t
message_ident (void *pMsgIn, size_t nMsgIn)
{
  int              size  = sizeof (_EightByteUnion);
  uint8_t         *p     = reinterpret_cast <uint8_t *> (pMsgIn);
  _EightByteUnion  fb    = {0ULL};
  int              b_idx = size - 1;

  for (auto n = nMsgIn; n /* > 0 */; --n) {
    // Replace end with (end ^ input)
    fb.u_int_8[b_idx] = (fb.u_int_8[b_idx] ^ *p) & 0xFF;

    // Rotate bytes left
    b_idx = (b_idx + 1) % size;
    ++p;
  }

  _EightByteUnion ob;

  for (int i = 0; i < size; ++i) {
    ob.u_int_8[i] = fb.u_int_8[b_idx];

    b_idx = (b_idx + 1) % size;
  }

  return ob.u_int_64;
}


#pragma pack(push, 1)
typedef struct _RD_Segment {

  /* 49-byte message segment header */
  uint32_t magic;       /* magic number: 0x624A654C ("bJeL") */
  uint32_t dst;         /* recipient identifier; IPv4 network order */
  uint32_t src;         /* sender identifier; IPv4 network order */
  uint32_t num_segs;    /* number of message segments > 0 */
  uint64_t ident;       /* message identifier/hash; network order */
  uint64_t seg_ident;   /* segment identifier/hash; network order */
  uint32_t epoch_secs;  /* UNIX epoch time */
  uint32_t seg_index;   /* zero-based message segment index < num_segs */
  uint32_t seg_len;     /* segment length; message length = sizeof (struct _RD_Msg_Rec) + segment length */
  uint32_t seg_len2;    /* segment length shadow; used to detect header corruption */

  uint8_t  msg_type;
  uint8_t  msg_fragment[1];     /* message fragment payload */

  void initMembers (uint32_t toIP, uint32_t numSegs,
                    void *pMsgIn, size_t nMsgIn, IOM_msg_type mType)
  {
    _SS_DIAGPRINT ("initMembers (" << toIP << ", " << numSegs << ", "
                   << nMsgIn << ", " << static_cast <int> (mType) << ")");

    dst        = toIP;
    num_segs   = numSegs;
    ident      = message_ident (pMsgIn, nMsgIn); // compute and set message ident
    epoch_secs = static_cast <uint32_t> (time (nullptr) & 0xFFFFFFFFU);
    msg_type   = static_cast <uint8_t>  (mType);
  }

} _RD_Segment, *_RD_Segment_Ptr;
#pragma pack(pop)

#define _RD_SEG_MAGIC  0x624A654CUL
#define _RD_SEG_LEN    static_cast <size_t> (sizeof (_RD_Segment) - 1)


#define _SEG_MBR_CONVERT(_mbr, _func)    _pRDSeg->_mbr = _func (_pRDSeg->_mbr)

static void _print_header (_RD_Segment_Ptr pRDSeg, bool isSend) {
  _SS_DIAGPRINT ((isSend ? "send" : "recv") << " header:"
                 << std::hex
                 << " magic "     << pRDSeg->magic
                 << " dst "       << pRDSeg->dst
                 << " src "       << pRDSeg->src
                 << std::dec
                 << " num_segs "  << pRDSeg->num_segs
                 << " ident "     << pRDSeg->ident
                 << " seg_ident " << pRDSeg->seg_ident
                 << " epoch "     << pRDSeg->epoch_secs
                 << " seg_index " << pRDSeg->seg_index
                 << " seg_len "   << pRDSeg->seg_len
                 << " seg_len2 "  << pRDSeg->seg_len2
                 << " msg_type "  << (pRDSeg->msg_type & 0xFF));
}


  static _RD_Segment_Ptr
toHost (_RD_Segment_Ptr _pRDSeg)
{
  _SEG_MBR_CONVERT (num_segs,   ntohl);
  _SEG_MBR_CONVERT (epoch_secs, ntohl);
  _SEG_MBR_CONVERT (seg_index,  ntohl);
  _SEG_MBR_CONVERT (seg_len,    ntohl);
  _SEG_MBR_CONVERT (seg_len2,   ntohl);

  return _pRDSeg;
}


  static _RD_Segment_Ptr
toWire (_RD_Segment_Ptr _pRDSeg)
{
  _SEG_MBR_CONVERT (num_segs,   htonl);
  _SEG_MBR_CONVERT (epoch_secs, htonl);
  _SEG_MBR_CONVERT (seg_index,  htonl);
  _SEG_MBR_CONVERT (seg_len,    htonl);
  _SEG_MBR_CONVERT (seg_len2,   htonl);

  return _pRDSeg;
}


static _RD_Segment _snd_template;
static _RD_Segment _rcv_template;

static std::unordered_map <std::string, uint32_t> _broadcastHostIPs;    // key: hostname, val: IP address
static std::unordered_map <uint32_t,    uint32_t> _broadcastIPSeeds;    // key: IP address, val: seed


  static int
_Prefilter (uint8_t *pBuffer, size_t nBuffer)
{
  if (nBuffer >= _RD_SEG_LEN) {
    _RD_Segment_Ptr p = reinterpret_cast <_RD_Segment_Ptr> (pBuffer);

    if (p->magic != _rcv_template.magic) {
#if defined (_DIAGPRINT_)
      uint32_t num_segs  = ntohl (p->num_segs);
      uint32_t seg_index = ntohl (p->seg_index);
      uint32_t seg_len   = ntohl (p->seg_len);
      uint32_t seg_len2  = ntohl (p->seg_len2);

      _SS_DIAGPRINT ("invalid magic in prefilter " << std::hex << p->magic << "/" << _rcv_template.magic << std::dec
                     << " " << num_segs
                     << " " << seg_index
                     << " " << seg_len
                     << " " << seg_len2);
#endif
      return IOM_PRFX_MAGIC;
    }

    // Ignore sent broadcast messages

    if (p->src == _snd_template.src)
      return IOM_PRFX_IS_SRC;

    // Check broadcast "listen" address

    if (p->dst != _rcv_template.dst) {
      if (_broadcastIPSeeds.size () /* > 0 */) {
        if (_broadcastIPSeeds.count (p->dst) == 0) {
          _SS_DIAGPRINT ("invalid broadcast dest in prefilter");
          return IOM_PRFX_BRDCST;
        }
      }
      else {
        _SS_DIAGPRINT ("destination mismatch in prefilter");
        return IOM_PRFX_X_DST;
      }
    }

    {
      uint32_t num_segs  = ntohl (p->num_segs);
      uint32_t seg_index = ntohl (p->seg_index);
      uint32_t seg_len   = ntohl (p->seg_len);
      uint32_t seg_len2  = ntohl (p->seg_len2);
      bool     isGood    = seg_len /* > 0 */ && seg_len == seg_len2 && seg_index < num_segs;

      if (!isGood) {
#if defined (_DIAGPRINT_)
        _SS_DIAGPRINT ("corrupted frame in prefilter"
                       " (" << nBuffer << "):"
                       " num_segs/seg_index/seg_len/seg_len2 (" << num_segs << "/" << seg_index << "/" << seg_len << "/" << seg_len2 << ")"
                       " (" << p->src << " " << _rcv_template.src << ")"
                       " (" << p->dst << " " << _rcv_template.dst << ")");
#endif
        return IOM_PREF_X_CHK;
      }
    }

    return 0;
  }

  return IOM_PREF_X_LEN;
}


class _SegPair
{
  _RD_Segment_Ptr  _segment;
  void            *_refcon;

  _SegPair () : _segment (nullptr), _refcon (nullptr) {}
  ~_SegPair () { if (_segment /* != nullptr */) free (_segment); }

  _RD_Segment_Ptr  segment () { return _segment; }
  void            *refcon  () { return _refcon; }

  void set (_RD_Segment_Ptr segment, void *refcon) { _segment = segment; _refcon  = refcon; }

  friend class _MsgTracker;
};

typedef _SegPair *_SegPairPtr;


class _MsgTracker
{
  uint32_t    _fromIP;
  _SegPairPtr _segPairs;
  uint32_t    _num_saw;
  uint32_t    _num_segs;

 public:
  _MsgTracker (uint32_t fromIP, _RD_Segment_Ptr pRDSeg);
  ~_MsgTracker ();
  int track   (_RD_Segment_Ptr pRDSeg, void *refcon, bool fMakeCopy = false);
};


class _MsgWrapper
{
  bool    _padBytes;
  char   *_pPrefixMsg;           // segment header + message + optional pad bytes
  size_t  _nPrefixMsg;
  FILE   *_dfp;

public:
  _MsgWrapper (bool padBytes = false) :
      _padBytes (padBytes),
      _pPrefixMsg (nullptr), _nPrefixMsg (0UL), _dfp (nullptr) {}

  static size_t NumPadBytes (size_t numBytes);

  void   wrap  (_RD_Segment_Ptr pRDSeg, void *pMsg, size_t nMsg, bool fDoClose = false);
  size_t count ();
  int    close (void **pMsg, size_t *nMsg);
};

#define _PAD_BYTES_TO   4

  size_t
_MsgWrapper::NumPadBytes (size_t numBytes)
{
  auto numPadBytes = numBytes % _PAD_BYTES_TO;

  return numPadBytes /* > 0UL */ ? _PAD_BYTES_TO - numPadBytes : numPadBytes;
}

  void
_MsgWrapper::wrap (_RD_Segment_Ptr pRDSeg, void *pMsg, size_t nMsg, bool fDoClose)
{
  char   *pPrefixMsg;           // segment header + message + pad bytes
  size_t  nPrefixMsg;
  size_t  padCount = 0L;

  FILE   *dfp = open_memstream (&pPrefixMsg, &nPrefixMsg);

  pRDSeg->seg_ident = 0ULL;

  (void) fwrite (pRDSeg, _RD_SEG_LEN, 1, dfp);
  (void) fwrite (pMsg, nMsg, 1, dfp);

  if (_padBytes) {
    padCount = NumPadBytes (_RD_SEG_LEN + nMsg);

    auto count = padCount;

    while (count-- /* > 0 */)
      (void) fputc (0, dfp);
  }

  (void) fclose (dfp);

  _RD_Segment_Ptr _pJelPrefix = reinterpret_cast <_RD_Segment_Ptr> (pPrefixMsg);

  _pJelPrefix->seg_ident = message_ident (pPrefixMsg, nPrefixMsg - padCount);
  _print_header (_pJelPrefix, true);

  toWire (_pJelPrefix);

  if (fDoClose) {
    _pPrefixMsg = pPrefixMsg;
    _nPrefixMsg = nPrefixMsg;

    return;
  }
  else {
    if (!_dfp)
      _dfp = open_memstream (&_pPrefixMsg, &_nPrefixMsg);

    (void) fwrite (pPrefixMsg, nPrefixMsg, 1, _dfp);

#if defined (_DIAGPRINT_)
    _SS_DIAGPRINT ("_MsgWrapper::wrap (" << nMsg << ", " << _RD_SEG_LEN << "):"
                   " wrote " << nPrefixMsg << ", ftell (" << ftell (_dfp) << ")");
#endif
  }
}

  int
_MsgWrapper::close (void **pMsg, size_t *nMsg)
{
  if (_dfp /* != nullptr */) {
    (void) fclose (_dfp);
    _dfp = nullptr;
  }

  *pMsg = _pPrefixMsg;
  *nMsg = _nPrefixMsg;

  _pPrefixMsg = nullptr;
  _nPrefixMsg = 0UL;

  return *pMsg /* != nullptr */ ? 0 : 1;
}


class _RDEncoder: public _MsgWrapper
{
  CLICodec     *_pCLICodec;
  MediaPathPtr  _mediaPtr;
  void         *_pMsg;
  size_t        _nMsg;

 public:
  _RDEncoder  (CLICodec *pCLICodec, MediaPathPtr mediaPtr, void *pMsg, size_t nMsg) :
      _MsgWrapper (), _pCLICodec (pCLICodec), _mediaPtr (mediaPtr), _pMsg (pMsg), _nMsg (nMsg) {}

  MediaPathPtr getMedia () { return _mediaPtr; }
  void         setMedia (MediaPathPtr mediaPtr) { _mediaPtr = mediaPtr; }
  size_t       msgLen   () { return _nMsg; }
  int          encode   (_RD_Segment_Ptr pRDSeg, void **pMsg, size_t *nMsg);
};

  int
_RDEncoder::encode (_RD_Segment_Ptr pRDSeg, void **pEncMsg, size_t *nEncMsg)
{
  // Prefix the message segment with the segment header

  void   *pPrefixMsg;
  size_t  nPrefixMsg;

  (void) wrap (pRDSeg, _pMsg, _nMsg, true);
  (void) close (&pPrefixMsg, &nPrefixMsg);

  int status = _pCLICodec->encode (pPrefixMsg, nPrefixMsg, pEncMsg, nEncMsg, _mediaPtr);
  //  _SS_DIAGPRINT ("_RDEncoder::encode (" << nPrefixMsg << ", " << *nEncMsg << ") with _pCLICodec @" << _pCLICodec << " -> " << status);

  free (pPrefixMsg);

  return status;
}


typedef std::unordered_map<uint64_t, _MsgTracker *>   MsgTrackerMap;

typedef std::unordered_map<uint32_t, MsgTrackerMap *> IPMessageTrackerMap;

typedef std::unordered_map<uint32_t, CLICodec *>     IPCodecMap;        // key: IPv4 address
typedef std::unordered_map<uint32_t, IPCodecMap *>   CIPCodecMap;       // key: IOM_msg_type channel

typedef std::unordered_map<IOM_msg_type, SendMsgCB>  SendMsgCBMap;
typedef std::unordered_map<IOM_msg_type, SendMsgFn>  SendMsgFnMap;

typedef std::unordered_map<IOM_msg_type, RecvMsgCB>  RecvMsgCBMap;
typedef std::unordered_map<IOM_msg_type, RecvMsgFn>  RecvMsgFnMap;

typedef std::vector <IOM_msg_type>                   IOMTypeList;


// (cType, (fromIP, CLICodec *))
static CIPCodecMap  _fromCodecs;

// (fromIP, (message_id, _MsgTracker))
static IPMessageTrackerMap _ipMsgTrackers;

// (cType, (toIP, CLICodec *))
static CIPCodecMap  _toCodecs;

// (IOM_msg_type, SendMsg{CB,Fn})
static SendMsgCBMap _sendCallbacks;
static SendMsgFnMap _sendFunctions;

// (IOM_msg_type, RecvMsg{CB,Fn})
static RecvMsgCBMap _recvCallbacks;
static RecvMsgFnMap _recvFunctions;

static IOMTypeList  _channelOrder;


  static SendMsgCB
_GetSendMsgCB (IOM_msg_type cType)
{
  if (_sendCallbacks.count (cType) /* > 0 */)
    return _sendCallbacks[cType];
  else
    return nullptr;
}

  static SendMsgFn
_GetSendMsgFn (IOM_msg_type cType)
{
  if (_sendFunctions.count (cType) /* > 0 */)
    return _sendFunctions[cType];
  else
    return nullptr;
}

  static RecvMsgCB
_GetRecvMsgCB (IOM_msg_type cType)
{
  if (_recvCallbacks.count (cType) /* > 0 */)
    return _recvCallbacks[cType];
  else
    return nullptr;
}

  static RecvMsgFn
_GetRecvMsgFn (IOM_msg_type cType)
{
  if (_recvFunctions.count (cType) /* > 0 */)
    return _recvFunctions[cType];
  else
    return nullptr;
}


// https://www.techiedelight.com/remove-entries-map-iterating-cpp/

  static void
_ClearCodecMap (CIPCodecMap &cMap)
{
    auto itOut = cMap.begin ();

    while (itOut != cMap.cend ()) {
        auto cMapIn = itOut->second;
        auto itIn   = cMapIn->begin ();

        while (itIn != cMapIn->cend ()) {
            delete itIn->second;
            itIn = cMapIn->erase (itIn);
        }

        delete itOut->second;
        itOut = cMap.erase (itOut);
    }
}


MessageWrapper::MessageWrapper ()
{
  _pMsgWrapperPriv = new _MsgWrapper (true);
}

MessageWrapper::~MessageWrapper ()
{
  _MsgWrapper *_pMsgWrapper = static_cast <_MsgWrapper *> (_pMsgWrapperPriv);

  delete _pMsgWrapper;
}

  size_t
MessageWrapper::WrappedSize (size_t nData)
{
  size_t nWrap = nData + _RD_SEG_LEN;

  return nWrap + _MsgWrapper::NumPadBytes (nWrap);
}

  void
MessageWrapper::wrap (void *pMsg, size_t nMsg, IOM_msg_type cType, std::string toHost)
{
  wrap (pMsg, nMsg, cType, CLICodec::ipv4FromHost (toHost));
}

  void
MessageWrapper::wrap (void *pMsg, size_t nMsg, IOM_msg_type mType, uint32_t toIP)
{
  _RD_Segment rdSegment = _snd_template;

  rdSegment.initMembers (toIP, 1, pMsg, nMsg, mType);
  rdSegment.seg_len  = nMsg;
  rdSegment.seg_len2 = nMsg;

  _MsgWrapper *_pMsgWrapper = static_cast <_MsgWrapper *> (_pMsgWrapperPriv);

  (void) _pMsgWrapper->wrap (&rdSegment, pMsg, nMsg, false);
}

  int
MessageWrapper::close (void **pData, size_t *nData)
{
  _MsgWrapper *_pMsgWrapper = static_cast <_MsgWrapper *> (_pMsgWrapperPriv);

  return _pMsgWrapper->close (pData, nData);
}


uint32_t    IOManager::_hostIP   = 0;
uint32_t    IOManager::_duration = 0;

  int
IOManager::SetHostIP (std::string hostname)
{
  return SetHostIP (CLICodec::ipv4FromHost (hostname));
}

  int
IOManager::SetHostIP (uint32_t hostIP)
{
  _hostIP             = hostIP;
  (void) memset (&_snd_template, 0, _RD_SEG_LEN);
  _snd_template.magic = htonl (_RD_SEG_MAGIC);
  _rcv_template       = _snd_template;

  _snd_template.src   = _hostIP;
  _rcv_template.dst   = _hostIP;

  return _hostIP /* != 0UL */ ? 0 : -1;
}

  uint32_t
IOManager::SetBroadcastHost (std::string broadcastHost, uint32_t broadcastSeed)
{
  uint32_t _broadcastIP;

  if (_broadcastHostIPs.count (broadcastHost) /* > 0 */)
    _broadcastIP = _broadcastHostIPs[broadcastHost];
  else {
    _broadcastIP = CLICodec::ipv4FromHost (broadcastHost);
    _broadcastHostIPs[broadcastHost] = _broadcastIP;
  }

  return SetBroadcastIP (_broadcastIP, broadcastSeed);
}

  uint32_t
IOManager::SetBroadcastIP (uint32_t broadcastIP, uint32_t broadcastSeed)
{
  uint32_t seed = broadcastSeed /* > 0 */ ? broadcastSeed : broadcastIP;

  _broadcastIPSeeds[broadcastIP] = seed;

  return seed;
}

  std::vector <std::string>
IOManager::GetBroadcastIPs ()
{
  std::vector<std::string> _keys;

  for (std::unordered_map<std::string, uint32_t>::iterator it = _broadcastHostIPs.begin ();
       it != _broadcastHostIPs.end ();
       ++it)
    _keys.push_back (it->first);

  return _keys;
}

  void
IOManager::SetProcessMsg (RecvMsgCB processMsg, IOM_msg_type cType)
{
  _SS_DIAGPRINT ("::SetProcessMsg CB " << static_cast <void*> (&processMsg) << " CType " << static_cast <int> (cType));
  _recvCallbacks[cType] = processMsg;
}

  void
IOManager::SetProcessMsg (RecvMsgFn processMsg, IOM_msg_type cType)
{
  _SS_DIAGPRINT ("::SetProcessMsg Func " << static_cast <void*> (&processMsg) << " CType " << static_cast <int> (cType));
  _recvFunctions[cType] = processMsg;
}

  void
IOManager::SetSendMsg (SendMsgCB sendMsg, IOM_msg_type cType)
{
  _sendCallbacks[cType] = sendMsg;
}

  void
IOManager::SetSendMsg (SendMsgFn sendMsg, IOM_msg_type cType)
{
  _sendFunctions[cType] = sendMsg;
}


#undef _FREE

#if defined (_DIAGPRINT_)

#define _FREE(_p)       {                       \
  _SS_DIAGPRINT ("free (" << _p << ") at " <<   \
                 __FILE__ << ", "               \
                 "line " << __LINE__ << ".");   \
  free (_p);                                    \
}

#else

#define _FREE(_p)       free (_p)

#endif


  int
IOManager::ProcessSegments (void *pMsgOut, size_t nMsgOut, uint32_t fromIP, void *refcon)
{
  void *_pMsgOut = pMsgOut;     // original argument value
  bool  fDidInit = false;
  bool  fMakeCopy;
  int   retVal   = IOM_PARTIAL_MSG;

  while (nMsgOut /* > 0UL */) {
    _RD_Segment_Ptr pRDSeg = static_cast <_RD_Segment_Ptr> (pMsgOut);
    size_t          lRDSeg;

    // Validate segment magic number, etc.

    auto _pStatus = _Prefilter (static_cast <uint8_t *> (pMsgOut), nMsgOut);

    if (_pStatus /* != 0 */) {
      _SS_DIAGPRINT ("::ProcessSegments (nMsgOut = " << nMsgOut << "): failed _Prefilter (): " << _pStatus);
      return IOM_NOT_SEGMENT;
    }

    (void) toHost (pRDSeg);      // wire-to-host

    _print_header (pRDSeg, false);

    lRDSeg = pRDSeg->seg_len + _RD_SEG_LEN;

    // Validate segment

    if (lRDSeg > nMsgOut) {
      _FREE (_pMsgOut);

#if defined (_DIAGPRINT_)
      _SS_DIAGPRINT ("::ProcessSegments (): lRDSeg > nMsgOut (" << lRDSeg << " > " << nMsgOut << ")");
#endif

      return IOM_NOT_SEGMENT;
    }

    if (!fDidInit) {
      fDidInit  = true;
      fMakeCopy = lRDSeg < nMsgOut;

#if defined (_DIAGPRINT_)
      _SS_DIAGPRINT ("::ProcessSegments (): lRDSeg < nMsgOut (" << lRDSeg << " < " << nMsgOut << ")");
#endif
    }

    if (_duration > 0) {
      uint32_t currTime = static_cast <uint32_t> (time (nullptr) & 0xFFFFFFFFU);

      if (pRDSeg->epoch_secs + _duration < currTime) {
        _FREE (_pMsgOut);

        _SS_DIAGPRINT ("::ProcessSegments (): expired segment");

        return IOM_EXPIRED_SEG;
      }
    }

    uint64_t _ident = pRDSeg->ident ^ pRDSeg->epoch_secs;

    if (pRDSeg->seg_len == pRDSeg->seg_len2) {
      uint32_t _msg_len   = pRDSeg->seg_len + sizeof (_RD_Segment) - 1;
      uint64_t _seg_ident = pRDSeg->seg_ident;

      pRDSeg->seg_ident = 0ULL;

      if (message_ident (pRDSeg, _msg_len) != _seg_ident) {
        _SS_DIAGPRINT ("Corrupted RDestini payload " << message_ident (pRDSeg, _msg_len) << " " <<  _msg_len);
      }
      else {
        uint8_t *pPayload = (static_cast <_RD_Segment_Ptr> (pMsgOut))->msg_fragment;

        if (pRDSeg->num_segs == 1 && _Prefilter (pPayload, pRDSeg->seg_len) == 0)
          return ProcessSegments (pPayload, pRDSeg->seg_len, fromIP, refcon);
      }

      pRDSeg->seg_ident = _seg_ident;
    }
    else
      _SS_DIAGPRINT ("Corrupted RDestini payload2");

    MsgTrackerMap *_msgTrackers;
    _MsgTracker   *pMsgTracker;

    if (_ipMsgTrackers.count (fromIP) /* > 0 */)
      _msgTrackers = _ipMsgTrackers[fromIP];
    else {
      _msgTrackers           = new MsgTrackerMap ();
      _ipMsgTrackers[fromIP] = _msgTrackers;

      _SS_DIAGPRINT ("new IP message tracker for " << fromIP);
    }

    if (_msgTrackers->count (_ident) /* > 0 */)
      pMsgTracker = (*_msgTrackers)[_ident];
    else {
      pMsgTracker             = new _MsgTracker (fromIP, pRDSeg);
      (*_msgTrackers)[_ident] = pMsgTracker;

      _SS_DIAGPRINT ("new ident message tracker for " << _ident);
    }

    retVal = pMsgTracker->track (pRDSeg, refcon, fMakeCopy);

    // Complete message; remove _MsgTracker

    if (retVal == IOM_WHOLE_MSG) {
      delete pMsgTracker;
      _msgTrackers->erase (_ident);
    }

    // Decrement byte count and increment segment buffer pointer

    nMsgOut -= lRDSeg;
    pMsgOut  = static_cast <char *> (pMsgOut) + lRDSeg;

    // Accommodate pad bytes

    if (fMakeCopy && nMsgOut /* > 0UL */) {
      size_t nPadBytes = _MsgWrapper::NumPadBytes (lRDSeg);

      nMsgOut -= nPadBytes;
      pMsgOut  = static_cast <char *> (pMsgOut) + nPadBytes;
    }

#if defined (_DIAGPRINT_)
    _SS_DIAGPRINT ("::ProcessSegments (): nMsgOut = " << nMsgOut);
#endif
  }

#if defined (_DIAGPRINT_)
  _SS_DIAGPRINT ("::ProcessSegments (): retVal = " << retVal);
#endif

  return retVal;
}

  void
IOManager::AddChannel (IOM_msg_type cType)
{
  _channelOrder.push_back (cType);
}


  static void
_MakeCodec (uint32_t hostIP, uint32_t secret, IOM_msg_type cType, std::string _codec, CIPCodecMap &_ccodecs)
{
  IPCodecMap *_codecs;

  if (_ccodecs.count (cType) /* > 0 */)
    _codecs = _ccodecs[cType];
  else {
    _codecs = new IPCodecMap ();
    _ccodecs[cType] = _codecs;
  }

  if (_codecs->count (hostIP) == 0) {
    auto pCodec = CLICodec::GetNamedCodec (_codec);

    if (pCodec /* != nullptr */) {
      _SS_DIAGPRINT ("_MakeCodec (" << hostIP << ", " << secret << ", " <<
                     static_cast <int> (cType) << ", " << _codec <<
                     ") New: " << pCodec << ")");
      pCodec->setSecret (secret);
      (*_codecs)[hostIP] = pCodec;
    }
  }
}

  void
IOManager::MakeCodecs (std::string hostname, IOM_msg_type cType, std::string codec)
{
  MakeCodecs (CLICodec::ipv4FromHost (hostname), cType, codec);
}

  void
IOManager::MakeCodecs (uint32_t hostIP, IOM_msg_type cType, std::string codec)
{
#if defined (__SRC_DST_SEED__)
  _MakeCodec (hostIP, CLICodec::makeSecret ( hostIP, _hostIP), cType, codec, _fromCodecs);
  _MakeCodec (hostIP, CLICodec::makeSecret (_hostIP,  hostIP), cType, codec, _toCodecs);
#else
  _MakeCodec (hostIP, _hostIP, cType, codec, _fromCodecs);
  _MakeCodec (hostIP,  hostIP, cType, codec, _toCodecs);
#endif
}

  void
IOManager::MakeCodecs (std::string hostname, uint32_t seed, IOM_msg_type cType, std::string codec)
{
  MakeCodecs (CLICodec::ipv4FromHost (hostname), seed, cType, codec);
}

  void
IOManager::MakeCodecs (uint32_t hostIP, uint32_t seed, IOM_msg_type cType, std::string codec)
{
  SetBroadcastIP (hostIP, seed);

  uint32_t secret = CLICodec::makeSecret (hostIP, seed);

  _MakeCodec (hostIP, secret, cType, codec, _fromCodecs);
  _MakeCodec (hostIP, secret, cType, codec, _toCodecs);
}

  static CLICodec *
_GetCodec (uint32_t hostIP, IOM_msg_type &cType, CIPCodecMap &_ccodecs)
{
  if (cType == IOM_CT_ORDERED) {
    for (unsigned int i = 0; i < _channelOrder.size (); i++) {
      auto _pCodec = _GetCodec (hostIP, _channelOrder[i], _ccodecs);
      if (_pCodec /* != nullptr */) {
        cType = _channelOrder[i];
        return _pCodec;
      }
    }

    return nullptr;
  }
  else {
    _SS_DIAGPRINT ("_GetCodec (" << hostIP << ", " << static_cast <int> (cType) <<
                   ") has cType = " << _ccodecs.count (cType));

    if (_ccodecs.count (cType) /* > 0 */) {
      auto _codecs = _ccodecs[cType];

      _SS_DIAGPRINT ("_GetCodec () has hostIP = " <<  hostIP << " " << _codecs->count (hostIP));
      return _codecs->count (hostIP) /* > 0 */ ? (*_codecs)[hostIP] : nullptr;
    }
    else
      return nullptr;
  }
}

  CLICodec *
IOManager::GetFromCodec (std::string hostname, IOM_msg_type &cType)
{
  return GetFromCodec (CLICodec::ipv4FromHost (hostname), cType);
}

  CLICodec *
IOManager::GetFromCodec (uint32_t hostIP, IOM_msg_type &cType)
{
  return _GetCodec (hostIP, cType, _fromCodecs);
}

  CLICodec *
IOManager::GetToCodec (std::string hostname, IOM_msg_type &cType)
{
  return GetToCodec (CLICodec::ipv4FromHost (hostname), cType);
}

  CLICodec *
IOManager::GetToCodec (uint32_t hostIP, IOM_msg_type &cType)
{
  return _GetCodec (hostIP, cType, _toCodecs);
}


  int
IOManager::Examine (void *pMsgIn, size_t nMsgIn, IOM_msg_type cType, uint32_t fromIP, void *refcon)
{
  _RD_Segment_Ptr  pRDSeg  = nullptr;
  void            *pMsgOut = nullptr;
  size_t           nMsgOut;

  if (cType == IOM_CT_ORDERED) {
    for (unsigned int i = 0; i < _channelOrder.size (); i++) {
      auto _cType = _channelOrder[i];
      auto retVal = Examine (pMsgIn, nMsgIn, _cType, fromIP, refcon);
      
      if (retVal >= 0)
        return retVal;
    }

    return IOM_NOT_SEGMENT;
  }

  if (fromIP) {
    CLICodec *pCodec = GetFromCodec (fromIP, cType);

    if (pCodec /* != nullptr */) {
      if (pCodec->decode (pMsgIn, nMsgIn, &pMsgOut, &nMsgOut) == 0 &&
          nMsgOut >= sizeof (_RD_Segment))
        pRDSeg = static_cast <_RD_Segment_Ptr> (pMsgOut);
      else if (pMsgOut /* != nullptr */) {
        _FREE (pMsgOut);
        pRDSeg = nullptr;
      }
    }
  }
  else {
    if (_fromCodecs.count (cType) /* != 0 */) {
      auto _codecs = _fromCodecs[cType];
      bool doBreak = false;

      for (const auto& any : *_codecs) {
        auto extHost = any.first;
        auto pCodec  = any.second;

        _rcv_template.src = extHost;

        pMsgOut           = nullptr;

        if (pCodec->decode (static_cast <char *> (pMsgIn), nMsgIn, &pMsgOut, &nMsgOut) == 0 &&
            nMsgOut >= sizeof (_RD_Segment)) {
          pRDSeg  = static_cast <_RD_Segment_Ptr> (pMsgOut);
          fromIP  = pRDSeg->src;
          doBreak = true;
        }
        else if (pMsgOut /* != nullptr */) {
          _FREE (pMsgOut);
          pRDSeg  = nullptr;
        }

        if (doBreak)
          break;
      }
    }
  }

  if (pRDSeg /* != nullptr */)
    return ProcessSegments (pMsgOut, nMsgOut, fromIP, refcon);

  else {
    _SS_DIAGPRINT ("Image not a RDestini segment");
    return IOM_NOT_SEGMENT;
  }
}


  int
IOManager::Send (void *pMsgIn, size_t nMsgIn, std::string hostname,
                 IOM_msg_type cType, void *refcon, IOM_msg_type mType,
                 MediaPathPtr pInMediaPath)
{
  return Send (pMsgIn, nMsgIn, CLICodec::ipv4FromHost (hostname), cType, refcon, mType, pInMediaPath);
}


  int
IOManager::Send (void *pMsgIn, size_t nMsgIn, uint32_t toIP,
                 IOM_msg_type cType, void *refcon, IOM_msg_type mType,
                 MediaPathPtr pInMediaPath)
{
  SendMsgCB _sendCallback = _GetSendMsgCB (cType);
  SendMsgFn _sendFunction = _GetSendMsgFn (cType);

  if (_sendCallback == nullptr && _sendFunction == nullptr)
    return IOM_NO_SENDER;

  _SS_DIAGPRINT ("Entering IOManager::Send (" << toIP << ")");

  std::vector<_RDEncoder *> rdEncoders;

  if (nMsgIn /* > 0 */) {

    // Create a list of images that can contain the message segments

    CLICodec *pCLICodec = GetToCodec (toIP, cType);

    if (pCLICodec == nullptr) {
      _SS_DIAGPRINT ("IOManager::Send (" << toIP << ") No media codec");
      return IOM_NO_CODEC;
    }

    char *pMsg = static_cast <char *> (pMsgIn);

    for (auto n = nMsgIn; n > 0;) {
      MediaPathPtr pMediaPath;

      _SS_DIAGPRINT ("IOM before check pInMediaPath");

      if (pInMediaPath /* != nullptr */)
        pMediaPath = pInMediaPath;
      else {
        pMediaPath = pCLICodec->getRandomMedia ();
        _SS_DIAGPRINT ("IOM after getRandomMedia ()");

        if (pMediaPath /* != nullptr */)
          _SS_DIAGPRINT ("IOManager::Send () selected random image \"" << pMediaPath->path () << "\"");
      }

      size_t imgCap = pMediaPath ? pMediaPath->capacity () - _RD_SEG_LEN : n + 1;

      if (imgCap > 0) {
        bool n_gt_cap = n > imgCap;

        rdEncoders.push_back (new _RDEncoder (pCLICodec, pMediaPath, pMsg, n_gt_cap ? imgCap : n));

        if (n_gt_cap) {
          pMsg += imgCap;
          n    -= imgCap;
        }
        else
          break;
      }
    }

    // Encode and publish

    int             status    = 0;
    int             errVal    = 0;
    unsigned int    numSegs   = rdEncoders.size ();
    _RD_Segment     rdSegment = _snd_template;
    _RD_Segment_Ptr pRDSeg    = &rdSegment;

    pRDSeg->initMembers (toIP, numSegs, pMsgIn, nMsgIn, mType != IOM_MT_CT_COPY ? mType : cType);

    for (unsigned int i = 0; i < numSegs; ++i) {
      _RDEncoder   *pRDEncoder  = rdEncoders.at (i);
      MediaPathPtr  _pMediaPath = pRDEncoder->getMedia ();
      void         *pMsgOut;
      size_t        nMsgOut;

      pRDSeg->seg_index = i;
      pRDSeg->seg_len   = pRDEncoder->msgLen ();
      pRDSeg->seg_len2  = pRDSeg->seg_len;

      while (true) {
        pMsgOut = nullptr;
        status  = pRDEncoder->encode (pRDSeg, &pMsgOut, &nMsgOut);

	if (status && status != EAGAIN)
	  _SS_DIAGPRINT ("pRDEncoder->encode (" << nMsgIn << "): " << status);

        if (status) {
          MediaPathPtr pMediaPath = pCLICodec->getRandomMedia ();

          if (pMediaPath != _pMediaPath) {
            if (pMsgOut /* != nullptr */)
              _FREE (pMsgOut);

            pRDEncoder->setMedia (pMediaPath);
            continue;
          }
        }

        break;
      }

      //      _SS_DIAGPRINT ("pRDEncoder->encode (" << nMsgIn << "): " << status);

      delete pRDEncoder;

      if (status == 0) {
        if (_sendCallback /* != nullptr */)
          status = _sendCallback (toIP, refcon, reinterpret_cast <uint8_t *> (pMsgOut), nMsgOut, cType);
        else
          status = _sendFunction (toIP, refcon, reinterpret_cast <uint8_t *> (pMsgOut), nMsgOut, cType);

        if (status < 0)
          errVal = status;

        _FREE (pMsgOut);
      }
      else
        errVal = -status;
    }

    return errVal /* != 0 */ ? errVal : status;
  }

  return -1;
}


  int
IOManager::Broadcast (void *pMsgIn, size_t nMsgIn, std::string broadcastHost,
                      IOM_msg_type cType, void *refcon, IOM_msg_type mType,
                      MediaPathPtr pInMediaPath)
{
  return Broadcast (pMsgIn, nMsgIn, CLICodec::ipv4FromHost (broadcastHost), cType, refcon, mType, pInMediaPath);
}

  int
IOManager::Broadcast (void *pMsgIn, size_t nMsgIn, uint32_t broadcastIP,
                      IOM_msg_type cType, void *refcon, IOM_msg_type mType,
                      MediaPathPtr pInMediaPath)
{
  int count = 0;

  if (_broadcastIPSeeds.count (broadcastIP) /* > 0 */) {
    int status = Send (pMsgIn, nMsgIn, broadcastIP,
                       cType, refcon, mType, pInMediaPath);

    if (status < 0)
      count = status;
    else if (count >= 0)
      ++count;
  }

  return count;
}


  void
IOManager::CleanUp ()
{
  auto it = _ipMsgTrackers.begin ();

  while (it != _ipMsgTrackers.cend ()) {
    delete it->second;
    it = _ipMsgTrackers.erase (it);
  }

  _ClearCodecMap (_fromCodecs);
  _ClearCodecMap (_toCodecs);
}


_MsgTracker::_MsgTracker (uint32_t fromIP, _RD_Segment_Ptr pRDSeg)
{
  _fromIP   = fromIP;
  _segPairs = new (std::nothrow) _SegPair[pRDSeg->num_segs];
  _num_segs = _segPairs /* != nullptr */ ? pRDSeg->num_segs : 0;
  _num_saw  = 0;
}


_MsgTracker::~_MsgTracker ()
{
  if (_segPairs /* != nullptr */) {
    delete [] _segPairs;
    _segPairs = nullptr;
  }
}

  int
_MsgTracker::track (_RD_Segment_Ptr pRDSeg, void *refcon, bool fMakeCopy)
{
  _SS_DIAGPRINT ("In MsgTracker::track");

  if (_segPairs == nullptr)
   return IOM_OUT_OF_MEM;

  if (pRDSeg->num_segs != _num_segs)
    return IOM_BAD_NUM_SEG;    // mismatched number of segments

  uint32_t seg_index = pRDSeg->seg_index;

  if (seg_index >= _num_segs)
    return IOM_BAD_SEG_IDX;    // bad segment index

  _SegPairPtr segPair = _segPairs + seg_index;

  if (segPair->segment () /* != nullptr */)
    return IOM_DUP_SEGMENT;    // duplicate fragment

  // For packed messages, copy the segment

  if (fMakeCopy) {
    size_t          _lRDSeg = pRDSeg->seg_len + _RD_SEG_LEN;
    _RD_Segment_Ptr _pRDSeg = static_cast <_RD_Segment_Ptr> (calloc (1, _lRDSeg));

    if (_pRDSeg == nullptr)
      return IOM_OUT_OF_MEM;

    pRDSeg = static_cast <_RD_Segment_Ptr> (memcpy (_pRDSeg, pRDSeg, _lRDSeg));
  }

  segPair->set (pRDSeg, refcon);

  _SS_DIAGPRINT ("Tracker Debug " << seg_index << "/" << _num_segs << ": " << pRDSeg->seg_len);

  if (++_num_saw == _num_segs) {
    IOM_msg_type mType      = static_cast <IOM_msg_type> (pRDSeg->msg_type);
    RecvMsgCB    _recvMsgCB = _GetRecvMsgCB (mType);
    RecvMsgFn    _recvMsgFn = _GetRecvMsgFn (mType);

    _SS_DIAGPRINT ("Tracker looking for _recvMsg (" << static_cast <int> (mType) << ")");

    if (_recvMsgCB /* != nullptr */ || _recvMsgFn /* != nullptr */) {
      char   *pMsgIn;
      size_t  nMsgIn;
      FILE   *dfp = open_memstream (&pMsgIn, &nMsgIn);

      for (uint32_t i = 0; i < _num_segs; i++) {
        segPair = _segPairs + i;

        _RD_Segment_Ptr pSeg = segPair->segment ();

        (void) fwrite (pSeg->msg_fragment, pSeg->seg_len, 1, dfp);
      }

      (void) fclose (dfp);

      _SS_DIAGPRINT ("before ::ProcessSegments (): " << nMsgIn);

      // Preferentially track broadcast address

      uint32_t _ip = _broadcastIPSeeds.count (pRDSeg->dst) /* > 0 */ ? pRDSeg->dst : _fromIP;

      if (IOManager::ProcessSegments (pMsgIn, nMsgIn, _ip, refcon) == IOM_NOT_SEGMENT) {
        _SS_DIAGPRINT ("::Track " << static_cast<void*> (&_recvMsgCB) << " " << static_cast <void*> (&_recvMsgFn) << " MType " << static_cast <int> (mType));
        if (_recvMsgCB /* != nullptr */)
          _recvMsgCB (_ip, refcon, reinterpret_cast <uint8_t *> (pMsgIn), nMsgIn);
        else
          _recvMsgFn (_ip, refcon, reinterpret_cast <uint8_t *> (pMsgIn), nMsgIn);

        free (pMsgIn);
      }
    }
    else {
      _SS_DIAGPRINT ("Tracker no _recvMsg (" << static_cast <int> (mType) << ")!");
    }

    return IOM_WHOLE_MSG;      // message complete; release _MsgTracker
  }
  else
    _SS_DIAGPRINT ("Tracker: " << _num_saw << " " << _num_segs);

  return IOM_PARTIAL_MSG;
}
