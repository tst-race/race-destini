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

#include "popenRWE.h"

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <sys/types.h>
#include <sys/wait.h>

int popenRWE(int *rwepipe, const char *exe, char * const argv[]) {
  int in[2];
  int out[2];
  int err[2];
  int pid;
  int rc;

  rc = pipe(in);
  if (rc<0)
    goto error_in;

  rc = pipe(out);
  if (rc<0)
    goto error_out;

  rc = pipe(err);
  if (rc<0)
    goto error_err;

  pid = fork();

  if (pid > 0) { /* parent */
    close(in[0]);
    close(out[1]);
    close(err[1]);
    rwepipe[0] = in[1];
    rwepipe[1] = out[0];
    rwepipe[2] = err[0];
    return pid;
  } else if (pid == 0) { /* child */
    close(in[1]);
    close(out[0]);
    close(err[0]);
    close(0);
    if(!dup(in[0])) {
      ;
    }
    close(1);
    if(!dup(out[1])) {
      ;
    }
    close(2);
    if(!dup(err[1])) {
      ;
    }

    execv(exe, argv);
    _exit(1);
  } else
    goto error_fork;

  return pid;

error_fork:
  close(err[0]);
  close(err[1]);
error_err:
  close(out[0]);
  close(out[1]);
error_out:
  close(in[0]);
  close(in[1]);
error_in:
  return -1;
}

int pcloseRWE2(int pid, int *rwepipe, int *wstatus)
{
  close(rwepipe[0]);
  close(rwepipe[1]);
  close(rwepipe[2]);
  return waitpid(pid, wstatus, 0);
}

int pcloseRWE(int pid, int *rwepipe)
{
  int wstatus;
  (void) pcloseRWE2 (pid, rwepipe, &wstatus);
  return wstatus;
}
