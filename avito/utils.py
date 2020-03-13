from os import path, makedirs
from traceback import format_exception
from sys import stdout
from datetime import datetime


def format_string(_string, mask='', substitute=''):
    if mask:
        for symbol in mask:
            _string = _string.replace(symbol, substitute)
    return _string


def wrap(both=None, before=None, after=None):
    def taker(func):
        def wrapper(*args, **kwargs):
            if both:
                both()
            if before:
                before()
            result = func(*args, **kwargs)
            if after:
                after()
            if both:
                both()
            return result
        return wrapper
    return taker


@wrap(both=lambda: print('-' * 50))
def log(*args, sep=' ', end='\n', file=stdout, **kwargs):
    '''Custom print function to distinct app's console output from other's.'''
    for i, arg in enumerate(args):
        if 'traceback object' not in str(args[i]):
            print(args[i], end=sep if i != len(args)-1 else end, **kwargs)
        else:
            print(*format_exception(*arg), sep=end, **kwargs)


def find_longest(_string, char):
    longest = 0
    count = 0
    for c in _string:
        if c == char:
            count += 1
        else:
            longest = max(longest, count)
            count = 0
    return longest


def url_to_filename(url, mask='', substitute='', ext='', _os='win'):
    '''Setting up proper filename based on user url and os.'''
    _mask = {
        '': '',
        'win': r'\/:*?<>|"',  # banned characters
        'mac': '',
        'linux': ''
    }
    filename = url + (('.' + ext) * bool(ext))
    if not mask:
        mask = _mask.get(_os, '')
    filename = format_string(filename, mask, substitute)
    longest = find_longest(filename, substitute)
    if longest > 1:
        for i in range(longest, 1, -1):
            filename = filename.replace(substitute * i, substitute)
    if filename.endswith(substitute):
        filename = filename[:-1]
    return filename


def get_fullpath(filepath, check=True):
    '''Creates fullpath to file. Checks path existance / creates missing directories if check=True'''
    fullpath = path.abspath(filepath)
    if check:
        if not path.exists(fullpath):
            dirs = path.dirname(fullpath)
            if not path.exists(dirs):
                makedirs(dirs)
                raise Exception(
                    f'Не удается найти файл по указанному пути {fullpath}. Создаю директории.')
    return fullpath


def read_data(filepath):
    fullpath = get_fullpath(filepath)
    with open(fullpath, 'r', encoding='utf-8') as file:
        data = file.read()
        return data


def write_data(filepath, data, mode='w'):
    fullpath = get_fullpath(filepath)
    with open(fullpath, mode, encoding='utf-8') as file:
        file.write(data)


def load_data(filepath):
    data = ''
    try:
        return read_data(filepath)
    except IOError as e:
        log(e, '\nСоздаю новый файл.')
        write_data(filepath, '')
        return data


def save_data(filepath, data, end='\n'):
    if data not in load_data(filepath):
        write_data(filepath, data + end, mode='a')


def erase_data(filepath):
    if load_data(filepath):
        write_data(filepath, '')


def save_error(*args, **kwargs):
    '''saving error report after max tries in retry decorator been reached'''
    date = str(datetime.now())
    with open('errors.txt', 'a', encoding='utf-8') as file:
        log(date, *args, file=file, **kwargs)


def format_csv_data(data, strip=True, hyphens='', delim=(';', ' '), newline=('\n', '  ')):
    _string = ''
    if data:
        _string = data.strip() if strip else data
    for symbol, substitute in [delim, newline]:
        if symbol in _string:
            _string = _string.replace(symbol, substitute)
    _string = hyphens + _string + hyphens
    return _string


def save_data_to_csv(columns, data, filename, delim=';', newline='\n'):
    '''Saving data to csv in following format (a;b;c\nd;e;f)'''
    log(f'Сохранение данных в csv файл.')
    output = ''
    if not load_data(filename):
        output = delim.join(columns) + newline
    if data:
        output += delim.join([format_csv_data(data.get(key, ''))
                          for key in columns]) + newline
    save_data(filename, output, end='')
