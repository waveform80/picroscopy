# vim: set et sw=4 sts=4:

"""Installation utility functions"""

import io
import re

def get_version(filename):
    """
    Trivial parser to extract a __version__ variable from a source file.

    :param str filename: the file to extract __version__ from
    :returns str: the version string for the package
    """
    version_re = re.compile(r'(\d\.\d(\.\d+)?)')
    with io.open(filename, 'r') as source:
        for line_num, line in enumerate(source):
            if line.startswith('__version__'):
                match = version_re.search(line)
                if not match:
                    raise Exception(
                        'Invalid __version__ string found on '
                        'line %d of %s' % (line_num + 1, filename))
                return match.group(1)
    raise Exception('No __version__ line found in %s' % filename)

def description(filename):
    """
    Returns the first non-heading paragraph from a ReStructuredText file.

    :param str filename: the file to extract the description from
    :returns str: the description of the package
    """
    state = 'before_header'
    result = []
    # We use a simple DFA to parse the file which looks for blank, non-blank,
    # and heading-delimiter lines.
    with io.open(filename, 'r') as rst_file:
        for line in rst_file:
            line = line.rstrip()
            # Manipulate state based on line content
            if line == '':
                if state == 'in_para':
                    state = 'after_para'
            elif line == '=' * len(line):
                if state == 'before_header':
                    state = 'in_header'
                elif state == 'in_header':
                    state = 'before_para'
            else:
                if state == 'before_para':
                    state = 'in_para'
            # Carry out state actions
            if state == 'in_para':
                result.append(line)
            elif state == 'after_para':
                break
    return ' '.join(line.strip() for line in result)

