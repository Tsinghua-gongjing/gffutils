import tempfile
from nose.tools import assert_raises
from .. import parser
from .. import constants
from .. import helpers
from ..__init__ import example_filename
import attr_test_cases

TEST_FILENAMES = [example_filename(i) for i in [
    'c_elegans_WS199_ann_gff.txt',
    'ensembl_gtf.txt',
    'hybrid1.gff3',
    'ncbi_gff3.txt',
    'c_elegans_WS199_dna_shortened.fa',
    'F3-unique-3.v2.gff',
    'jgi_gff2.txt',
    'wormbase_gff2_alt.txt',
    'c_elegans_WS199_shortened_gff.txt',
    'glimmer_nokeyval.gff3',
    'mouse_extra_comma.gff3',
    'wormbase_gff2.txt']]


def test_split_attrs():
    # nosetests generator for all the test cases in attr_test_cases.  (note no
    # docstring for this test function so that nosetests -v will print the test
    # cases)
    for (attr_str, attr_dict, acceptable_reconstruction) \
            in attr_test_cases.attrs:
        yield attrs_OK, attr_str, attr_dict, acceptable_reconstruction


def attrs_OK(attr_str, attr_dict, acceptable_reconstruction=None):
    """
    Given an attribute string and a dictionary of what you expect, test the
    attribute splitting and reconstruction (invariant roundtrip).

    There are some corner cases for the roundtrip invariance that don't work
    (see attr_test_cases.py for details); `acceptable_reconstruction` handles
    those.
    """
    result, dialect = parser._split_keyvals(attr_str)
    assert result == attr_dict, result

    reconstructed = parser._reconstruct(result, dialect)
    if acceptable_reconstruction:
        assert reconstructed == acceptable_reconstruction, reconstructed
    else:
        assert reconstructed == attr_str, reconstructed


def parser_smoke_test():
    """
    Just confirm we can iterate completely through the test files....
    """
    # Don't show the warnings for tests
    import logging
    parser.logger.setLevel(logging.CRITICAL)
    for filename in TEST_FILENAMES:
        p = parser.Parser(filename)
        for i in p:
            continue

def test_empty_recontruct():
    """
    reconstructing attributes with incomplete information returns empty string
    """
    assert parser._reconstruct(None, constants.dialect) == ""
    assert_raises(helpers.AttributeStringError, parser._reconstruct, dict(ID='asdf'), None)
    assert_raises(helpers.AttributeStringError, parser._reconstruct, None, None)

def test_empty_split_keyvals():
    assert parser._split_keyvals(keyval_str=None) == helpers.DefaultOrderedDict(list)

def test_repeated_keys_conflict():
    """
    if dialect says repeated keys, but len(vals) > 1, then the keys are not
    actually repeated....
    """
    dialect = constants.dialect.copy()
    dialect['repeated keys'] = True
    assert_raises(helpers.AttributeStringError, parser._split_keyvals, "Parent=1,2,3", dialect)

def test_parser_from_string():
    """
    make sure from string and from file return identical results
    """
    line = "chr2L	FlyBase	exon	7529	8116	.	+	.	Name=CG11023:1;Parent=FBtr0300689,FBtr0300690"
    tmp = tempfile.NamedTemporaryFile()
    tmp.write(line)
    tmp.seek(0)

    p1 = parser.Parser(
        "chr2L	FlyBase	exon	7529	8116	.	+	.	Name=CG11023:1;Parent=FBtr0300689,FBtr0300690",
        from_string=True)
    p2 = parser.Parser(tmp.name)
    lines = zip(p1, p2)
    assert len(lines) == 1
    assert p1.current_line_number == p2.current_line_number == 0
    assert lines[0][0] == lines[0][1]


def test_checklines_limit():
    fn = example_filename('ensembl_gtf.txt')
    p = parser.Parser(fn, checklines=1)
    p._sniff()

def test_valid_line_count():
    p = parser.Parser(example_filename('ncbi_gff3.txt'))
    assert p._valid_line_count() == 17

    p = parser.Parser(example_filename('hybrid1.gff3'))
    assert p._valid_line_count() == 6

    p = parser.Parser(example_filename('FBgn0031208.gff'))
    assert p._valid_line_count() == 27