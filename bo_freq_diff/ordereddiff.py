from .syllablediff import SyllableDiff
from collections import defaultdict
from pathlib import Path


class OrderedDiff:
    def __init__(self, text1, text2):
        self.diffs = SyllableDiff().diff(text1, text2)
        self.types = defaultdict(list)
        self.freqs = {}
        self.group_type()
        self.group_frequency()

    def group_type(self):
        for i, diff in enumerate(self.diffs):
            if type(diff) == dict:
                signature = ''
                if '-' in diff:
                    signature += '-' + diff['-']
                if '+' in diff:
                    signature += '+' + diff['+']
                self.types[signature].append(i)

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
                out.append(['Freq/Type'] + l_context + ['A', 'B'] + r_context)

                # add content
                for key, freq in ordered:
                    out += self.split_context_export(key, freq, left, right)
            else:
                # add csv header
                out.append(['Freq/Type', 'L', 'A', 'B', 'R'])

                # add content
                for key, freq in ordered:
                    out += self.joined_context_export(key, freq, left, right)

        elif order == 'alpha':
            print('not implemented yet')
        return out

    def split_context_export(self, key, freq, left, right):
        out = []
        # add the header to the current type
        header = [f'{str(freq)}: {key}'] + [''] * left + ['', ''] + [''] * right
        out.append(header)

        # add all the instances
        for occ in self.types[key]:
            l, orig, new, r = self.gen_context(occ, left, right)
            while len(l) < left:
                l = [''] + l
            while len(r) < right:
                r = r + ['']
            out.append([''] + l + [orig, new] + r)
        return out

    def joined_context_export(self, key, freq, left, right):
        out = []
        # add the header for the current type
        header = (f'{str(freq)}: {key}', '', '', '', '')
        out.append(header)
        # add all the instances
        for occ in self.types[key]:
            l, orig, new, r = self.gen_context(occ, left, right)
            l = ''.join(l)
            r = ''.join(r)
            out.append(('', l, orig, new, r))
        return out

    @staticmethod
    def write_to_csv(rows, filename=Path('test.csv')):
        out = '\n'.join([','.join(row) for row in rows])
        filename.write_text(out, encoding='utf-8-sig')

    def gen_context(self, occ, l_context, r_context):
        def choose_variant(context, variant='+'):
            for i in range(len(context)):
                if type(context[i]) == dict:
                    if variant in context[i]:
                        context[i] = context[i][variant]
                    else:
                        context[i] = context[i][list(context[i].keys())[0]]
            return context

        # adjust contexts
        while occ - l_context < 0:
            l_context -= 1
        while occ + r_context > len(self.diffs):
            r_context -= 1

        left = self.diffs[occ-l_context:occ]
        left = choose_variant(left)

        right = self.diffs[occ+1:occ+r_context]
        right = choose_variant(right)

        orig, new = '', ''
        if '-' in self.diffs[occ]:
            orig = self.diffs[occ]['-']
        if '+' in self.diffs[occ]:
            new = self.diffs[occ]['+']

        return left, orig, new, right
