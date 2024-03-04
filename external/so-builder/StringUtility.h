#if !defined (__STRINGUTILITY_H__)
#define __STRINGUTILITY_H__

#include <string>

class StringUtility
{
 public:
  static char        **tokenize (const char *str, const char *sep);
  static std::string   joinStrings (std::string sep... /*, (char *) NULL */);
  static std::string   joinTokens  (const char *sep, char **tokens);
  static void          releaseTokens (char **tokens);
  static std::string   replaceAll (const char *inStr, const char *findStr, std::string repStr);

};

#endif /* !defined (__STRINGUTILITY_H__) */
