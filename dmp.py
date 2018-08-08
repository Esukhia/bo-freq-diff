from diff_match_patch import diff_match_patch


class DMP(diff_match_patch):
    def __init__(self):
        super().__init__()
        self.word_sep = ' '  # custom defined word separator

    def diff_wordMode(self, text1, text2):
        """
        implements what is proposed here:
        See https://github.com/google/diff-match-patch/wiki/Line-or-Word-Diffs#word-mode
        """
        lineText1, lineText2, lineArray = self.diff_linesToWords(text1, text2)
        diffs = self.diff_main(lineText1, lineText2, False)
        self.diff_charsToLines(diffs, lineArray)
        return diffs

    def diff_linesToWords(self, text1, text2):
        """
        a copy of diff_linesToChars that redefines the linebreak character
        to self.word_sep
        """
        lineArray = []
        lineHash = {}

        lineArray.append('')

        def diff_linesToCharsMunge(text):
            chars = []
            lineStart = 0
            lineEnd = -1
            while lineEnd < len(text) - 1:
                lineEnd = text.find(self.word_sep, lineStart)
                if lineEnd == -1:
                    lineEnd = len(text) - 1
                line = text[lineStart:lineEnd + 1]
                lineStart = lineEnd + 1

                if line in lineHash:
                    chars.append(chr(lineHash[line]))
                else:
                    lineArray.append(line)
                    lineHash[line] = len(lineArray) - 1
                    chars.append(chr(len(lineArray) - 1))
            return "".join(chars)

        chars1 = diff_linesToCharsMunge(text1)
        chars2 = diff_linesToCharsMunge(text2)
        return chars1, chars2, lineArray


if __name__ == '__main__':
    dmp = DMP()

    orig = 'བཀྲ་ ཤིས་ བདེ་ ལེགས།'
    new = 'བཀྲ་ ཤས་ བདེ་ ལེག།'
    diffs = dmp.diff_wordMode(orig, new)
    print(diffs)
    # [(0, 'བཀྲ་ '), (-1, 'ཤིས་ '), (1, 'ཤས་ '), (0, 'བདེ་ '), (-1, 'ལེགས།'), (1, 'ལེག།')]
