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

            if token not in structure:
                structure[token] = {'freq': 0, 'tokens': {}, 'correct_concs': {}, 'order': 0, 'skrt': False}

            structure[token]['freq'] += freq
            if vol_name not in structure[token]['tokens']:
                structure[token]['tokens'][vol_name] = []

            for line in group[1:]:
                _, left, _, _, right, sent_number = line.split(',')
                structure[token]['tokens'][vol_name].append((left, right, sent_number))

    for num, token in enumerate(structure):
        structure[token]['order'] = num

    return structure


def load_sentences():
    in_path = Path('output/sentences')
    sentences = {}
    print('Loading sentences...', end=' ', flush=True)
    for f in in_path.glob('*.txt'):
        if f.stem not in sentences:
            sentences[f.stem] = f.read_text(encoding='utf-8-sig').split('\n')
    print('done.')
    return sentences


def generate_report(structure, ex_per_type):
    report = []
    for token in sorted(structure, key=lambda x: structure[x]['order']):
        if structure[token]['skrt']:
            continue
        if structure[token]['freq'] < ex_per_type:
            ex_per_type = structure[token]['freq']
        vols = structure[token]['tokens']
        error_type = f'{structure[token]["order"]+1}.\t{token}\t(freq:{structure[token]["freq"]})\n'
        exs = 0
        while exs < ex_per_type:
            for vol, tokens in vols.items():
                if exs < ex_per_type:
                    left, right, sent_num = random.choice(tokens)
                    t = f'{left}*{token}*{right},{vol},{sent_num}\n'
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


def mark_skrt(structure):
    bo_non_bo = {}
    for n, error in enumerate(structure):
        parts = error.strip('+-').split('+')
        for p in parts:
            if not structure[error]['skrt']:
                tokens = tok.tokenize(p)
                for t in tokens:
                    if not structure[error]['skrt'] and t.skrt or t.type != 'syl':
                        bo_non_bo[t] = True
                        structure[error]['skrt'] = True

    return structure


def find_correct_concs(sentences, error):
    output = []
    for vol, sents in sentences.items():
        already_found = []
        if vol in structure[error]['tokens']:
            already_found = [int(a[2]) for a in structure[error]['tokens'][vol]]
        for num, sent in enumerate(sents):
            if num not in already_found:
                output.append(sent)

    return output


def get_context(sentences, sent_num, vol, left, right):
    sent_num = int(sent_num)
    return ''.join(sentences[vol][sent_num - left: sent_num]), ''.join(sentences[vol][sent_num + 1: sent_num + right + 1])


def generate_examples(structure, error_tokens_dir, skrt_error_tokens_dir, correct_concs_dir, skrt_correct_concs_dir, maximum, left, right, gen_skrt=False):
    sentences = load_sentences()
    for error in structure:
        if error == '-':
            continue

        if not gen_skrt and structure[error]['skrt']:
            continue

        if structure[error]['skrt']:
            cur_token_dir = skrt_error_tokens_dir
            cur_conc_dir = skrt_correct_concs_dir
        else:
            cur_token_dir = error_tokens_dir
            cur_conc_dir = correct_concs_dir

        print(error)
        if structure[error]['freq'] < maximum and structure[error]['freq'] > 0:
            maximum = structure[error]['freq']
        vols = structure[error]['tokens']
        exs = 0
        examples = []
        previous_ex = ''
        while exs < maximum:
            for vol, tokens in vols.items():
                if exs < maximum:
                    left_context, right_context, sent_num = random.choice(tokens)
                    l_sent, r_sent = get_context(sentences, sent_num, vol, left, right)
                    left_context = str(l_sent + left_context).replace('_', ' ')
                    right_context = str(right_context + r_sent).replace('_', ' ')
                    # format example
                    ex = f'{left_context}*{error}*{right_context} {vol}'
                    if ex != previous_ex:
                        examples.append({'ex': ex})
                        previous_ex = ex

                    exs += 1

        output = str(examples).replace(',', ',\n')
        Path(cur_token_dir / (str(structure[error]['order'] + 1) + error[:20] + '.json')).write_text(output, encoding='utf-8-sig')

        # correct occurences
        if '-' in error:
            if '+' in error:
                token = error[error.find('-') + 1: error.find('+')]
            else:
                token = error[error.find('-') + 1:]
            exs = 0
            found = {}
            for vol, sents in sentences.items():
                occs = []
                for num, s in enumerate(sents):
                    if token in s:
                        if token in s:
                            ex = s.replace(token, '*' + token + '*')
                            left_context = ''.join(sents[num - left: num])
                            right_context = ''.join(sents[num + 1: num + right + 1])
                            ex = f'{left_context}{ex}{right_context} {vol}'
                            occs.append(ex)
                if occs:
                    found[vol] = occs

            if found:
                examples = []
                previous_ex = ''
                while exs < maximum:
                    for vol, sents in found.items():
                        if exs < maximum:
                            ex = random.choice(sents)
                            if previous_ex != ex:
                                examples.append({'ex': ex})
                                previous_ex = ex
                            exs += 1
                output = str(examples).replace(',', ',\n')
                Path(cur_conc_dir / (str(structure[error]['order']+1) + error[:20] + '_correct_sentences.json')).write_text(output, encoding='utf-8-sig')


if __name__ == '__main__':
    in_name = Path('output/error_diffs')
    error_tokens_dir = Path('output/error_tokens')
    skrt_error_tokens_dir = Path('output/skrt_error_tokens')
    conc_dir = Path('output/correct_concs')
    skrt_conc_dir = Path('output/skrt_correct_concs')

    if not in_name.is_dir():
        print('no input')
    if not conc_dir.is_dir():
        conc_dir.mkdir(exist_ok=True)
    if not skrt_conc_dir.is_dir():
        skrt_conc_dir.mkdir(exist_ok=True)
    if not error_tokens_dir.is_dir():
        error_tokens_dir.mkdir(exist_ok=True)
    if not skrt_error_tokens_dir.is_dir():
        skrt_error_tokens_dir.mkdir(exist_ok=True)

    for f in error_tokens_dir.glob('*.*'):
        f.unlink()
    for f in skrt_error_tokens_dir.glob('*.*'):
        f.unlink()
    for f in conc_dir.glob('*.*'):
        f.unlink()
    for f in skrt_conc_dir.glob('*.*'):
        f.unlink()

    tokens_per_type_in_report = 20
    tokens_per_type_in_total = 100
    structure = load_diffs(in_name)
    structure = mark_skrt(structure)
    report = generate_report(structure, tokens_per_type_in_report)
    Path('output/report.txt').write_text(report, encoding='utf-8-sig')
    generate_examples(structure, error_tokens_dir, skrt_error_tokens_dir, conc_dir, skrt_conc_dir, tokens_per_type_in_total, 1, 1, gen_skrt=False)
