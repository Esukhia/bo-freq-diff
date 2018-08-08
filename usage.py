from bo_freq_diff import *

orig = 'བཀྲ་ ཤིས་ བདེ་ ལེགས།'
new = 'བཀྲ་ ཤས་ བདེ་ ལེག།'

dmp = DMP()
diffs = dmp.diff_wordMode(orig, new)
print(diffs)
# [(0, 'བཀྲ་ '), (-1, 'ཤིས་ '), (1, 'ཤས་ '), (0, 'བདེ་ '), (-1, 'ལེགས།'), (1, 'ལེག།')]


sd = SyllableDiff()
orig = 'བཀྲ་ཤས་བདེ་ལེག།'
new = 'བཀྲ་ཤིས་བདེ་ལེགས།'
diffs = sd.diff(orig, new)
print(diffs)
# ['བཀྲ་ ', {'-': 'ཤས་ ', '+': 'ཤིས་ '}, 'བདེ་ ', {'-': 'ལེག ', '+': 'ལེགས '}, '།']


od = OrderedDiff(orig, new)
out = od.export_diffs()
print(out)
# [('1: -ཤས་+ཤིས་', '', '', '', ''),
#  ('', 'བཀྲ་', 'ཤས་', 'ཤིས་', 'བདེ་ལེགས།'),
#  ('1: -ལེག+ལེགས', '', '', '', ''),
#  ('', 'བཀྲ་ཤིས་བདེ་', 'ལེག', 'ལེགས', '།')]
od.write_to_csv('test.csv', out)
# title,left,original,new,left
# 1: -ཤས་+ཤིས་,,,,
# ,བཀྲ་,ཤས་,ཤིས་,བདེ་ལེགས།
# 1: -ལེག+ལེགས,,,,
# ,བཀྲ་ཤིས་བདེ་,ལེག,ལེགས,།

