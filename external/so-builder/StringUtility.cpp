#include <cstdarg>
#include <cstdlib>
#include <cstring>
#include <vector>

#include "StringUtility.h"


  char **
StringUtility::tokenize (const char *str, const char *sep)
{
  char *_str   = strdup (str);
  char *_start = _str;
  char *_token;
  std::vector <char *> tokenList;

  do {
    _token = strsep (&_start, sep);
    tokenList.push_back (_token);
  } while (_token /* != (char *) NULL */);

  char **tokens = static_cast <char **> (malloc (sizeof (char *) * tokenList.size ()));
  char **entry  = tokens;

  for (std::vector <char *>::iterator it = tokenList.begin ();
       it != tokenList.end ();
       ++it) {
    *entry = *it;
    ++entry;
  }

  return tokens;
}

  std::string
StringUtility::joinStrings (std::string sep...)
{
  va_list     args;
  std::string retStr = "";

  va_start (args, sep);
 
  while (true) {
    char *str = va_arg (args, char *);

    if (str == nullptr)
      break;

    if (strlen (str) /* > 0 */) {
      if (retStr.length () /* > 0 */)
	retStr += sep + str;
      else
	retStr  = str;
    }
  }

  va_end (args);

  return retStr;
}

  std::string
StringUtility::joinTokens (const char *sep, char **tokens)
{
  std::string retStr = "";

  for (/* tokens */; *tokens /* != (char *) NULL */; ++tokens) {
    char *token = *tokens;

    if (strlen (token) /* > 0 */) {
      if (retStr.length () /* > 0 */)
	retStr += sep;

      retStr += token;
    }
  }

  return retStr;
}

  void
StringUtility::releaseTokens (char **tokens)
{
  free (*tokens);
  free (tokens);
}

  std::string
StringUtility::replaceAll (const char *inStr, const char *findStr, std::string repStr)
{
  char *start = const_cast <char *> (inStr);
  char *token = strstr (start, findStr);

  if (token == nullptr)
    return std::string (inStr);

  else {
    size_t      lPrefix = static_cast <size_t> (token - start);
    size_t      delta   = lPrefix + strlen (findStr);
    std::string retStr  = std::string (start, lPrefix) +
                          repStr +
                          replaceAll (start + delta, findStr, repStr);

    return retStr;
  }
}


#if defined (_TEST_MAIN_)

#include <iostream>

  int
main ()
{
  std::cout << StringUtility::joinStrings (" ... ",
					   "We're", "very", "hesitant", "about this!", (char *) NULL)
	    << '\n';

  char **tokens = StringUtility::tokenize ("This is  a  test.", " ");

  std::cout << StringUtility::joinTokens ("|", tokens) << '\n';
  StringUtility::releaseTokens (tokens);

  std::cout << StringUtility::replaceAll ("What can we <secret> with <secret>?", "<secret>", "(ssh!)")
	    << '\n';
}

#endif
