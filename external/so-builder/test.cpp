#include <stdio.h>
#include <stdlib.h>
#include <netdb.h>
#include <stdint.h>
#include <string.h>

int main () {

  const struct hostent *he = gethostbyname ("0.0.2.3");
  if (he == nullptr)
    return 0UL;

  size_t ip_len = static_cast<size_t> (he->h_length);
  uint32_t ipV4 = 0UL;

  if (ip_len == 4)
    (void) memcpy (&ipV4, he->h_addr_list[0], ip_len);

  printf ("%d", htonl(ipV4));

  return ipV4;

}
