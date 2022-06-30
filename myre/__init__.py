from myre.parse import parse
from myre.debug import debug

def match(pattern: str, text: str):
    """
    Here are the rough workflow
    1. parse the regular expression into a tree
    2. calculate nullable/firstpos/lastpos and followpos functions
    3. build a NFA without epsilon transition
    4. convert the NFA to DFA
    5. match the text with the DFA
    """
    tree = parse(pattern)
    debug(f"\n{tree} {tree.root.firstpos}")
    tree.dump_followpos()
    debug(tree.dfa)
    return tree.dfa.match(text)
