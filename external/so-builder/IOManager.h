/*
 * IOManager header.  Defines IOManager API.
 */

#ifndef __IOMANAGER_H__

#include <cstdint>
#include <cstdio>
#include <functional>
#include <vector>

#include "CLICodec.h"

enum {
  IOM_WHOLE_MSG   =  1,
  IOM_PARTIAL_MSG =  0,
  IOM_OUT_OF_MEM  = -1,
  IOM_NOT_SEGMENT = -2,
  IOM_DUP_SEGMENT = -3,
  IOM_BAD_SEG_IDX = -4,
  IOM_BAD_NUM_SEG = -5,
  IOM_EXPIRED_SEG = -6,
  IOM_NO_SENDER   = -7,
  IOM_NO_CODEC    = -8,
  IOM_PRFX_MAGIC  = -9,
  IOM_PRFX_IS_SRC = -10,
  IOM_PRFX_BRDCST = -11,
  IOM_PRFX_X_DST  = -12,
  IOM_PREF_X_CHK  = -13,
  IOM_PREF_X_LEN  = -14,
};

typedef enum IOM_msg_type
{
  IOM_CT_ORDERED = -1,
  IOM_CT_GENERAL,
  IOM_CT_AVIDEO,
  IOM_CT_D_SVR,

  IOM_MT_CT_COPY = -1,
  IOM_MT_GENERAL = IOM_CT_GENERAL,
  IOM_MT_AVIDEO  = IOM_CT_AVIDEO,
  IOM_MT_D_SVR   = IOM_CT_D_SVR
} IOM_msg_type;


class MessageWrapper
{
  void *_pMsgWrapperPriv;       // has-a (cf. is-a, which requires advertising _MessageWrapper)

 public:
  MessageWrapper  ();
  ~MessageWrapper ();

  static size_t WrappedSize (size_t nData);

  void   wrap  (void  *pMsg,  size_t  nMsg, IOM_msg_type cType, std::string toHost);
  void   wrap  (void  *pMsg,  size_t  nMsg, IOM_msg_type cType, uint32_t    toIP);
#if defined (SWIG)
  int    close (void **pData = nullptr, size_t *nData = nullptr);
#else
  int    close (void **pData, size_t *nData);
#endif
};


typedef void (*RecvMsgCB) (uint32_t srcIP, void *refcon, uint8_t *, size_t);
typedef int  (*SendMsgCB) (uint32_t dstIP, void *refcon, uint8_t *, size_t, IOM_msg_type);

typedef std::function <void (uint32_t, void *, uint8_t *, size_t)>               RecvMsgFn;
typedef std::function <int  (uint32_t, void *, uint8_t *, size_t, IOM_msg_type)> SendMsgFn;

class IOManager
{
  static uint32_t    _hostIP;
  static uint32_t    _duration;    // discard segment when epoch_secs + _duration < current time iff _duration > 0

  static int       ProcessSegments    (void *pMsgOut, size_t nMsgOut, uint32_t fromIP, void *refcon);

  friend class _MsgTracker;

 public:

  static void      AddChannel    (IOM_msg_type cType);

  static void      MakeCodecs    (std::string hostname,                IOM_msg_type cType, std::string codec);
  static void      MakeCodecs    (uint32_t    hostIP,                  IOM_msg_type cType, std::string codec);
  static void      MakeCodecs    (std::string hostname, uint32_t seed, IOM_msg_type cType, std::string codec);
  static void      MakeCodecs    (uint32_t    hostIP,   uint32_t seed, IOM_msg_type cType, std::string codec);

  static CLICodec *GetFromCodec  (std::string fromHost, IOM_msg_type &cType);
  static CLICodec *GetFromCodec  (uint32_t    fromIP,   IOM_msg_type &cType);

  static CLICodec *GetToCodec    (std::string toHost,   IOM_msg_type &cType);
  static CLICodec *GetToCodec    (uint32_t    toIP,     IOM_msg_type &cType);

                                // Sets current host IP address
  static int  SetHostIP         (std::string hostname);
  static int  SetHostIP         (uint32_t hostIP = 0UL);

                                // Examine () callback function
  static void SetProcessMsg     (RecvMsgCB processMsg, IOM_msg_type mType = IOM_MT_GENERAL);
  static void SetProcessMsg     (RecvMsgFn processMsg, IOM_msg_type mType = IOM_MT_GENERAL);
                                // Send () callback function
  static void SetSendMsg        (SendMsgCB sendMsg,    IOM_msg_type cType = IOM_CT_ORDERED);
  static void SetSendMsg        (SendMsgFn sendMsg,    IOM_msg_type cType = IOM_CT_ORDERED);

  static uint32_t  SetBroadcastHost (std::string broadcastHost, uint32_t broadcastSeed = 0);
  static uint32_t  SetBroadcastIP   (uint32_t    broadcastIP,   uint32_t broadcastSeed = 0);

  static std::vector <std::string> GetBroadcastIPs ();

  // Process incoming or send outgoing messages

  static int  Examine   (void *pMsgIn,  size_t nMsgIn, IOM_msg_type cType, uint32_t fromIP, void *refcon);

  static int  Send      (void *message, size_t message_length, std::string hostname,
                         IOM_msg_type cType,
                         void *refcon = nullptr,
                         IOM_msg_type mType = IOM_MT_CT_COPY,
                         MediaPathPtr pInMediaPath = nullptr);
  static int  Send      (void *message, size_t message_length, uint32_t toIP,
                         IOM_msg_type cType,
                         void *refcon = nullptr,
                         IOM_msg_type mType = IOM_MT_CT_COPY,
                         MediaPathPtr pInMediaPath = nullptr);
  static int  Broadcast (void *message, size_t message_length, std::string broadcastHost,
                         IOM_msg_type cType,
                         void *refcon = nullptr,
                         IOM_msg_type mType = IOM_MT_CT_COPY,
                         MediaPathPtr pInMediaPath = nullptr);
  static int  Broadcast (void *message, size_t message_length, uint32_t broadcastIP,
                         IOM_msg_type cType,
                         void *refcon = nullptr,
                         IOM_msg_type mType = IOM_MT_CT_COPY,
                         MediaPathPtr pInMediaPath = nullptr);

  // Optional configuration

  // discard segment when epoch_secs + _duration < current time iff _duration > 0
  static void SetDuration (uint32_t duration) { _duration = duration; }

  // Optional clean up on shutdown

  static void CleanUp ();
};


#define __IOMANAGER_H__
#endif /* !defined  __IOMANAGER_H__ */
