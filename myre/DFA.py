from collections import defaultdict
from dataclasses import dataclass

@dataclass
class MatchObj:
    whole_text: str
    start: int
    end: int # exclusive

    def text(self):
        return self.whole_text[self.start: self.end]

    def color_text(self):
        left = self.whole_text[: self.start]
        mid = self.whole_text[self.start: self.end]
        right = self.whole_text[self.end:]
        return f"{left}\033[31m{mid}\033[0m{right}"

class DFA:
    def __init__(self, start, pos_to_sym, follows):
        self.start = frozenset(start)
        self.pos_to_sym = pos_to_sym
        self.follows = follows

        # src_state, sym -> dst_state
        self.trans = defaultdict(dict)

        # visited
        self.visited = set()
        self.finish_states = set()

        self.build_graph(self.start)

    def build_graph(self, cur_state):
        self.visited.add(cur_state)

        # build sym_to_poslist
        sym_to_poslist = defaultdict(list)
        for pos in cur_state:
            sym = self.pos_to_sym[pos]
            if not isinstance(sym, str):
                # should be the sentinel
                self.finish_states.add(cur_state)
            sym_to_poslist[sym].append(pos)

        for sym, poslist in sym_to_poslist.items():
            next_state = set()
            for pos in poslist:
                next_state |= self.follows[pos]

            next_state = frozenset(next_state)
            if not next_state: # next_state is empty
                continue
            assert isinstance(sym, str), f"sym is {sym}" # sym is not the sentinel
            self.trans[cur_state][sym] = next_state
            if next_state not in self.visited:
                self.build_graph(next_state)

    def match_prefix(self, text, start_pos):
        last_match_idx = None
        cur_state = self.start
        if cur_state in self.finish_states:
            last_match_idx = start_pos

        for sym_idx in range(start_pos, len(text)):
            sym = text[sym_idx]
            if sym not in self.trans[cur_state]:
                break
            cur_state = self.trans[cur_state][sym]
            if cur_state in self.finish_states:
                last_match_idx = sym_idx + 1
        return MatchObj(text, start_pos, last_match_idx) if last_match_idx is not None else None
        
    def match(self, text):
        """
        Return True if any substring of text is matched
        """
        # TODO this implementation naively try each start position.
        # One alternative way is prepend '.*' to the pattern
        for pos in range(len(text)):
            if matched := self.match_prefix(text, pos):
                return matched
        return None

    def __str__(self):
        return f"DFA: start {self.start}, pos_to_sym {self.pos_to_sym}, trans table {self.trans}, finish_states {self.finish_states}"
