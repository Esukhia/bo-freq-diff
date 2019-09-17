from pathlib import Path
import time
import datetime
import re

from bo_freq_diff import SegmentDiff, SentenceOrderedDiff
from pybo import WordTokenizer, Token, Chunks, sentence_tokenizer
from pybo import ChunkMarkers as cm

rpl_start, rpl_middle, rpl_end = '{~~', '~>', '~~}'
del_start, del_end = '{--', '--}'
pls_start, pls_end = '{++', '++}'
marks = [rpl_start, rpl_middle, rpl_end, del_start, del_end, pls_start, pls_end]
tok = WordTokenizer('GMD', ignore_chars=['\n'])


class BoNonboChunk(Chunks):
    def __init__(self, string):
        super().__init__(string, ignore_chars=['\n'])

    def bo_chunk(self):
        return self.chunk_bo_chars()

    def get_cleaned_bo(self):
        chunks = self.bo_chunk()
        chunks = self.get_chunked(chunks)
        has_bo = True if cm.BO.value in [a[0] for a in chunks] else False
        chunks = [b for a, b in chunks if a == cm.BO.value]
        return ''.join(chunks).strip(), has_bo


def clean_non_bo(string):
    chunk = BoNonboChunk(string)
    cleaned, _ = chunk.get_cleaned_bo()
    cleaned = cleaned.strip()
    return cleaned


def gen_sent_pair(sent):
    orig = []
    corr = []
    for word in sent:
        if word.endswith('_'):
            end = '_'
            word = word.rstrip('_')
        else:
            end = ''

        if word.startswith('_'):
            start = '_'
            word = word.lstrip('_')
        else:
            start = ''

        word = word.replace(rpl_start + rpl_middle + rpl_end, '')
        word = word.replace(del_start + del_end, '')
        word = word.replace(pls_start + pls_end, '')

        if word.startswith(rpl_start) and word.endswith(rpl_end) and rpl_middle in word:
            to_del, to_add = word.replace(rpl_start, '').replace(rpl_end, '').split(rpl_middle)
            orig.append(start + to_del + end)
            corr.append(start + to_add + end)
        elif word.startswith(del_start) and word.endswith(del_end):
            to_del = word.replace(del_start, '').replace(del_end, '')
            orig.append(start + to_del + end)
        elif word.startswith(pls_start) and word.endswith(pls_end):
            to_add = word.replace(pls_start, '').replace(pls_end, '')
            corr.append(start + to_add + end)
        elif '~' not in word and '+' not in word and '-' not in word:
            orig.append(start + word + end)
            corr.append(start + word + end)
        else:
            raise SyntaxError(f'{word} is incorrect.\n{sent}')

    return ''.join(orig), ''.join(corr)


def join_diffs(tokens):
    i = 0
    while i < len(tokens):
        if i == 2258:
            print()
        cur = tokens[i]
        diff = ''
        if '{' in cur.text and cur.text.count('{') != cur.text.count('}'):
            j = 0

            cur = tokens[i + j]
            diff += cur.text
            j += 1
            while diff.count('{') != diff.count('}'):
                cur = tokens[i + j]
                diff += cur.text
                j += 1
            new_tokens = []
            for n in diff.split('}'):
                new = Token()
                if n and '{' in n:
                    new.text = n + '}'
                else:
                    new.text = n
                new_tokens.append(new)
            tokens[i: i + j] = new_tokens

        i += 1

    for num, t in enumerate(tokens):
        if t.text.count('{') != t.text.count('}'):
            print(num, t.text)

    return tokens


def space_sep_tokens(string):
    tokens = tok.tokenize(string)
    tokens = [t.text.replace(' ', '_') for t in tokens]
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


def write_sentences(filename, sentences):
    out_file = Path('output/sentences') / filename.name
    if not out_file.parent.is_dir():
        out_file.parent.mkdir(exist_ok=True)
    with out_file.open('w', encoding='utf-8-sig') as w:
        for sent in sentences:
            if len(sent) == 2:
                w.write(sent[1] + '\n')
            else:
                w.write(sent[0] + '\n')


def prepare_dataset(filename1, filename2, outdir):
    orig = filename1.read_text(encoding='utf-8-sig').replace('\n', '').replace('༌', '་')
    orig = clean_non_bo(orig)
    orig = re.sub(r'\s+', '_', orig)
    corr = filename2.read_text(encoding='utf-8-sig').replace('\n', '').replace('༌', '་')
    corr = clean_non_bo(corr)
    corr = re.sub(r'\s+', '_', corr)

    sd = SegmentDiff()
    diffs = sd.diff(orig, corr, mode='CM')
    diffs = [a if a else ' ' for a in diffs]  # get back the spaces that are empty strings
    joined = ''.join(diffs)

    tokens = tok.tokenize(joined)
    tokens = join_diffs(tokens)
    sentences = sentence_tokenizer(tokens)
    sentences = [[s.text for s in sent] for l, sent in sentences]  # extract strings from sentence tokens

    # sentence_pairs = [gen_sent_pair(sent) for sent in sentences]
    sentence_pairs = []
    for num, sent in enumerate(sentences):
        sentence_pairs.append(gen_sent_pair(sent))

    sentence_pairs = [(a.replace(' ', '_'), b.replace(' ', '_')) for a, b in sentence_pairs]
    # ds = SegmentDiff(space_sep_tokens)
    write_sentences(filename1, sentence_pairs)
    diffs = [sd.diff(t1, t2) for t1, t2 in sentence_pairs]
    diffs = [get_spaces_back(d) for d in diffs]

    sod = SentenceOrderedDiff(diffs)
    split_out = sod.export_diffs()
    joined_out = sod.export_diffs(split_context=False)
    sod.write_to_csv(split_out, outdir / (filename1.stem + '_split.csv'))
    sod.write_to_csv(joined_out, outdir / (filename1.stem + '_joined.csv'))


if __name__ == '__main__':
    # make sure the directories exist
    uptime = time.time()
    orig = Path('input/original')
    corrected = Path('../derge-tengyur/text')
    outdir = Path('output/error_diffs')
    assert orig.is_dir()
    assert corrected.is_dir()
    assert outdir.is_dir()

    orig_files = [o.stem for o in orig.glob('*.txt')]
    cor_files = [c.stem for c in corrected.glob('*.txt')]
    o_only = [o for o in orig_files if o not in cor_files]
    c_only = [c for c in cor_files if c not in orig_files]
    print('only in original:', o_only)
    print('only in corrected:', c_only)

    for o in list(orig.glob('*.txt'))[3:]:
        c = corrected / o.name
        if c.is_file():
            print(o.name, end=' ', flush=True)
            start = time.time()
            prepare_dataset(o, c, outdir)
            end = time.time()
            elapsed = str(datetime.timedelta(seconds=end - uptime))[:7]
            duration = str(datetime.timedelta(seconds=end - start))[:7]
            print(f'{duration} ({elapsed} since start)')

    print()
