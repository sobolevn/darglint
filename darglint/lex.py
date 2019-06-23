"""Defines a function for lexing a comment, `lex`."""

from typing import (
    Iterator,
    List,
    Optional,
)
from .peaker import Peaker
from .token import Token, TokenType

# These convenience functions take an optional string
# because the peaker could return None when at the end
# of the stream.


def _is_space(char):
    # type: (Optional[str]) -> bool
    return char == ' '


def _is_newline(char):
    # type: (Optional[str]) -> bool
    return char == '\n'


def _is_colon(char):
    # type: (Optional[str]) -> bool
    return char == ':'


def _is_hash(char):
    # type: (Optional[str]) -> bool
    return char == '#'


def _is_separator(char):
    # type: (Optional[str]) -> bool
    """Check whether if `char` is a separator other than newline or space.

    Args:
        char: The character to check.

    Returns:
        true if `char` is a separator other than newline or space.

    """
    if char is None:
        return False
    return char.isspace() and not (_is_space(char) or _is_newline(char))


def _is_double_quotation(char):
    # type: (Optional[str]) -> bool
    return char == '"'


def _is_lparen(char):
    # type: (Optional[str]) -> bool
    return char == '('


def _is_rparen(char):
    # type: (Optional[str]) -> bool
    return char == ')'


def _is_word(char):
    # type: (str) -> bool
    return not any([
        _is_space(char),
        _is_newline(char),
        _is_colon(char),
        _is_separator(char),
        _is_double_quotation(char),
        _is_hash(char),
        _is_lparen(char),
        _is_rparen(char),
    ])


def lex(program):
    # type: (str) -> Iterator[Token]
    """Create a stream of tokens from the string.

    Args:
        program: The program to lex, as a string.

    Yields:
        Tokens lexed from the string.

    """
    extra = ''  # Extra characters which are pulled but unused from a check.
    peaker = Peaker((x for x in program or []))  # the stream
    line_number = 0
    while peaker.has_next():
        # Each of the following conditions must move the stream
        # forward and -- excepting separators -- yield a token.
        if _is_space(peaker.peak()):
            spaces = ''.join(peaker.take_while(_is_space))
            for _ in range(len(spaces) // 4):
                yield Token(' ' * 4, TokenType.INDENT, line_number)
        elif _is_newline(peaker.peak()):
            value = peaker.next()
            yield Token(value, TokenType.NEWLINE, line_number)
            line_number += 1
        elif _is_colon(peaker.peak()):
            value = peaker.next()
            yield Token(value, TokenType.COLON, line_number)
        elif _is_separator(peaker.peak()):
            peaker.take_while(_is_separator)
        elif _is_double_quotation(peaker.peak()):
            value = ''.join(peaker.take_while(_is_double_quotation))
            if len(value) >= 3:
                for _ in range(len(value) // 3):
                    yield Token('"""', TokenType.DOCTERM, line_number)
            else:
                extra = value
        elif _is_hash(peaker.peak()):
            value = peaker.next()
            yield Token(value, TokenType.HASH, line_number)
        elif _is_lparen(peaker.peak()):
            value = peaker.next()
            yield Token(value, TokenType.LPAREN, line_number)
        elif _is_rparen(peaker.peak()):
            value = peaker.next()
            yield Token(value, TokenType.RPAREN, line_number)
        else:
            value = ''.join(peaker.take_while(_is_word))
            if extra != '':
                value = extra + value
                extra = ''
            assert len(value) > 0, "There should be non-special characters."
            yield Token(value, TokenType.WORD, line_number)


KEYWORDS = {
    'Args': TokenType.ARGUMENTS,
    # 'Arguments': NodeType.ARGUMENTS,
    # 'Returns': NodeType.RETURNS,
    'Yields': TokenType.YIELDS,
    'Raises': TokenType.RAISES,
    'Returns': TokenType.RETURNS,
    'noqa': TokenType.NOQA,
}


def condense(tokens):
    # type: (Iterator[Token]) -> List[Token]
    """Condense the stream of tokens into a list consumable by CYK.

    This servers two purposes:

    1. It minimizes the lookup table used in the CYK algorithm.
       (The CYK algorithm is a dynamic algorithm, with one dimension
       in the two-dimension lookup table being determined by the number
       of tokens.)

    2. It applies more discriminate token types to the tokens identified
       by lex.  Eventually, this will be moved into the lex function.

    Args:
        tokens: The stream of tokens from the lex function.

    Returns:
        A List of tokens which have been condensed into as small a
        representation as possible.

    """
    ret = list()  # type: List[Token]
    try:
        curr = next(tokens)
    except StopIteration:
        return ret

    if curr.value in KEYWORDS:
        curr.token_type = KEYWORDS[curr.value]

    for token in tokens:
        if token.token_type == TokenType.WORD and token.value in KEYWORDS:
            ret.append(curr)
            curr = Token(
                token.value,
                KEYWORDS[token.value],
                token.line_number,
            )
        elif token.token_type == TokenType.WORD:
            if curr.token_type == TokenType.WORD:
                curr.value += ' {}'.format(token.value)
            else:
                ret.append(curr)
                curr = token
        else:
            ret.append(curr)
            curr = token

    ret.append(curr)

    return ret
