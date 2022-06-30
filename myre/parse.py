from myre.DFA import DFA
from myre.debug import debug

class Sentinel:
    """
    The special terminating symbol
    """
    def __str__(self):
        return '#' # show it as a '#'

    __repr__ = __str__

SENTINEL = Sentinel()

class Node:
    def indent(self, indent):
        """
        indent: the level of indentation

        Return the indent string
        """
        return "  " * indent

    def __str__(self):
        return self.tostr()

# TODO avoid this global state by something like ParseCtx
next_pos = 1
pos_to_sym = {}
follows = []

class SymbolNode(Node):
    def __init__(self, symbol):
        global next_pos, pos_to_sym
        super().__init__()
        assert symbol is SENTINEL or len(symbol) == 1
        self.symbol = symbol
        self.pos = next_pos
        next_pos += 1

        pos_to_sym[self.pos] = self.symbol

    def tostr(self, indent=0):
        return f"{self.indent(indent)}SYM '{self.symbol}', pos {self.pos}\n"

    @property
    def nullable(self):
        return False

    @property
    def firstpos(self):
        return {self.pos}

    @property
    def lastpos(self):
        return {self.pos}

    def compute_followpos(self):
        pass

    def dup(self):
        return SymbolNode(self.symbol)

class ConcatNode(Node):
    def __init__(self, lhs, rhs):
        super().__init__()
        self.lhs = lhs
        self.rhs = rhs

    def tostr(self, indent=0):
        return f"{self.indent(indent)}CONCAT\n{self.lhs.tostr(indent+1)}{self.rhs.tostr(indent+1)}"

    @property
    def nullable(self):
        return self.lhs.nullable and self.rhs.nullable

    @property
    def firstpos(self):
        ret = self.lhs.firstpos
        if self.lhs.nullable:
            ret |= self.rhs.firstpos
        return ret

    @property
    def lastpos(self):
        ret = self.rhs.lastpos
        if self.rhs.nullable:
            ret |= self.lhs.lastpos
        return ret

    def compute_followpos(self):
        self.lhs.compute_followpos()
        self.rhs.compute_followpos()
        for a in self.lhs.lastpos:
            for b in self.rhs.firstpos:
                follows[a].add(b) 

    def dup(self):
        return ConcatNode(self.lhs.dup(), self.rhs.dup())

class UnionNode(Node):
    def __init__(self, lhs, rhs):
        super().__init__()
        self.lhs = lhs
        self.rhs = rhs

    def tostr(self, indent=0):
        return f"{self.indent(indent)}UNION\n{self.lhs.tostr(indent+1)}{self.rhs.tostr(indent+1)}"

    @property
    def nullable(self):
        return self.lhs.nullable or self.rhs.nullable

    @property
    def firstpos(self):
        return self.lhs.firstpos | self.rhs.firstpos

    @property
    def lastpos(self):
        return self.lhs.lastpos | self.rhs.lastpos

    def compute_followpos(self):
        self.lhs.compute_followpos()
        self.rhs.compute_followpos()

    def dup(self):
        return UnionNode(self.lhs.dup(), self.rhs.dup())

class StarNode(Node):
    def __init__(self, nested):
        super().__init__()
        self.nested = nested # the nested node

    def tostr(self, indent=0):
        return f"{self.indent(indent)}STAR\n{self.nested.tostr(indent+1)}"

    @property
    def nullable(self):
        return True

    @property
    def firstpos(self):
        return self.nested.firstpos

    @property
    def lastpos(self):
        return self.nested.lastpos

    def compute_followpos(self):
        for a in self.nested.lastpos:
            for b in self.nested.firstpos:
                follows[a].add(b)
        self.nested.compute_followpos()

    def dup(self):
        return StarNode(self.nested.dup())

class Parser:
    def __init__(self, pattern):
        self.pattern = pattern
        assert len(pattern) > 0
        self.next_idx = 0

    def peek(self, off=1):
        if self.next_idx + off - 1 < len(self.pattern):
            return self.pattern[self.next_idx + off - 1]
        elif self.next_idx + off - 1 == len(self.pattern):
            return SENTINEL
        else:
            return None

    def next_if(self, tok):
        if self.peek() == tok:
            self.next_idx += 1
            return True
        else:
            return False

    def next(self):
        ret = self.peek()
        assert ret is not None
        self.next_idx += 1
        return ret

    def parse_character_class(self):
        """
        TODO: does not support escaping for now
        """

        # TODO: handle the empty class '[]'
        assert self.peek() != ']'

        retnode = None

        def add_ch(next_ch):
            nonlocal retnode
            newnode = SymbolNode(next_ch)
            if not retnode:
                retnode = newnode
            else:
                retnode = UnionNode(retnode, newnode)

        while self.peek() != ']':
            assert self.peek() is not None
            next_ch = self.next()

            if self.peek() == '-' and self.peek(2) not in [']', SENTINEL]:
                # handle range
                self.next()
                end_ch = self.next()

                for ch_val in range(ord(next_ch), ord(end_ch) + 1):
                    add_ch(chr(ch_val))
            else:
                add_ch(next_ch)

        self.next() # consume ']'
        return retnode

    def parse_atom(self):
        if self.next_if('('):
            ret = self.parse_union()
            assert(self.next_if(')'))
            return ret

        if self.next_if('['):
            return self.parse_character_class()

        assert self.peek() is not None
        next_ch = self.next()

        # TODO: need handle other special symbols like '\' etc.
        # Uncomment the next line to fatal for the unsupported special tokens
        # assert next_ch is SENTINEL or next_ch.isalpha(), f"next_ch is {next_ch}"
        return SymbolNode(next_ch)

    def handle_plus(self, nested):
        """
        TODO: current implementation is we treat 'nested+' as 'nested nested *'.
        This cause the symbols for nested get duplicated. A better way is to
        support plus directly.
        """
        dup = nested.dup()
        return ConcatNode(
            nested,
            StarNode(dup)
        )

    def parse_star(self):
        # we treat multi consecutive stars as a single star
        ret = self.parse_atom()

        if self.next_if('+'):
            # TODO does not handle consecutive plus for now
            return self.handle_plus(ret)
        if self.peek() != '*':
            return ret
        while self.next_if('*'):
            pass
        return StarNode(ret)

    def parse_concat(self):
        ret = None
        while True:
            cur = self.parse_star()
            if ret is None:
                ret = cur
            else:
                ret = ConcatNode(ret, cur)
            if self.peek() in ['|', ')', None]: # in follow set of C (disregarding the 'C S' rule)
                break
        return ret

    def parse_union(self):
        ret = None
        while True:
            cur = self.parse_concat()
            if ret is None:
                ret = cur
            else:
                ret = UnionNode(ret, cur)
            if not self.next_if('|'):
                break
        return ret
    
    def parse(self):
        """
        Parse the regular expression to a tree.
        Only support the following operators so far:
        - concatenation
        - union
        - Kleene closure
    
        An atom regular expression is just a single symbol;
        An inductive regular 'r' expression has one of the following forms:
        1. (s)
        2. st
        3. s|t
        4. s*
    
        All ops (concatenation/union/Kleene closure) are left associative.
    
        We can use the follow CFG to represent a regular expression:
        E -> E '|' C # union
           | C
           ;
        C -> C S # concat
           | S
           ;
        S -> S '*'
           | A
           ;
        A -> Symbol
           | ( E )
           ;
        """
        root = self.parse_union()
        assert self.peek() is None, "We should have consuumed all characters"
        return ParseTree(root)

class ParseTree:
    def __init__(self, root):
        global follows
        self.root = root
        follows.clear()
        follows = [set() for _ in range(next_pos)]
        self.root.compute_followpos()

        self.dfa = DFA(
            start=self.root.firstpos,
            pos_to_sym=pos_to_sym,
            follows=follows,
        )

    def __str__(self):
        return str(self.root)

    def followpos(self, pos):
        return follows[pos]

    def dump_followpos(self):
        for pos in range(1, next_pos):
            debug(f"{pos} followpos {follows[pos]}")

def parse(pattern: str):
    global next_pos, pos_to_sym
    next_pos = 1
    pos_to_sym.clear()
    return Parser(pattern).parse()
