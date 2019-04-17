from pathlib import Path

from bo_freq_diff import SegmentDiff, SentenceOrderedDiff
from pybo import BoTokenizer, Token
from textunits import sentencify

rpl_start, rpl_middle, rpl_end = '{~~', '~>', '~~}'
del_start, del_end = '{--', '--}'
pls_start, pls_end = '{++', '++}'
marks = [rpl_start, rpl_middle, rpl_end, del_start, del_end, pls_start, pls_end]
tok = BoTokenizer('GMD', ignore_chars=['\n'])


def gen_sent_pair(sent):
    orig = []
    corr = []
    for word in sent:
        if word.endswith(' '):
            space = ' '
            word = word.strip()
        else:
            space = ''
        if word.startswith(rpl_start) and word.endswith(rpl_end) and rpl_middle in word:
            to_del, to_add = word.replace(rpl_start, '').replace(rpl_end, '').split(rpl_middle)
            orig.append(to_del + space)
            corr.append(to_add + space)
        elif word.startswith(del_start) and word.endswith(del_end):
            to_del = word.replace(del_start, '').replace(del_end, '')
            orig.append(to_del + space)
        elif word.startswith(pls_start) and word.endswith(pls_end):
            to_add = word.replace(pls_start, '').replace(pls_end, '')
            corr.append(to_add + space)
        elif '~' not in word and '+' not in word and '-' not in word:
            orig.append(word + space)
            corr.append(word + space)
        else:
            raise SyntaxError(f'{word} is incorrect.')

    return ''.join(orig), ''.join(corr)


def join_diffs(tokens):
    i = 0
    while i < len(tokens):
        cur = tokens[i]
        diff = ''
        if '{' in cur.content and '}' not in cur.content:
            j = 0
            while '}' not in cur.content:
                cur = tokens[i + j]
                diff += cur.content
                j += 1
            token = Token()
            token.content = diff
            tokens[i: i + j] = [token]

        i += 1

    return tokens


def space_sep_tokens(string):
    tokens = tok.tokenize(string)
    tokens = [t.content.replace(' ', '_') for t in tokens]
    return ' '.join(tokens)


def get_spaces_back(words):
    i = 0
    while i < len(words):
        if '_' in words[i]:
            new = words[i].replace('_', ' ')
            if i > 0:
                if isinstance(words[i - 1], str):
                    words[i - 1] += new
                elif isinstance(words[i - 1], dict):
                    for key in words[i - 1]:
                        words[i - 1][key] += new
                del words[i]
            else:
                words[i] = new

        if i < len(words) and isinstance(words[i], dict):
            for key in words[i]:
                words[i][key] = words[i][key].replace('_', ' ')

        i += 1

    return words


def prepare_dataset(filename1, filename2, outdir):
    orig = filename1.read_text(encoding='utf-8-sig')
    corr = filename2.read_text(encoding='utf-8-sig')

    sd = SegmentDiff()
    diffs = sd.diff(orig, corr, mode='CM')
    diffs = [a if a else ' ' for a in diffs]  # get back the spaces that are empty strings
    joined = ''.join(diffs)

    tokens = tok.tokenize(joined)
    tokens = join_diffs(tokens)
    sentences = sentencify(tokens)
    sentences = [[s.content for s in sent] for l, sent in sentences]  # extract strings from sentence tokens

    # sentence_pairs = [gen_sent_pair(sent) for sent in sentences]
    sentence_pairs = []
    for num, sent in enumerate(sentences):
        sentence_pairs.append(gen_sent_pair(sent))

    sentence_pairs = [(a.replace(' ', '_'), b.replace(' ', '_')) for a, b in sentence_pairs]
    # ds = SegmentDiff(space_sep_tokens)
    diffs = [sd.diff(t1, t2) for t1, t2 in sentence_pairs]
    diffs = [get_spaces_back(d) for d in diffs]

    sod = SentenceOrderedDiff(diffs)
    print('ok')
    split_out = sod.export_diffs()
    joined_out = sod.export_diffs(split_context=False)
    sod.write_to_csv(split_out, outdir / (filename1.stem + '_split.csv'))
    sod.write_to_csv(joined_out, outdir / (filename1.stem + '_joined.csv'))


if __name__ == '__main__':
    # make sure the directories exist
    orig = Path('input/original')
    corrected = Path('input/corrected')
    outdir = Path('output')
    assert orig.is_dir()
    assert corrected.is_dir()
    assert outdir.is_dir()

    for o in orig.glob('*.txt'):
        c = corrected / o.name
        if c.is_file():
            prepare_dataset(o, c, outdir)
