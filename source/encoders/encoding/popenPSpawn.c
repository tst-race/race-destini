/**
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
 *
 * This implementation uses posix_spawn () avoid unintentional fork ()-
 * induced thread deadlocks and avoid the (intractable) problem of defining
 * pipes with vfork ().
 *
 * Based upon https://github.com/sni/mod_gearman/blob/master/common/popenRWE.c
 */

/*
 https://cgi.cse.unsw.edu.au/~cs1521/20T2/code/processes/spawn_read_pipe.c
 */

#include "popenPSpawn.h"

#include <spawn.h>
#include <stdlib.h>
#include <unistd.h>
#include <unistd.h>
#include <sys/types.h>
#include <sys/wait.h>

int popenRWE(int *rwepipe, const char *exe, char * const argv[]) {
  int in[2];
  int out[2];
  int err[2];

#define _CREATE_PIPE_PAIR(_pFD, _error)	\
  if (pipe (_pFD) < 0) goto _error;	// NOLINT(bugprone-macro-parentheses)

  // Create the pipe pairs
  _CREATE_PIPE_PAIR (in,  error_in);
  _CREATE_PIPE_PAIR (out, error_out);
  _CREATE_PIPE_PAIR (err, error_err);

  // Create a list of file actions to be carried out on spawned process
  posix_spawn_file_actions_t actions;
  if (posix_spawn_file_actions_init (&actions) /* != 0 */)
    goto error_fork;

#define _CLOSE_DUP(_pFD, _idx1, _idx2, _stdFD)						\
  if (posix_spawn_file_actions_addclose (&actions, _pFD[_idx1])		/* != 0 */ ||	/* NOLINT(bugprone-macro-parentheses) */	\
      posix_spawn_file_actions_adddup2  (&actions, _pFD[_idx2], _stdFD) /* != 0 */)	/* NOLINT(bugprone-macro-parentheses)*/	\
    goto error_fork;

  // Configure spawned process file descriptors
  _CLOSE_DUP (in,  1, 0, 0);
  _CLOSE_DUP (out, 0, 1, 1);
  _CLOSE_DUP (err, 0, 1, 2);

#if defined (POSIX_SPAWN_USEVFORK)
  posix_spawnattr_t spawnattr;
  if (posix_spawnattr_init (&spawnattr) /* != 0 */)
    goto error_fork;

  if (posix_spawnattr_setflags (&spawnattr, POSIX_SPAWN_USEVFORK) /* != 0 */)
	goto error_fork;

  #define _SPAWN_ATTR	&spawnattr
#else
  #define _SPAWN_ATTR	NULL
#endif

  extern char **environ;
  pid_t		pid;
 
  // Spawn the process
  if (posix_spawn (&pid, exe, &actions, _SPAWN_ATTR, argv, environ) /* != 0 */)
    goto error_fork;

  (void) posix_spawn_file_actions_destroy (&actions);

#if defined (POSIX_SPAWN_USEVFORK)
  (void) posix_spawnattr_destroy (_SPAWN_ATTR);
#endif

#define _CLOSE_COPY(_pFD, _idx1, _idx2, _stdFD)	\
  close (_pFD[_idx2]);			/* NOLINT(bugprone-macro-parentheses) */ \
  rwepipe[_stdFD] = _pFD[_idx1];	/* NOLINT(bugprone-macro-parentheses) */

  // Close unused pipe ends and copy spawned process file descriptors
  _CLOSE_COPY (in,  1, 0, 0);
  _CLOSE_COPY (out, 0, 1, 1);
  _CLOSE_COPY (err, 0, 1, 2);

  return pid;

#define _CLOSE_PIPE_FDS(_label, _pFD)					\
_label:			/* NOLINT(bugprone-macro-parentheses) */	\
  close (_pFD[0]);	/* NOLINT(bugprone-macro-parentheses) */	\
  close (_pFD[1]);	/* NOLINT(bugprone-macro-parentheses) */

  _CLOSE_PIPE_FDS (error_fork, err);
  _CLOSE_PIPE_FDS (error_err,  out);
  _CLOSE_PIPE_FDS (error_out,  in);

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
