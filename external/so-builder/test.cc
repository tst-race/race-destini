#include "sha256.h"



int main() {
  string s = sha256("abcdj").substr(0,4);
  //  cout << s << endl;
  //string s = "abcdj";
  char * p;
  long n = strtoul( s.c_str(), & p, 16 );
  if ( * p != 0 ) { //my bad edit was here
    cout << "not a number" << endl;
  }
  else {
    cout << n << endl;
  }
}
