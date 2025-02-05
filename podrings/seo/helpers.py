import string


SMALL_WORDS = (
    'a', 'an', 'and', 'as', 'at',
    'by',
    'for',
    'if', 'in', 'is', 'it',
    'of', 'on', 'or',
    'the', 'to'
)


PUNCTUATION = string.punctuation + '“”'


def strip_punctuation(word):
    chars = ''

    for char in word:
        if char not in PUNCTUATION:
            chars += char

    return chars


def capitalise(word):
    chars = ''
    capitalised = False

    for char in word:
        if capitalised or char in PUNCTUATION:
            chars += char
            continue

        chars += char.upper()
        capitalised = True

    return chars


def title_case(text):
    if not text:
        return ''

    words = []
    for word in str(text).split():
        if not any(words):
            words.append(word)
            continue

        stripped_word = strip_punctuation(word)

        if stripped_word == stripped_word.lower():
            if stripped_word not in SMALL_WORDS:
                words.append(capitalise(word))
                continue

        words.append(word)

    return ' '.join(words)
