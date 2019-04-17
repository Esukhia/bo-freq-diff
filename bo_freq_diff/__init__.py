from .dmp import DMP
from .segmentdiff import SegmentDiff
from .ordereddiff import OrderedDiff
from .sentenceordereddiff import SentenceOrderedDiff
from pathlib import Path


def diff_one_file(filename1, filename2, outfile=Path('test.csv')):
    return_mark = '–'
    space_mark = '_'
    content1 = filename1.read_text(encoding='utf-8-sig').replace('\n', return_mark).replace(' ', space_mark)
    content2 = filename2.read_text(encoding='utf-8-sig').replace('\n', return_mark).replace(' ', space_mark)
    od = OrderedDiff(content1, content2)
    joined_out = od.export_diffs()
    od.write_to_csv(joined_out, outfile)
