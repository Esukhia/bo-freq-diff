from collections import defaultdict
from pathlib import Path


class SentenceOrderedDiff:
    def __init__(self, sents):
        self.sents = sents
        self.types = defaultdict(list)
        self.freqs = {}
        self.group_type()
        self.group_frequency()

    def group_type(self):
        for i, sent in enumerate(self.sents):
            for j, word in enumerate(sent):
                if type(word) == dict:
                    signature = ''
                    if '-' in word:
                        signature += '-' + word['-']
                    if '+' in word:
                        signature += '+' + word['+']
                    self.types[signature].append((i, j))

    def group_frequency(self):
        for k, v in self.types.items():
            self.freqs[k] = len(v)

    def export_diffs(self, order='freq', reverse=True, left=5, right=5, split_context=True):
        out = []  # rows of tuples each containing 4 elements: (title, left, orig, new, left)
        if order == 'freq':
            ordered = sorted([(k, v) for k, v in self.freqs.items()], key=lambda x: x[1], reverse=reverse)
            if split_context:
                # add csv header
                l_context = sorted([f'L{str(i)}' for i in range(1, left + 1)], reverse=True)
                r_context = [f'R{str(i)}' for i in range(1, right + 1)]
                out.append(['Freq/Type'] + l_context + ['A', 'B'] + r_context + ['sentence number'])

                # add content
                for key, freq in ordered:
                    out += self.split_context_export(key, freq, left, right)
            else:
                # add csv header
                out.append(['Freq/Type', 'L', 'A', 'B', 'R', 'sentence number'])

                # add content
                for key, freq in ordered:
                    out += self.joined_context_export(key, freq)

        elif order == 'alpha':
            print('not implemented yet')
        return out

    def split_context_export(self, key, freq, left, right):
        out = []
        # add the header to the current type
        header = [f'{str(freq)}: {key}'] + [''] * left + ['', ''] + [''] * right
        out.append(header)

        # add all the instances
        for sent, occ in self.types[key]:
            l, orig, new, r = self.gen_context(sent, occ, left, right)
            while len(l) < left:
                l = [''] + l
            while len(r) < right:
                r = r + ['']
            out.append([''] + l + [orig, new] + r + [str(sent)])
        return out

    def joined_context_export(self, key, freq):
        out = []
        # add the header for the current type
        header = (f'{str(freq)}: {key}', '', '', '', '')
        out.append(header)
        # add all the instances
        for sent, occ in self.types[key]:
            l, orig, new, r = self.gen_context(sent, occ, occ, len(self.sents[sent]) - occ)
            l = ''.join(l)
            r = ''.join(r)

            out.append(('', l, orig, new, r, str(sent)))
        return out

    @staticmethod
    def write_to_csv(rows, filename=Path('test.csv')):
        out = '\n'.join([','.join(row) for row in rows])
        filename.write_text(out, encoding='utf-8-sig')

    @staticmethod
    def choose_variant(context, variant='+'):
        for i in range(len(context)):
            if type(context[i]) == dict:
                if variant in context[i]:
                    context[i] = context[i][variant]
                else:
                    context[i] = context[i][list(context[i].keys())[0]]
        return context

    def gen_context(self, sent, occ, l_context, r_context):

        # adjust contexts
        while occ - l_context < 0:
            l_context -= 1
        while occ + r_context > len(self.sents[sent]):
            r_context -= 1

        left = self.sents[sent][occ-l_context:occ]
        left = self.choose_variant(left)

        right = self.sents[sent][occ+1:occ+r_context]
        right = self.choose_variant(right)

        orig, new = '', ''
        if '-' in self.sents[sent][occ]:
            orig = self.sents[sent][occ]['-']
        if '+' in self.sents[sent][occ]:
            new = self.sents[sent][occ]['+']

        return left, orig, new, right
