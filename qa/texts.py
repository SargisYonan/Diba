"""Sample text for the proofs: the alphabet, words, the Lord's Prayer, and
the same with East Syriac vowels."""

ALPHABET = "ܐܒܓܕܗܘܙܚܛܝܟܠܡܢܣܥܦܨܩܪܫܬ"

WORDS = """ܫܠܡܐ ܐܬܘܪܝܐ ܣܘܪܝܝܐ ܟܬܒܐ ܥܠܡܐ ܡܠܟܐ ܐܠܗܐ ܕܝܒܐ ܢܘܗܪܐ ܒܪܢܫܐ
ܡܕܢܚܐ ܥܕܬܐ ܠܫܢܐ ܣܦܪܐ ܦܬܓܡܐ ܨܠܘܬܐ ܛܘܒܐ ܙܒܢܐ ܓܢܬܐ ܩܠܐ ܚܘܒܐ
ܡܝܐ ܝܘܡܐ ܠܠܝܐ ܐܪܥܐ ܫܡܝܐ ܩܕܝܫܐ ܚܝܐ ܒܝܬ ܢܗܪܝܢ""".split()

PRAYER = ("ܐܒܘܢ ܕܒܫܡܝܐ ܢܬܩܕܫ ܫܡܟ ܬܐܬܐ ܡܠܟܘܬܟ ܢܗܘܐ ܨܒܝܢܟ ܐܝܟܢܐ ܕܒܫܡܝܐ "
          "ܐܦ ܒܐܪܥܐ ܗܒ ܠܢ ܠܚܡܐ ܕܣܘܢܩܢܢ ܝܘܡܢܐ ܘܫܒܘܩ ܠܢ ܚܘܒܝܢ ܘܚܛܗܝܢ "
          "ܐܝܟܢܐ ܕܐܦ ܚܢܢ ܫܒܩܢ ܠܚܝܒܝܢ ܘܠܐ ܬܥܠܢ ܠܢܣܝܘܢܐ ܐܠܐ ܦܨܢ ܡܢ ܒܝܫܐ")

# Punctuation in use: a sentence ending, a pause, a paragraph end.
PUNCTUATED = ("ܐܒܘܢ ܕܒܫܡܝܐ. ܢܬܩܕܫ ܫܡܟ: ܬܐܬܐ ܡܠܟܘܬܟ܁ ܢܗܘܐ ܨܒܝܢܟ܂ "
              "ܐܝܟܢܐ ܕܒܫܡܝܐ܅ ܐܦ ܒܐܪܥܐ܀")


# Vowelled text is written with ASCII stand-ins for the marks, which are hard
# to type and to read in source: a ptaha, A zqapa, e zlama psiqa, E zlama
# qashya, i/u hbasa-esasa (under Yudh/Waw), o rwaha, q qushshaya, r rukkakha,
# s syame.
MARK_KEYS = {"a": "\u0732", "A": "\u0735", "e": "\u0738", "E": "\u0739", "i": "\u073C",
             "u": "\u073C", "o": "\u073F", "q": "\u0741", "r": "\u0742", "s": "\u0308"}


def vowel(text):
    return "".join(MARK_KEYS.get(ch, ch) for ch in text)


VOWELLED_WORDS = [vowel(w) for w in """ܫܠAܡAܐ ܐAܬrܘoܪAܝAܐ ܣܘuܪAܝAܐ ܟܬrAܒrAܐ ܟܬrAܒrEsܐ
ܡaܠܟAܐ ܡaܠܟEsܐ ܥAܠܡAܐ ܐaܠAܗAܐ ܕEܐܒrAܐ ܢܘuܗܪAܐ ܝAܘܡAܐ ܠeܠܝAܐ ܡaܕܢܚAܐ
ܥEܕܬrAܐ ܠeܫAܢAܐ ܣeܦܪEsܐ ܨܠܘoܬrAܐ ܛܘoܒrAܐ ܚܘuܒAܐ ܡaܝAܐ ܩaܕܝiܫAܐ ܚaܝEsܐ
ܟqaܠܒqAܐ ܒܝiܬ ܢaܗܪܝiܢ""".split()]

VOWELLED_PRAYER = vowel(
    "ܐaܒܘuܢ ܕܒaܫܡaܝAܐ ܢeܬܩaܕaܫ ܫܡAܟr ܬEܐܬEܐ ܡaܠܟܘuܬrAܟr ܢeܗܘEܐ ܨeܒܝAܢAܟr "
    "ܐaܝܟaܢAܐ ܕܒaܫܡaܝAܐ ܐAܦ ܒܐaܪܥAܐ ܗaܒ ܠaܢ ܠaܚܡAܐ ܕܣܘuܢܩAܢaܢ ܝAܘܡAܢAܐ "
    "ܘaܫܒܘoܩ ܠaܢ ܚAܘܒaܝܢ ܘܚAܛAܗaܝܢ ܐaܝܟaܢAܐ ܕܐAܦ ܚܢaܢ ܫܒaܩܢ ܠܚaܝAܒaܝܢ "
    "ܘܠAܐ ܬaܥܠaܢ ܠܢeܣܝܘoܢAܐ ܐeܠAܐ ܦaܨAܢ ܡeܢ ܒܝiܫAܐ")
