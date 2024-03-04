#include <cstdlib>
#include <fstream>
#include <iostream>
#include <string>

#include "CLICodec.h"


// NOLINTNEXTLINE(bugprone-macro-parentheses)
#define _SS_DIAGPRINT(_sExpr) {std::cout << _sExpr << std::endl;}


  static void
_codecTest (CLICodec *cliCodec, const char *pTestMsg)
{
    std::string _testMsg = std::string (pTestMsg);
    //    std::string _testMsg = "";
    void   	*pEnMsgOut;
    size_t 	 nEnMsgOut;

    _SS_DIAGPRINT ("Before .encode () with \"" << _testMsg << "\" (" << _testMsg.length () << ")");
    int     status = cliCodec->encode (_testMsg.c_str (), _testMsg.length (), &pEnMsgOut, &nEnMsgOut);

    if (status == 0) {
        _SS_DIAGPRINT (".encode () nEnMsgOut: " << nEnMsgOut);
    
    
	void   *pDeMsgOut;
	size_t  nDeMsgOut;
	_SS_DIAGPRINT ("Before .decode ()");
	status = cliCodec->decode (pEnMsgOut, nEnMsgOut, &pDeMsgOut, &nDeMsgOut);

	if (status == 0) {
	    _SS_DIAGPRINT (".decode () nDeMsgOut: " << nDeMsgOut << ", pDeMsgOut: \"" << std::string ((char *) pDeMsgOut, nDeMsgOut) << "\"");
	}
	else {
	    _SS_DIAGPRINT (".decode () failed with " << status);
	}
    }
    else {
        _SS_DIAGPRINT (".encode () failed with " << status);
    }
}


  int
main (int argc, char **argv)
{
    CLICodec::SetDirname ("/code");

    // Get codec definition

    auto codecJSONPath = CLICodec::DirFilename ("codec.json");
    auto codecJSON     = codecJSONPath.c_str ();

    if (fileExists (codecJSON)) {
         --argc; ++argv;

         std::ifstream fJSON (codecJSON);
         auto cliCodec = CLICodec::GetCodecFromStream (fJSON);
         if (cliCodec == nullptr || !cliCodec->isGood ())
             throw std::runtime_error ("DestiniEncoding: bad or incomplete JSON (" + codecJSONPath + ")");
	 else
	   _codecTest (cliCodec, argc /* > 0 */ ? *argv : "This is a test");
    }
    else
        throw std::runtime_error ("DestiniEncoding: JSON (" + codecJSONPath + ") not found");

    return 0;
}
