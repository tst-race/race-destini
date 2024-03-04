/**
 * Copyright 2009-2010 Bart Trojanowski <bart@jukie.net>
 * Licensed under GPLv2, or later, at your choosing.
 *
 * bidirectional popen() call
 *
 * @param rwepipe - int array of size three
 * @param exe - program to run
 * @param argv - argument list
 * @return pid or -1 on error
 *
 * The caller passes in an array of three integers (rwepipe), on successful
 * execution it can then write to element 0 (stdin of exe), and read from
 * element 1 (stdout) and 2 (stderr).
 */

#ifndef __POPENRWE_H__

#ifdef __cplusplus
extern "C" {
#endif

int popenRWE   (int *rwepipe, const char *exe, char * const argv[]);
int pcloseRWE  (int pid, int *rwepipe);
int pcloseRWE2 (int pid, int *rwepipe, int *wstatus);

#ifdef __cplusplus
} /* close extern "C" { */
#endif

#define __POPENRWE_H__
#endif
