# Makefile V2.2
#
# mkmf -F l.Makefile

# Variables to modify:
#
#   CFLAGS:         as desired.
#   CFLAGS_ADD:	    as desired.
#   C++FLAGS:	    as desired.
#   C++FLAGS_ADD:   as desired.
#   DOCPUSH:	    documents installed in DOCDEST (i.e., doc/mylib.ms).
#   HDRSPUSH:	    headers installed in HDRSDEST (i.e., mylib.h).
#   MANPUSH:	    man pages installed in MANDEST (i.e., man/mylib.1).
#   LIBRARY:	    name of this library (i.e., libmylib.a).
#   TOPDIR:	    relative location of installation directory.
#
#   CONFIGURATION:  The following baseline qualifiers may be added:
#			application
#			library
#			lint
#			CPLUSPLUS
#			DEBUG
#			NO_STATIC_$(OS_SYSN)

CONFIGURATION += DEBUG
CONFIGURATION += application CPLUSPLUS NO_STATIC_FreeBSD NO_STATIC_SunOS

BRANDELF      = /usr/bin/brandelf    

F_BRANDELF    = $(shell if test -f $(BRANDELF) ; then echo 1 ; fi)

C++	      = g++

C++FLAGS      = -D__CPLUSPLUS__ $(ARCH_FLAGS) $(CCOPT) $(C++FLAGS_ADD)

#C++FLAGS_ADD  = 

CC	      = gcc

ifneq (, $(findstring DEBUG, $(CONFIGURATION)))
    CCOPT	 = -g -O0
    LDFLAGS	+= -g
else
    CCOPT     = -O2
endif
ifneq (, $(findstring lint, $(CONFIGURATION)))
    CCOPT    += -Dlint -ansi -pedantic -Wunused -Wuninitialized		\
		-Wimplicit -Wreturn-type -Wcomment -Wchar-subscripts	\
		-Wparentheses -Wswitch -DDO_STRICT_ANSI
endif

DEV_INCLS     = -I$(EM_INC_DIR)			\
		-I../libunit

INCLS	      = -I. $(DEV_INCLS)	 	\
		$(OS_INCLS)

CURR_DIR      = $(shell pwd)

ARCH_FLAGS  =

# Establish the "no newline" echo flag
ifeq ("$(shell echo -n)", "")
    ECHO_FLAG = -n
endif

DEFS	      = -DIPV4_MAINTAIN_BACKWARD_REFERENCES

CFLAGS	      = $(ARCH_FLAGS) $(CCOPT) $(DEFS) $(CFLAGS_ADD)

CFLAGS.java   = -I$(JAVADIR) -I$(JAVADIR)/OS_NAME

CPPFLAGS     += $(INCLS)

# CPPFLAGS     += -DIPV4_MAINTAIN_BACKWARD_REFERENCES

CPPFLAGS     += $(MACROS_SYS)				\
		$(DEFS)

ifneq (, $(findstring mempool, $(MAKECMDGOALS)))
    CPPFLAGS += -DDEBUG_PS -DDEBUG_ALLOC
endif

# Target-specific C preprocessor #defines

DEBUGGER      =

DEST	      = $(TOPDIR)/bin

DOCDEST       = $(TOPDIR)/doc

DOCPUSH       = 

HDRS	      =

HDRS.java     = $(SRCS.javah:%.java=%.h) $(SRCS.javahs:%.java=%.h)

HDRSDEST      = $(TOPDIR)/include

HDRSPUSH      = *.h

JAVA	      = java

JAVAFLAGS     = 

JAVA.args     = 

JAVAC	      = javac

JAVACFLAGS    = -g
#JAVACFLAGS    = -g -deprecation

JAVAH	      = javah

JAVAPATH      = 

ifneq (, $(findstring CPLUSPLUS, $(CONFIGURATION)))
    LD.dyn    = $(C++)
else
    LD.dyn    = $(CC)
endif

LDFLAGS	     += $(.LOAD_EVAL)

LDFLAGS.dyn   = 

# -Bstatic for cc, -static for gcc

LDFLAGS_STATIC = $(LDFLAGS) -L$(TOPDIR)/lib

ifeq ($(CC), gcc)
    LDFLAGS_STATIC += -static
else
    LDFLAGS_STATIC += -Bstatic
endif

LD_LIBRARY_PATH = .:..

LIBRARY       = 

LIBRARY.dyn   = 

# Target-specific library declarations

LIBS_SYS      = $(OS_LIB_SYS) -lm -levent -ljsoncpp

LIBS	      = 

ifeq ($(WIN), X)
    LIBS     += -L/usr/local/lib		\
		-lXaw -lXmu -lXt -lXext -lX11
endif


LIBS_MEMPOOL  = ${EM_LIB_DIR}/libmp.a	

LIBS_STATIC   = $(LIBS)

ifneq (, $(findstring CPLUSPLUS, $(CONFIGURATION)))
    LINKER    = $(C++)
else
    LINKER    = $(CC)
endif

MAKEFILE      = Makefile

MANDEST       = $(TOPDIR)/man

MANPUSH       = 

DEST	      = .

OS_DIR	      = .

OBJS 	      = $(SRCS.cpp:%.cpp=$(OS_DIR)/%.o) $(SRCS:%.c=$(OS_DIR)/%.o)

OBJS_ADD      = 

OS_LIB_SYS    = $(LIB_SYS.$(OS_SYSN))

PRINT	      = pr

PROGRAM_NAME  = testCLICodec

PROGRAM	      = $(OS_DIR)/$(PROGRAM_NAME)

PROGRAM_PURIFY   = $(PROGRAM).purify

PROGRAM_QUANTIFY = $(PROGRAM).quantify

PROGRAM_COVERAGE = $(PROGRAM).coverage

PROGRAM_STATIC = $(PROGRAM).static

PROGRAM_MEMPOOL  = $(PROGRAM).mp

PURIFYCACHE   = -cache-dir=/project/emerald/emerald_devel/purify_cache \
		-always-use-cache-dir

PURIFYIGNORE  = -ignore-runtime-environment=yes

# PURIFYLOGFILE = -logfile="%v_%p.log"

PURIFYOPTIONS = $(PURIFYIGNORE) $(PURIFYCLCTR)	\
		$(PURIFYCACHE) $(PURIFYLOGFILE)	\
		-chain-length="12"

PURIFY        = purify $(PURIFYOPTIONS)

QUANTIFY      = quantify $(PURIFYCACHE)

COVERAGE      = purecov $(PURIFYCACHE)

SHELL	      = /bin/sh

ifneq (, $(findstring application, $(CONFIGURATION)))
    SRCS.cpp  = StringUtility.cpp	\
		CLICodec.cpp		\
		testCLICodec.cpp
endif

ifneq (, $(findstring library, $(CONFIGURATION)))
    SRCS      = 
endif

ifneq (, $(findstring java, $(CONFIGURATION)))
    SRCS      = $(SRCS.javahs:%.java=_%.c)
endif

# Class only
SRCS.java     = 

# Header only
SRCS.javah    = 

# Headers and stubs
SRCS.javahs   = 

STUBS.java    = $(SRCS.javahs:%.java=%.stub)

SUFFIX	      = m:sC C:sC cpp:sC java:s stub:sC

ifneq (, $(findstring application, $(CONFIGURATION)))
    TARGET    = $(PROGRAM)
endif
ifneq (, $(findstring library, $(CONFIGURATION)))
    TARGET    = $(LIBRARY)
endif
ifneq (, $(findstring java, $(CONFIGURATION)))
    TARGET    = $(CLASSES.java) $(HDRS.java) $(STUBS.java) $(OBJS) \
		$(LIBRARY.dyn)
endif

TARGET += $(.ALWAYS_EVAL)

TEST.java     = $(SRCS.java:%.java=%)

TOPDIR	      = .

WIN	      = NONE

ZIPFILE	      = 

ZIPFILE.src   = $(CURR_DIR)Src.zip


.SUFFIXES:	.m .c .C .cpp .java .class .stub

.m.o:;		$(OBJCC) $(CFLAGS) -c $<
		@if [ -f $*.c ]; then rm -f $*.c; exit 1; fi

$(OS_DIR)/%.o:	%.c
		$(CC) $(CFLAGS) $(CPPFLAGS) -c $< -o $@

$(OS_DIR)/%.o:	%.C
		$(C++) $(C++FLAGS) $(CPPFLAGS) -c $< -o $@

$(OS_DIR)/%.o:	%.cpp
		$(C++) $(C++FLAGS) $(CPPFLAGS) -c $< -o $@

.java.class:;	$(JAVAPATH)$(JAVAC) $(JAVACFLAGS) $<

.class.h:;	@rm -f $*.h
		$(JAVAPATH)$(JAVAH) $*

.class.stub:;	@rm -f $*.stub
		$(JAVAPATH)$(JAVAH) -stubs -o $*.stub $*

all:		$(OS_DIR) $(TARGET)

$(LIBRARY):	$(OBJS)
		@echo $(ECHO_FLAG) "Loading $(LIBRARY) ... "
		@ar cru $(LIBRARY) $(OBJS)
		@ranlib $(LIBRARY)
		@echo "done"

$(LIBRARY.dyn):	$(CLASSES.java) $(HDRS.java) $(STUBS.java) $(OBJS)
		@echo $(ECHO_FLAG) "Loading $(LIBRARY.dyn) ... "
		@$(LD.dyn) -G -o $(LIBRARY.dyn) $(LDFLAGS.dyn) $(OBJS)
		@echo "done"

$(PROGRAM):     $(OS_DIR) $(OBJS) $(LIBS) # dynamic
		@echo $(ECHO_FLAG) "Loading $(PROGRAM) ... "
		@rm -f	$(OS_DIR)/.debug_support	\
			$(OS_DIR)/.profile_support
		@(LIBS_SYS="$(LIBS_SYS)"; \
		 $(LINKER) $(ARCH_FLAGS) $(LDFLAGS) \
		     $(OBJS) $(OBJS_ADD) $(LIBS) $$LIBS_SYS -o $(PROGRAM))
            ifneq (, $(findstring DEBUG, $(CONFIGURATION)))
		@touch $(OS_DIR)/.debug_support
            endif
            ifneq (, $(findstring PROFILE, $(CONFIGURATION)))
		@touch $(OS_DIR)/.profile_support
            endif
		@echo "done"


$(PROGRAM_STATIC): $(OS_DIR) $(OBJS) $(OBJS_STATIC) $(LIBS) # static
            ifneq (, $(findstring NO_STATIC_$(OS_SYSN), $(CONFIGURATION)))
		$(error Static build is disallowed under $(OS_SYSN))
            endif
		@echo $(ECHO_FLAG) "Loading $(PROGRAM_STATIC) ... "
		@($(LINKER) $(LDFLAGS_STATIC)			\
		    $(OBJS) $(OBJS_STATIC) $(OBJS_ADD)		\
		    $(LIBS_STATIC) $(LIBS_SYS) -o $(PROGRAM_STATIC))
            ifneq (, $(F_BRANDELF))
		@$(BRANDELF) -t $(OS_SYSN) $(PROGRAM_STATIC)
            endif
		@echo "done"

$(PROGRAM_PURIFY):	$(OS_DIR) $(OBJS) $(LIBS) # purify
		@echo $(ECHO_FLAG) "Loading $(PROGRAM_PURIFY) ... "
		@($(PURIFY)					\
		    $(LINKER) $(LDFLAGS) $(OBJS) $(OBJS_ADD)	\
		      $(LIBS) $(LIBS_SYS) -o $(PROGRAM_PURIFY))
		@echo "done"

$(PROGRAM_QUANTIFY):	$(OS_DIR) $(OBJS) $(LIBS) # quantify
		@echo $(ECHO_FLAG) "Loading $(PROGRAM_QUANTIFY) ... "
		@($(QUANTIFY)					\
		    $(LINKER) $(LDFLAGS) $(OBJS) $(OBJS_ADD)	\
		      $(LIBS) $(LIBS_SYS) -o $(PROGRAM_QUANTIFY))
		@echo "done"

$(PROGRAM_COVERAGE):	$(OS_DIR) $(OBJS) $(LIBS) # coverage
		@echo $(ECHO_FLAG) "Loading $(PROGRAM_COVERAGE) ... "
		@($(COVERAGE)					\
		    $(LINKER) $(LDFLAGS) $(OBJS) $(OBJS_ADD)	\
		      $(LIBS) $(LIBS_SYS) -o $(PROGRAM_COVERAGE))
		@echo "done"

$(PROGRAM_MEMPOOL):	$(OS_DIR) $(OBJS) $(LIBS) # mempool
		@echo $(ECHO_FLAG) "Loading $(PROGRAM_MEMPOOL) ... "
		@($(LINKER) $(LDFLAGS) $(OBJS) $(OBJS_ADD)	\
		    $(LIBS) $(LIBS_MEMPOOL) $(LIBS_SYS) -o $(PROGRAM_MEMPOOL))
		@echo "done"

.PHONY:		all		\
		purify		\
		quantify	\
		coverage	\
		static		\
		mempool		\
		zipsrc		\
		clean		\
		depend		\
		extract		\
		index		\
		install		\
		lint		\
		print		\
		rcsdiff		\
		test		\
		run		\
		tags		\
		update

purify:		$(PROGRAM_PURIFY)

quantify:	$(PROGRAM_QUANTIFY)

coverage:	$(PROGRAM_COVERAGE)

static:		$(PROGRAM_STATIC)

mempool:	$(PROGRAM_MEMPOOL)

zipsrc:;	@echo $(ECHO_FLAG) "Making/updating $(ZIPFILE.src) ... "
		@(cd ..; \
		  zip -u -l \
		  -r ./$(CURR_DIR)/$(ZIPFILE.src) $(CURR_DIR) \
		  -i \*README -i \*TODO -i \*EBNF \
		  -i \*EXTENDING -i \*PORTING \
		  -i \*USAGE -i \*INSTALL -i \*NOTES \
		  -i \*FILES -i \*CHANGES -i \*REQUIREMENTS -i \*BUGS \
		  -i \*install\* -i \*configure \
		  -i \*.htm* \
		  -i \*.txt -i \*.1 -i \*.3 -i \*.8 -i \*.tmpl \
		  -i \*.inc -i \*.init -i \*.invinit \
		  -i \*.net -i \*.config \
		  -i \*.map -i \*.conf \
		  -i \*.csh -i \*.sh \
		  -i \*.ps \
		  -i \*.ps.\* \
		  -i \*.y -i \*.l \*.awk \
		  -i \*.m4 -i \*.in -i \*mkdep -i \*.sub -i \*.guess \
		  -i \*.in -i \*.sub \
		  $(ZIPFILE_ADD) \
		  -i \*.java -i \*.c -i \*.cpp -i \*.h \
		  -i \*.s \
		  -i \*Makefile\* -i \*make\* \
		  -x \*,v )

clean:;		rm -f $(OBJS) $(TARGET) $(OS_DIR)/*.d	\
		$(PROGRAM_PURIFY) $(PROGRAM_QUANTIFY)	\
		$(PROGRAM_COVERAGE) $(PROGRAM_STATIC)	\
		$(PROGRAM_MEMPOOL) \
		$(CLASSES.java) $(HDRS.java) $(STUBS.java) *.class C_* P_*

depend:;	mkmf -f $(MAKEFILE) \
		LIBRARY=$(LIBRARY) LIBRARY.dyn=$(LIBRARY.dyn) \
		DEST=$(DEST) CFLAGS="$(CFLAGS)" C++FLAGS="$(C++FLAGS)" \
		SUFFIX="$(SUFFIX)"

.doc:		$(DOCPUSH)
		@-if [ "$?" != "" ]; then \
			echo Installing $? in $(DOCDEST); \
			(cd $(DOCDEST); rm -f $(?F)); \
			cp $? $(DOCDEST); \
			(cd $(DOCDEST); chmod 0444 $(?F)); \
		fi
		@touch .doc

extract:;	ar xo $(DEST)/$(LIBRARY)
		rm -f __.SYMDEF

.headers:	$(HDRSPUSH)
		@-if [ "$?" != "" ]; then \
			echo Installing $? in $(HDRSDEST); \
			(cd $(HDRSDEST); rm -f $(?F)); \
			cp $? $(HDRSDEST); \
			(cd $(HDRSDEST); chmod 0444 $(?F)); \
		fi
		@touch .headers
 
index:;		ctags -wx $(HDRS) $(SRCS)

install:	$(DEST) $(PROGRAM)
		@echo " "
		@echo "installing $(PROGRAM) in $(DEST)"
		@rm -f $(DEST)/$(PROGRAM) $(DEST)/$(PROGRAM_STATIC)
		@cp $(PROGRAM) $(DEST)/$(PROGRAM)
		@chmod 555 $(DEST)/$(PROGRAM)
		@ if [ -x $(PROGRAM_STATIC) ] ; then \
		    cp $(PROGRAM_STATIC) $(DEST)/$(PROGRAM_STATIC) ; \
		    chmod 555 $(DEST)/$(PROGRAM_STATIC) ; \
		  fi

library:        $(LIBRARY) $(LIBRARY.dyn)

lint:;		lint $(CPPFLAGS) $(SRCS)

# Needs to be modified so it installs files in the man subdirectory
# based on the file's extension.
.man:		$(MANPUSH)
		@-if [ "$?" != "" ]; then \
			echo Installing $? in $(MANDEST); \
			(cd $(MANDEST); rm -f $(?F)); \
			cp $? $(MANDEST); \
			(cd $(HDRSDEST); chmod 444 $(?F)); \
		fi
		@touch .man

print:;		$(PRINT) $(HDRS) $(SRCS)

rcsdiff:;	rcsdiff RCS/*,v

test:		$(PROGRAM)
		@LD_LIBRARY_PATH="$(LD_LIBRARY_PATH)"; \
			export LD_LIBRARY_PATH; \
			$(DEBUGGER) $(PROGRAM)

run:		$(TARGET)
		@LD_LIBRARY_PATH="$(LD_LIBRARY_PATH)"; \
			export LD_LIBRARY_PATH; \
			CLASSPATH="$(CLASSPATH)"; \
			export CLASSPATH; \
			RUNLIST="$(TEST.java)"; \
	                while [ -n "$${RUNLIST:-}" ] ; \
				do \
				i=`echo $$RUNLIST | cut -f1 -d' '` ; \
				RUNLIST=`echo $$RUNLIST | cut -f2- -d' '` ; \
				if [ $$i = $$RUNLIST ] ; then \
					RUNLIST='' ; \
				fi ; \
				echo "\n::: $$i :::\n" ; \
				$(JAVAPATH)$(JAVA) $(JAVAFLAGS) $$i \
					$(JAVA.args); \
				done

tags:           $(HDRS) $(SRCS)
		ctags $(HDRS) $(SRCS)
		etags $(HDRS) $(SRCS)

update:         $(DEST)/$(LIBRARY) $(DEST)/$(LIBRARY.dyn)

$(DEST)/$(LIBRARY): $(SRCS) $(HDRS) 
		@-ar xo $(DEST)/$(LIBRARY)
		@make -f $(MAKEFILE) DEST=$(DEST) install clean

$(OS_DIR)/%.d:	%.c
		@-if [ ! -d $(OS_DIR) ] ; then \
		    $(EM_MKDIR) $(OS_DIR) ; \
		fi ; \
		$(SHELL) -ec '$(CC) -MM $(CPPFLAGS) $< \
		    | sed '\''s#$*\.o[ :]*#$(OS_DIR)/& $@ #g'\'' > $@'

$(OS_DIR)/%.d:	%.cpp
		@-if [ ! -d $(OS_DIR) ] ; then \
		    $(EM_MKDIR) $(OS_DIR) ; \
		fi ; \
		$(SHELL) -ec '$(C++) -MM $(CPPFLAGS) $< \
		    | sed '\''s#$*\.o[ :]*#$(OS_DIR)/& $@ #g'\'' > $@'

include ${SRCS:%.c=$(OS_DIR)/%.d}
ifneq (, $(findstring CPLUSPLUS, $(CONFIGURATION)))
    include ${SRCS.cpp:%.cpp=$(OS_DIR)/%.d}
endif

A2EPARSER_DEPENDS	= _a2eihooks.c ia2eparser.c	\
			  _tmplStrings.c		\
			  BNRanking.cpp BNRanking.h	\
			  Ranking.cpp Ranking.h		

ifneq (, $(findstring XML_SUPPORT, $(CONFIGURATION)))
    A2EPARSER_DEPENDS  += _xml2ps.c	\
			  xmlstream.h
endif

ifneq (, $(findstring POSTGRES_SUPPORT, $(CONFIGURATION)))
    A2EPARSER_DEPENDS  += _postgres.c
endif

$(OS_DIR)/alertmgr.o: $(A2EPARSER_DEPENDS)
###
