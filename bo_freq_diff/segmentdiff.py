from .dmp import DMP
from pybo import PyBoChunk


def syllabify(string):
    pybochunk = PyBoChunk(string)
    chunks = pybochunk.chunk()
    chunks = pybochunk.get_chunked(chunks)
    return ' '.join([c[1] for c in chunks])


class SegmentDiff:
    def __init__(self, segment=syllabify):
        self.dmp = DMP()
        self.sgmt = segment

    def diff(self, text1, text2, mode=None):
        syllabified1 = self.sgmt(text1)
        syllabified2 = self.sgmt(text2)
        diffs = self.dmp.diff_wordMode(syllabified1, syllabified2)
        diffs = self.format_diffs(diffs)
        if mode == 'CM':
            diffs = self.cm_markup(diffs)
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
                formatted.extend(text.split(' '))  # split the text between diffs into syllables
            elif op == -1:
                diff['-'] = text.replace(' ', '')  # delete all spaces added to separate syllables
            elif op == 1:
                diff['+'] = text.replace(' ', '')  # idem

        if diff:
            formatted.append(diff)

        return formatted

    def cm_markup(self, diffs):
        i = 0
        while i < len(diffs):
            el = diffs[i]
            if isinstance(el, dict):
                if '-' in el and '+' in el:
                    diffs[i] = '{~~' + el['-'] + '~>' + el['+'] + '~~}'
                elif '-' in el:
                    diffs[i] = '{--' + el['-'] + '--}'
                elif '+' in el:
                    diffs[i] = '{++' + el['+'] + '++}'
                else:
                    raise ValueError('wrong patch operation value')
            i += 1

        return diffs
