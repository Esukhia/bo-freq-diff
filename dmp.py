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
        note: all names containing "line" have been renamed to "word"
        """
        wordArray = []
        wordHash = {}

        wordArray.append('')

        def diff_wordsToCharsMunge(text):
            chars = []
            wordStart = 0
            wordEnd = -1
            while wordEnd < len(text) - 1:
                wordEnd = text.find(self.word_sep, wordStart)
                if wordEnd == -1:
                    wordEnd = len(text) - 1
                word = text[wordStart:wordEnd + 1]
                wordStart = wordEnd + 1

                if word in wordHash:
                    chars.append(chr(wordHash[word]))
                else:
                    wordArray.append(word)
                    wordHash[word] = len(wordArray) - 1
                    chars.append(chr(len(wordArray) - 1))
            return "".join(chars)

        chars1 = diff_wordsToCharsMunge(text1)
        chars2 = diff_wordsToCharsMunge(text2)
        return chars1, chars2, wordArray


if __name__ == '__main__':
    dmp = DMP()

    orig = 'བཀྲ་ ཤིས་ བདེ་ ལེགས།'
    new = 'བཀྲ་ ཤས་ བདེ་ ལེག།'
    diffs = dmp.diff_wordMode(orig, new)
    print(diffs)
    # [(0, 'བཀྲ་ '), (-1, 'ཤིས་ '), (1, 'ཤས་ '), (0, 'བདེ་ '), (-1, 'ལེགས།'), (1, 'ལེག།')]
