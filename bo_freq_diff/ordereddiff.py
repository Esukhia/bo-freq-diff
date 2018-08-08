from .syllablediff import SyllableDiff
from collections import defaultdict
import csv


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
                signature = f'-{str(diff["-"])}+{str(diff["+"])}'
                self.types[signature].append(i)

    def group_frequency(self):
        for k, v in self.types.items():
            self.freqs[k] = len(v)

    def export_diffs(self, order='freq', reverse=True, left=5, right=5):
        out = []  # rows of tuples each containing 4 elements: (title, left, orig, new, left)
        if order == 'freq':
            ordered = sorted([(k, v) for k, v in self.freqs.items()], reverse=reverse)
            for key, freq in ordered:
                # add the header for the current type
                out.append((f'{str(freq)}: {key}', '', '', '', ''))
                # add all the instances
                for occ in self.types[key]:
                    l, orig, new, r = self.gen_context(occ, left, right)
                    out.append(('', l, orig, new, r))
        elif order == 'alpha':
            print('not implemented yet')
        return out

    def write_to_csv(self, filename, rows):
        header = ('title', 'left', 'original', 'new', 'left')
        with open(filename, 'w', encoding='utf-8-sig') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(header)
            for row in rows:
                writer.writerow(row)

    def gen_context(self, occ, l_context, r_context):
        def choose_variant(context, variant='+'):
            for i in range(len(context)):
                if type(context[i]) == dict:
                    context[i] = context[i][variant]
            return context

        # adjust contexts
        while occ - l_context < 0:
            l_context -= 1
        while occ + r_context > len(self.diffs):
            r_context -= 1

        left = self.diffs[occ-l_context:occ]
        left = choose_variant(left)
        left = ''.join(left)

        right = self.diffs[occ+1:occ+r_context]
        right = choose_variant(right)
        right = ''.join(right)

        orig, new = self.diffs[occ]['-'], self.diffs[occ]['+']

        return left, orig, new, right
