from pathlib import Path
import random
from pybo import BoString, BoTokenizer


tok = BoTokenizer('GMD')


def load_diffs(diff_path):
    """
    :param diff_path: the diff folder path
    :return: the following structure:
    {'type': {'freq': 0,
              'tokens': {'vol1': ['occurences', ''],
                         'vol2': ['occ']}
             }
     }
    """
    structure = {}
    bo_non_bo = {}
    for f in Path(diff_path).glob('*_joined.csv'):
        vol_name = f.stem[:f.stem.rfind('_')]
        content = f.read_text(encoding='utf-8-sig').split('\n')[1:]
        groups = []
        cur = []
        for line in content:
            if not line.startswith(','):
                # add previous group
                if cur:
                    groups.append(cur)
                    cur = []
                cur.append(line)
            else:
                cur.append(line)
        if cur:
            groups.append(cur)

        for group in groups:
            group = [l for l in group if l]
            if not group:
                continue
            freq, token = group[0].split(':')
            freq, token = int(freq), token.replace(',', '').strip()

            # filter skrt and non-bo types
            if is_not_bo(token, bo_non_bo):
                continue

            if token not in structure:
                structure[token] = {'freq': 0, 'tokens': {}, 'order': 0}

            structure[token]['freq'] += freq
            if vol_name not in structure[token]['tokens']:
                structure[token]['tokens'][vol_name] = []

            for line in group[1:]:
                _, left, _, _, right = line.split(',')
                structure[token]['tokens'][vol_name].append((left, right))

    for num, token in enumerate(structure):
        structure[token]['order'] = num

    return structure


def generate_report(structure, ex_per_type):
    report = []
    for token in sorted(structure, key=lambda x: structure[x]['order']):
        if structure[token]['freq'] < ex_per_type:
            ex_per_type = structure[token]['freq']
        vols = structure[token]['tokens']
        error_type = f'{structure[token]["order"]+1}.\t{token}\t(freq:{structure[token]["freq"]})\n'
        exs = 0
        while exs < ex_per_type:
            for vol, tokens in vols.items():
                if exs < ex_per_type:
                    left, right = random.choice(tokens)
                    t = f'{left}*{token}*{right},{vol}\n'
                    error_type += t
                    exs += 1

        report.append(error_type)
    return f'amount of error types = {len(report)}\n' + '\n'.join(report)


def is_not_bo(string, bo_non_bo):
    parts = string.lstrip('-').lstrip('+').split('+')
    has_no_bo = 0
    for part in parts:
        if part in bo_non_bo:
            if bo_non_bo[part]:
                has_no_bo += 1
        else:
            tokens = tok.tokenize(part)
            for t in tokens:
                if t.skrt or t.type != 'syl':
                    has_no_bo += 1
                    bo_non_bo[part] = True
                else:
                    bo_non_bo[part] = False
    return has_no_bo > 0


def generate_examples(structure, out_dir, maximum):
    for error in structure:
        if structure[error]['freq'] < maximum and structure[error]['freq'] > 0:
            maximum = structure[error]['freq']
        vols = structure[error]['tokens']
        exs = 0
        examples = []
        while exs < maximum:
            for vol, tokens in vols.items():
                if exs < maximum:
                    left, right = random.choice(tokens)
                    # format example
                    ex = f'{left}*{error}*{right}'

                    examples.append({'ex': ex})
                    exs += 1

        output = str(examples).replace(',', ',\n')
        Path(Path(out_dir) / (str(structure[error]['order']+1) + error[:20] + '.json')).write_text(output, encoding='utf-8-sig')


if __name__ == '__main__':
    in_name = Path('output/error_diffs')
    out_dir = Path('output/error_tokens')
    if not in_name.is_dir():
        print('no input')
    if not out_dir.is_dir():
        out_dir.mkdir(exist_ok=True)

    for f in out_dir.glob('*.*'):
        f.unlink()

    tokens_per_type_in_report = 20
    tokens_per_type_in_total = 100
    structure = load_diffs(in_name)
    report = generate_report(structure, tokens_per_type_in_report)
    Path('output/report.txt').write_text(report, encoding='utf-8-sig')
    generate_examples(structure, out_dir, tokens_per_type_in_total)
    print()