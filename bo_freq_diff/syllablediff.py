from .dmp import DMP
from pybo import PyBoChunk


class SyllableDiff:
    def __init__(self):
        self.dmp = DMP()
        self.pbc = PyBoChunk

    def diff(self, text1, text2):
        syllabified1 = self.syllabify(text1)
        syllabified2 = self.syllabify(text2)
        diffs = self.dmp.diff_wordMode(syllabified1, syllabified2)
        diffs = self.format_diffs(diffs)
        return diffs

    def format_diffs(self, diffs):
        formatted = []
        diff = {}
        for op, text in diffs:
            text = text.rstrip(' ')  # strip the space added to syllabify
            if op == 0:
                if diff:
                    formatted.append(diff)
                    diff = {}
                formatted.append(text)
            elif op == -1:
                diff['-'] = text
            elif op == 1:
                diff['+'] = text

        if diff:
            formatted.append(diff)

        return formatted

    def syllabify(self, string):
        pybochunk = self.pbc(string)
        chunks = pybochunk.chunk()
        chunks = pybochunk.get_chunked(chunks)
        return ' '.join([c[1] for c in chunks])
