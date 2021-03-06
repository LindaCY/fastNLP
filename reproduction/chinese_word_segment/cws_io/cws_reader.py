

from fastNLP.core.dataset import DataSet
from fastNLP.core.instance import Instance
from fastNLP.io.dataset_loader import DataSetLoader


def cut_long_sentence(sent, max_sample_length=200):
    """
    将长于max_sample_length的sentence截成多段，只会在有空格的地方发生截断。所以截取的句子可能长于或者短于max_sample_length

    :param sent: str.
    :param max_sample_length: int.
    :return: list of str.
    """
    sent_no_space = sent.replace(' ', '')
    cutted_sentence = []
    if len(sent_no_space) > max_sample_length:
        parts = sent.strip().split()
        new_line = ''
        length = 0
        for part in parts:
            length += len(part)
            new_line += part + ' '
            if length > max_sample_length:
                new_line = new_line[:-1]
                cutted_sentence.append(new_line)
                length = 0
                new_line = ''
        if new_line != '':
            cutted_sentence.append(new_line[:-1])
    else:
        cutted_sentence.append(sent)
    return cutted_sentence

class NaiveCWSReader(DataSetLoader):
    """
    这个reader假设了分词数据集为以下形式, 即已经用空格分割好内容了
        这是 fastNLP , 一个 非常 good 的 包 .
    或者,即每个part后面还有一个pos tag
        也/D  在/P  團員/Na  之中/Ng  ，/COMMACATEGORY
    """
    def __init__(self, in_word_splitter=None):
        super().__init__()

        self.in_word_splitter = in_word_splitter

    def load(self, filepath, in_word_splitter=None, cut_long_sent=False):
        """
        允许使用的情况有(默认以\t或空格作为seg)
            这是 fastNLP , 一个 非常 good 的 包 .
        和
            也/D  在/P  團員/Na  之中/Ng  ，/COMMACATEGORY
        如果splitter不为None则认为是第二种情况, 且我们会按splitter分割"也/D", 然后取第一部分. 例如"也/D".split('/')[0]
        :param filepath:
        :param in_word_splitter:
        :return:
        """
        if in_word_splitter == None:
            in_word_splitter = self.in_word_splitter
        dataset = DataSet()
        with open(filepath, 'r') as f:
            for line in f:
                line = line.strip()
                if len(line.replace(' ', ''))==0: # 不能接受空行
                    continue

                if not in_word_splitter is None:
                    words = []
                    for part in line.split():
                        word = part.split(in_word_splitter)[0]
                        words.append(word)
                        line = ' '.join(words)
                if cut_long_sent:
                    sents = cut_long_sentence(line)
                else:
                    sents = [line]
                for sent in sents:
                    instance = Instance(raw_sentence=sent)
                    dataset.append(instance)

        return dataset


class POSCWSReader(DataSetLoader):
    """
    支持读取以下的情况, 即每一行是一个词, 用空行作为两句话的界限.
        迈 N
        向 N
        充 N
        ...
        泽 I-PER
        民 I-PER

        （ N
        一 N
        九 N
        ...


    :param filepath:
    :return:
    """
    def __init__(self, in_word_splitter=None):
        super().__init__()
        self.in_word_splitter = in_word_splitter

    def load(self, filepath, in_word_splitter=None, cut_long_sent=False):
        if in_word_splitter is None:
            in_word_splitter = self.in_word_splitter
        dataset = DataSet()
        with open(filepath, 'r') as f:
            words = []
            for line in f:
                line = line.strip()
                if len(line) == 0: # new line
                    if len(words)==0: # 不能接受空行
                        continue
                    line = ' '.join(words)
                    if cut_long_sent:
                        sents = cut_long_sentence(line)
                    else:
                        sents = [line]
                    for sent in sents:
                        instance = Instance(raw_sentence=sent)
                        dataset.append(instance)
                    words = []
                else:
                    line = line.split()[0]
                    if in_word_splitter is None:
                        words.append(line)
                    else:
                        words.append(line.split(in_word_splitter)[0])
        return dataset


class ConllCWSReader(object):
    def __init__(self):
        pass

    def load(self, path, cut_long_sent=False):
        """
        返回的DataSet只包含raw_sentence这个field，内容为str。
        假定了输入为conll的格式，以空行隔开两个句子，每行共7列，即
            1	编者按	编者按	NN	O	11	nmod:topic
            2	：	：	PU	O	11	punct
            3	7月	7月	NT	DATE	4	compound:nn
            4	12日	12日	NT	DATE	11	nmod:tmod
            5	，	，	PU	O	11	punct

            1	这	这	DT	O	3	det
            2	款	款	M	O	1	mark:clf
            3	飞行	飞行	NN	O	8	nsubj
            4	从	从	P	O	5	case
            5	外型	外型	NN	O	8	nmod:prep
        """
        datalist = []
        with open(path, 'r', encoding='utf-8') as f:
            sample = []
            for line in f:
                if line.startswith('\n'):
                    datalist.append(sample)
                    sample = []
                elif line.startswith('#'):
                    continue
                else:
                    sample.append(line.split('\t'))
            if len(sample) > 0:
                datalist.append(sample)

        ds = DataSet()
        for sample in datalist:
            # print(sample)
            res = self.get_char_lst(sample)
            if res is None:
                continue
            line = ' '.join(res)
            if cut_long_sent:
                sents = cut_long_sentence(line)
            else:
                sents = [line]
            for raw_sentence in sents:
                ds.append(Instance(raw_sentence=raw_sentence))

        return ds

    def get_char_lst(self, sample):
        if len(sample)==0:
            return None
        text = []
        for w in sample:
            t1, t2, t3, t4 = w[1], w[3], w[6], w[7]
            if t3 == '_':
                return None
            text.append(t1)
        return text

