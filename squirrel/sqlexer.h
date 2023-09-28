/*  see copyright notice in squirrel.h */
#ifndef _SQLEXER_H_
#define _SQLEXER_H_

#include "sqcompilationcontext.h"

typedef unsigned char LexChar;

using namespace SQCompilation;

enum SQLexerState {
  LS_REGULAR,
  LS_TEMPALTE
};

enum SQTokenFlags {
  TF_PREP_EOL = 1 << 0,             // end of line after this token
  TF_PREP_SPACE = 1 << 1,           // space after this token
};

struct SQLexer
{
    SQLexer(SQSharedState *ss, SQCompilationContext &ctx);
    ~SQLexer();
    void Init(SQSharedState *ss, const char *code, size_t codeSize);
    SQInteger Lex();
    const SQChar *Tok2Str(SQInteger tok);
private:
    SQInteger LexSingleToken();
    SQInteger GetIDType(const SQChar *s,SQInteger len);
    SQInteger ReadString(SQInteger ndelim,bool verbatim, bool advance = true);
    SQInteger ReadNumber();
    void LexBlockComment();
    void LexLineComment();
    SQInteger ReadID();
    SQInteger ReadDirective();
    void Next();
    static SQInteger readf(void *);
    SQInteger AddUTF8(SQUnsignedInteger ch);
    SQInteger ProcessStringHexEscape(SQChar *dest, SQInteger maxdigits);
    SQInteger _curtoken;
    SQTable *_keywords;
    SQBool _reached_eof;
    SQCompilationContext &_ctx;
    const char *_sourceText;
    size_t _sourceTextSize;
    size_t _sourceTextPtr;
public:
    SQInteger _prevtoken;
    SQInteger _currentline;
    SQInteger _lasttokenline;
    SQInteger _lasttokencolumn;
    SQInteger _currentcolumn;
    SQInteger _tokencolumn;
    SQInteger _tokenline;
    SQInteger _expectedToken;
    unsigned _prevflags;
    unsigned _flags;
    enum SQLexerState _state;
    const SQChar *_svalue;
    SQInteger _nvalue;
    SQFloat _fvalue;
    SQLEXREADFUNC _readf;
    SQUserPointer _up;
    LexChar _currdata;
    SQSharedState *_sharedstate;
    sqvector<SQChar> _longstr;
};

#endif
