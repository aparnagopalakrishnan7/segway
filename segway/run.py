#!/usr/bin/env python
from __future__ import division, with_statement

"""
run: DESCRIPTION
"""

__version__ = "$Revision$"

# Copyright 2008 Michael M. Hoffman <mmh1@washington.edu>

from cStringIO import StringIO
from contextlib import closing, contextmanager
from copy import copy
from errno import EEXIST, ENOENT
from functools import partial
from itertools import count, izip
from math import ceil, floor, frexp, ldexp, log10
from os import extsep, getpid
from shutil import move
from string import Template
import sys
from threading import Event, Thread

from DRMAA import ExitTimeoutError, Session as _Session
from numpy import (add, amin, amax, append, arange, array, column_stack, diag,
                   empty, finfo, float32, fromfile, intc, invert, isnan,
                   newaxis, NINF, outer, s_, square, tile, vectorize)
from numpy.random import uniform
from optbuild import (Mixin_NoConvertUnderscore,
                      OptionBuilder_ShortOptWithSpace,
                      OptionBuilder_ShortOptWithSpace_TF)
from path import path

from ._util import (data_filename, data_string, DTYPE_IDENTIFY, DTYPE_OBS_INT,
                    EXT_GZ, fill_array, find_segment_starts, get_tracknames,
                    gzip_open, iter_chroms_coords, load_coords,
                    NamedTemporaryDir, PKG, walk_continuous_supercontigs,
                    walk_supercontigs)

# XXX: I should really get some sort of Enum for this, I think Peter
# Norvig has one
DISTRIBUTION_NORM = "norm"
DISTRIBUTION_GAMMA = "gamma"
DISTRIBUTIONS = [DISTRIBUTION_NORM, DISTRIBUTION_GAMMA]
DISTRIBUTION_DEFAULT = DISTRIBUTION_NORM

## XXX: should be options
MEAN_METHOD_UNIFORM = "uniform" # randomly pick from the range
MEAN_METHOD_ML_JITTER = "ml_jitter" # maximum likelihood, then jitter
MEAN_METHODS = [MEAN_METHOD_UNIFORM, MEAN_METHOD_ML_JITTER]
MEAN_METHOD = MEAN_METHOD_UNIFORM

COVAR_METHOD_MAX_RANGE = "max_range" # maximum range
COVAR_METHOD_ML_JITTER = "ml_jitter" # maximum likelihood, then jitter
COVAR_METHODS = [COVAR_METHOD_MAX_RANGE, COVAR_METHOD_ML_JITTER]
COVAR_METHOD = COVAR_METHOD_MAX_RANGE

PARAM_METHOD_ML_JITTER = "ml_jitter"
PARAM_METHOD_MEAN_RANDOM_VAR_MAX = "mean_random_var_max"
PARAM_METHOD = PARAM_METHOD_MEAN_RANDOM_VAR_MAX

NUM_SEGS = 2 # XXX: to change, will require CARD_SEG to be set
MAX_EM_ITERS = 100
TEMPDIR_PREFIX = PKG + "-"
COVAR_TIED = True # would need to expand to MC, MX to change
MAX_CHUNKS = 1000
ISLAND = False
SESSION_WAIT_TIMEOUT = 60 # seconds
JOIN_TIMEOUT = finfo(float).max
LEN_SEG_EXPECTED = 10000
SWAP_ENDIAN = False

## option defaults
VERBOSITY = 0
PRIOR_STRENGTH = 0

DRMSINFO_PREFIX = "GE" # XXX: only SGE is supported for now

FINFO_FLOAT32 = finfo(float32)
MACHEP_FLOAT32 = FINFO_FLOAT32.machep
TINY_FLOAT32 = FINFO_FLOAT32.tiny

FUDGE_EP = -17 # ldexp(1, -17) = ~1e-6
assert FUDGE_EP > MACHEP_FLOAT32

# binary
JITTER_ORDERS_MAGNITUDE = 5 # log10(2**5) = 1.5 decimal orders of magnitude

FUDGE_TINY = -ldexp(TINY_FLOAT32, 6)
ABSOLUTE_FUDGE = 0.001

LOG_LIKELIHOOD_DIFF_FRAC = 1e-5

ORD_A = ord("A")
ORD_C = ord("C")
ORD_G = ord("G")
ORD_T = ord("T")
ORD_a = ord("a")
ORD_c = ord("c")
ORD_g = ord("g")
ORD_t = ord("t")
NUM_SEQ_COLS = 2 # dinucleotide, presence_dinucleotide

# for extra memory savings, set to (False) or (not ISLAND)
COMPONENT_CACHE = True

# number of frames in a segment must be at least number of frames in model
MIN_FRAMES = 2
MAX_FRAMES = 1000000000 # 1 billion
MEM_REQ_PARALLEL = "10.5G"
MEM_REQ_BUNDLE = "500M"
RES_REQ_IDS = ["mem_requested"]
NUM_TRIANGULATION_FRAMES = 3

# linear model for memory requests for number of data columns
MEM_REQS = {1: [3619, 8098728],
            2: [3619, 8098728],
            3: [1553, 16121352],
            4: [5768, 14442884],
            5: [5768, 14442884], # XXX: must correct
            6: [5768, 14442884]}

## defaults
RANDOM_STARTS = 1

# replace NAN with SENTINEL to avoid warnings
# XXX: replace with something negative and outlandish again
SENTINEL = float32(9.87654321)

CPP_DIRECTIVE_FMT = "-D%s=%s"

ACC_FILENAME_FMT = "acc.%s.%s.bin"
GMTK_INDEX_PLACEHOLDER = "@D"
NAME_PLACEHOLDER = "bundle"

# programs
ENV_CMD = "/usr/bin/env"
BASH_CMD = "bash"

BASH_CMDLINE = [BASH_CMD, "--login", "-c"]

TRIANGULATE_PROG = OptionBuilder_ShortOptWithSpace_TF("gmtkTriangulate")
EM_TRAIN_PROG = OptionBuilder_ShortOptWithSpace_TF("gmtkEMtrainNew")
VITERBI_PROG = OptionBuilder_ShortOptWithSpace_TF("gmtkViterbiNew")
NATIVE_SPEC_PROG = (Mixin_NoConvertUnderscore
                    + OptionBuilder_ShortOptWithSpace)() # do not run

NATIVE_SPEC_DEFAULT = dict(w="n")

SPECIAL_TRACKNAMES = ["dinucleotide"]

def extjoin(*args):
    return extsep.join(args)

# extensions and suffixes
EXT_BED = "bed"
EXT_IDENTIFY = "identify.h5"
EXT_JT = "jt"
EXT_LIKELIHOOD = "ll"
EXT_LIST = "list"
EXT_FLOAT = "float32"
EXT_INT = "int"
EXT_OUT = "out"
EXT_PARAMS = "params"
EXT_TAB = "tab"
EXT_TRIFILE = "trifile"

def make_prefix_fmt(num):
    # make sure there are sufficient leading zeros
    return "%%0%dd." % (int(floor(log10(num))) + 1)

PREFIX_LIKELIHOOD = "likelihood"
PREFIX_CHUNK = "chunk"
PREFIX_PARAMS = "params"

# XXX: do not hardcode
PREFIX_SEG_LEN_FMT = "seg%s" % make_prefix_fmt(NUM_SEGS)

SUFFIX_LIST = extsep + EXT_LIST
SUFFIX_OUT = extsep + EXT_OUT
SUFFIX_TRIFILE = extsep + EXT_TRIFILE

BED_FILEBASENAME = extjoin(PKG, EXT_BED, EXT_GZ) # "segway.bed.gz"

# templates and formats
RES_STR_TMPL = "seg.str.tmpl"
RES_INPUT_MASTER_TMPL = "input.master.tmpl"
RES_OUTPUT_MASTER = "output.master"
RES_DONT_TRAIN = "dont_train.list"
RES_INC = "seg.inc"

DIRICHLET_FRAG = "0 dirichlet_seg_seg 2 CARD_SEG CARD_SEG"

# XXX: manually indexing these things is silly
DENSE_CPT_START_SEG_FRAG = "0 start_seg 0 CARD_SEG"
DENSE_CPT_SEG_SEG_FRAG = "1 seg_seg 1 CARD_SEG CARD_SEG"
DENSE_CPT_SEG_DINUCLEOTIDE_FRAG = \
    "2 seg_dinucleotide 1 CARD_SEG CARD_DINUCLEOTIDE"
DIRICHLET_SEG_SEG_FRAG = "DirichletTable dirichlet_seg_seg"

MEAN_TMPL = "$index mean_${seg}_${track} 1 ${rand}"

COVAR_TMPL_TIED = "$index covar_${track} 1 ${rand}"
# XXX: unused
COVAR_TMPL_UNTIED = "$index covar_${seg}_${track} 1 ${rand}"

GAMMASCALE_TMPL = "$index gammascale_${seg}_${track} 1 1 ${rand}"
GAMMASHAPE_TMPL = "$index gammashape_${seg}_${track} 1 1 ${rand}"

MC_NORM_TMPL = "$index 1 COMPONENT_TYPE_DIAG_GAUSSIAN" \
    " mc_norm_${seg}_${track} mean_${seg}_${track} covar_${track}"
MC_GAMMA_TMPL = "$index 1 COMPONENT_TYPE_GAMMA mc_gamma_${seg}_${track}" \
    " ${min_track} gammascale_${seg}_${track} gammashape_${seg}_${track}"
MC_TMPLS = dict(norm=MC_NORM_TMPL,
                gamma=MC_GAMMA_TMPL)

MX_TMPL = "$index 1 mx_${seg}_${track} 1 dpmf_always" \
    " mc_${distribution}_${seg}_${track}"

NAME_COLLECTION_TMPL = "$track_index collection_seg_${track} 2"
NAME_COLLECTION_CONTENTS_TMPL = "mx_${seg}_${track}"

TRACK_FMT = "browser position %s:%s-%s"
FIXEDSTEP_FMT = "fixedStep chrom=%s start=%s step=1 span=1"

# XXX: this could be specified as a dict instead
WIG_HEADER = 'track type=wiggle_0 name=%s ' \
    'description="%s segmentation of %%s" visibility=dense viewLimits=0:1 ' \
    'autoScale=off' % (PKG, PKG)

TRAIN_ATTRNAMES = ["input_master_filename", "params_filename",
                   "log_likelihood_filename"]
LEN_TRAIN_ATTRNAMES = len(TRAIN_ATTRNAMES)

## functions

def vstack_tile(array_like, reps):
    return tile(array_like, (reps, 1))

def extjoin_not_none(*args):
    return extjoin(*[str(arg) for arg in args
                     if arg is not None])

def rewrite_strip_comments(infile, outfile):
    for line in infile:
        inline = line.rstrip()

        if not inline or inline.startswith("%"):
            outline = inline
        else:
            outline = (yield inline)

            if outline is None:
                outline = inline

        print >>outfile, outline

def consume_until(iterable, text):
    for line in iterable:
        if line.startswith(text):
            break

def copy_until(infile, outfile, text):
    for line in infile:
        print >>outfile, line

        if line.startswith(text):
            return

def is_comment(line):
    return line.startswith("%")

# XXX: suggest upstream as addition to DRMAA-python
@contextmanager
def Session(*args, **kwargs):
    res = _Session()
    res.init(*args, **kwargs)

    assert res.DRMSInfo.startswith(DRMSINFO_PREFIX)

    try:
        yield res
    finally:
        res.exit()

def make_res_req(size):
    res = []
    for res_req_id in RES_REQ_IDS:
        res.append("%s=%s" % (res_req_id, size))

    return res

def convert_chunks(attrs, name):
    supercontig_start = attrs.start
    edges_array = getattr(attrs, name) + supercontig_start
    return edges_array.tolist()

def is_training_progressing(last_ll, curr_ll,
                            min_ll_diff_frac=LOG_LIKELIHOOD_DIFF_FRAC):
    # using x !< y instead of x >= y to give the right default answer
    # in the case of NaNs
    return not abs((curr_ll - last_ll)/last_ll) < min_ll_diff_frac

def resource_substitute(resourcename):
    return Template(data_string(resourcename)).substitute

def save_template(filename, resource, mapping, dirname=None,
                  delete_existing=False, start_index=None):
    """
    creates a temporary file if filename is None or empty
    """
    if filename:
        if not delete_existing and path(filename).exists():
            return filename, False
    else:
        resource_part = resource.rpartition(".tmpl")
        stem = resource_part[0] or resource_part[2]
        stem_part = stem.rpartition(extsep)
        prefix = stem_part[0]
        ext = stem_part[2]

        filebasename = extjoin_not_none(prefix, start_index, ext)

        filename = path(dirname) / filebasename

    with open(filename, "w+") as outfile:
        tmpl = Template(data_string(resource))
        text = tmpl.substitute(mapping)

        outfile.write(text)

    return filename, True

def find_overlaps(start, end, coords):
    """
    find items in coords that overlap (start, end)

    NOTE: multiple overlapping regions in coords will result in data
    being considered more than once
    """
    res = []

    for coord_start, coord_end in coords:
        if start > coord_end:
            pass
        elif end <= coord_start:
            pass
        elif start <= coord_start:
            if end >= coord_end:
                res.append([coord_start, coord_end])
            else:
                res.append([coord_start, end])
        elif start > coord_start:
            if end >= coord_end:
                res.append([start, coord_end])
            else:
                res.append([start, end])

    return res

def make_cpp_options(input_params_filename, output_params_filename=None):
    directives = {}

    if input_params_filename:
        directives["INPUT_PARAMS_FILENAME"] = input_params_filename

    if output_params_filename:
        directives["OUTPUT_PARAMS_FILENAME"] = output_params_filename

    res = " ".join(CPP_DIRECTIVE_FMT % item for item in directives.iteritems())

    if res:
        return res

    # default: return None

def make_native_spec(**kwargs):
    options = NATIVE_SPEC_DEFAULT.copy()
    options.update(kwargs)

    res = " ".join(NATIVE_SPEC_PROG.build_args(options=options))

    return res

def make_spec(name, items):
    items[:0] = ["%s_IN_FILE inline" % name, str(len(items)), ""]

    return "\n".join(items) + "\n"

def make_table_spec(frag, table):
    items = [frag] + [" ".join(map(str, row)) for row in table]
    return "\n".join(items) + "\n"

# def make_dt_spec(num_tracks):
#     return make_spec("DT", ["%d seg_obs%d BINARY_DT" % (index, index)
#                             for index in xrange(num_tracks)])

def make_normalized_random_table(num_rows, num_cols):
    random_vals = uniform(size=(num_rows, num_cols))
    random_vals_sums = random_vals.sum(1)[..., newaxis]

    return random_vals / random_vals_sums

def make_random_spec(frag, *args, **kwargs):
    table = make_normalized_random_table(*args, **kwargs)

    return make_table_spec(frag, table)

def prob_transition_from_expected_len(length):
    # formula from Meta-MEME paper, Grundy WN et al. CABIOS 13:397
    return length / (1 + length)

def make_name_collection_spec(num_segs, tracknames):
    substitute = Template(NAME_COLLECTION_TMPL).substitute
    substitute_contents = Template(NAME_COLLECTION_CONTENTS_TMPL).substitute

    items = []

    for track_index, track in enumerate(tracknames):
        mapping = dict(track=track, track_index=track_index)

        contents = [substitute(mapping)]
        for seg_index in xrange(num_segs):
            seg = "seg%d" % seg_index
            mapping = dict(seg=seg, track=track,
                           seg_index=seg_index, track_index=track_index)

            contents.append(substitute_contents(mapping))
        items.append("\n".join(contents))

    return make_spec("NAME_COLLECTION", items)

def load_gmtk_out(filename):
    # gmtkViterbiNew.cc writes things with C sizeof(int) == numpy.intc
    return fromfile(filename, dtype=DTYPE_IDENTIFY)

def write_bed(outfile, start_pos, labels, coords):
    (chrom, region_start, region_end) = coords

    start_pos += region_start

    zipper = zip(start_pos[:-1], start_pos[1:], labels)
    for seg_start, seg_end, seg_label in zipper:
        row = [chrom, str(seg_start), str(seg_end), str(seg_label)]
        print >>outfile, "\t".join(row)

def load_gmtk_out_write_bed((chrom, start, end), gmtk_outfilename, bed_file,
                            tracknames):
    data = load_gmtk_out(gmtk_outfilename)

    start_pos, labels = find_segment_starts(data)

    write_bed(bed_file, start_pos, labels, (chrom, start, end))

def set_cwd_job_tmpl(job_tmpl):
    job_tmpl.workingDirectory = path.getcwd()

def make_dinucleotide_int_data(seq):
    """
    makes an array with two columns, one with 0..15=AA..TT and the other
    as a presence variable. Set column one to 0 when not present
    """
    nucleotide_int_data = (((seq == ORD_A) + (seq == ORD_a))
                           + ((seq == ORD_C) + (seq == ORD_c)) * 2
                           + ((seq == ORD_G) + (seq == ORD_g)) * 3
                           + ((seq == ORD_T) + (seq == ORD_t)) * 4) - 1
    nucleotide_missing = nucleotide_int_data == -1

    # rewrite all Ns as A now that you have the missingness mask
    nucleotide_int_data[nucleotide_int_data == -1] = 0
    col_shape = (len(nucleotide_int_data)-1,)

    # first column: dinucleotide: AA..TT=0..15
    # combine, and add extra AA stub at end, which will be set missing
    # 0 AA AC AG AT
    # 4 CA CC CG CT
    # 8 GA GC GG GT
    # 12 TA TC TG TT
    dinucleotide_int_data = empty(col_shape, DTYPE_OBS_INT)
    add(nucleotide_int_data[:-1] * 4, nucleotide_int_data[1:],
        dinucleotide_int_data)

    # second column: presence_dinucleotide: some missing=0; all present = 1
    # there are so few N boundaries that it is okay to
    # disregard the whole dinucleotide when half is N
    dinucleotide_missing = (nucleotide_missing[:-1] + nucleotide_missing[1:])

    dinucleotide_presence = empty(dinucleotide_missing.shape, DTYPE_OBS_INT)
    invert(dinucleotide_missing, dinucleotide_presence)

    # XXXopt: set these up properly in the first place instead of
    # column_stacking at the end
    return column_stack([dinucleotide_int_data, dinucleotide_presence])

def walk_all_supercontigs(h5file):
    """
    shares interface with walk_continuous_supercontigs()
    """
    for supercontig in walk_supercontigs(h5file):
        yield supercontig, None

def jitter_cell(cell):
    """
    adds some random noise
    """
    # get the binary exponent and subtract JITTER_ORDERS_MAGNITUDE
    # e.g. 3 * 2**10 --> 1 * 2**5
    max_noise = ldexp(1, frexp(cell)[1] - JITTER_ORDERS_MAGNITUDE)

    return cell + uniform(-max_noise, max_noise)

jitter = vectorize(jitter_cell)

def rewrite_cliques(infile, outfile, frame):
    # method
    print >>outfile, infile.next()

    # number of cliques
    orig_num_cliques = int(infile.next())
    print >>outfile, orig_num_cliques + 1

    # original cliques
    zipper = izip(xrange(orig_num_cliques), infile)
    for clique_index, line in zipper:
        print >>outfile, line

    # new clique
    print >>outfile, "%d 1 seg %d" % (orig_num_cliques, frame)

class RandomStartThread(Thread):
    def __init__(self, runner, session, start_index, interrupt_event):
        # keeps it from rewriting variables that will be used
        # later or in a different thread
        self.runner = copy(runner)

        self.session = session
        self.start_index = start_index
        self.interrupt_event = interrupt_event

        Thread.__init__(self)

    def run(self):
        self.runner.session = self.session
        self.runner.start_index = self.start_index
        self.runner.interrupt_event = self.interrupt_event
        self.result = self.runner.run_train_start()

class Runner(object):
    def __init__(self, **kwargs):
        # filenames
        self.h5filenames = None
        self.float_filelistpath = None
        self.int_filelistpath = None

        self.gmtk_include_filename = None
        self.input_master_filename = None
        self.structure_filename = None
        self.triangulation_filename = None
        self.jt_triangulation_filename = None

        self.params_filename = None
        self.dirname = None
        self.is_dirname_temp = False
        self.log_likelihood_filename = None
        self.dont_train_filename = None

        self.dumpnames_filename = None
        self.output_filelistname = None
        self.output_filenames = None

        self.obs_dirname = None
        self.bed_filename = None

        self.include_coords_filename = None

        # data
        # a "chunk" is what GMTK calls a segment
        self.num_chunks = None
        self.chunk_coords = None
        self.mins = None
        self.maxs = None
        self.chunk_mem_reqs = None
        self.tracknames = None

        # variables
        self.num_segs = NUM_SEGS
        self.segnames = ["seg%d" % seg_index for seg_index in xrange(NUM_SEGS)]
        self.random_starts = RANDOM_STARTS
        self.len_seg_strength = PRIOR_STRENGTH
        self.distribution = DISTRIBUTION_DEFAULT

        # flags
        self.delete_existing = False
        self.triangulate = True
        self.train = True # EM train # this should become an int for num_starts
        self.verbosity = VERBOSITY
        self.identify = True # viterbi
        self.dry_run = False
        self.use_dinucleotide = None

        # functions
        self.train_prog = None

        self.__dict__.update(kwargs)

    def load_log_likelihood(self):
        with open(self.log_likelihood_filename) as infile:
            return float(infile.read().strip())

    def load_include_coords(self):
        filename = self.include_coords_filename

        self.include_coords = load_coords(filename)

    def generate_tmpl_mappings(self, segnames=None, tracknames=None):
        if segnames is None:
            segnames = self.segnames

        if tracknames is None:
            tracknames = self.tracknames

        num_tracks = len(tracknames)

        for seg_index, segname in enumerate(segnames):
            for track_index, trackname in enumerate(tracknames):
                yield dict(seg=segname, track=trackname,
                           seg_index=seg_index, track_index=track_index,
                           index=num_tracks*seg_index + track_index,
                           distribution=self.distribution)

    def make_filename(self, *exts):
        filebasename = extjoin_not_none(*exts)

        return self.dirpath / filebasename

    def set_tracknames(self, chromosome):
        # XXXopt: a lot of stuff here repeated for every chromosome
        # unnecessarily
        tracknames = get_tracknames(chromosome)

        # includes specials
        include_tracknames_all = self.include_tracknames

        # XXX: some repetition in next two assignments
        tracknames_all = [trackname
                          for trackname in tracknames + SPECIAL_TRACKNAMES
                          if trackname in include_tracknames_all]

        include_tracknames = frozenset(trackname
                                       for trackname in include_tracknames_all
                                       if trackname not in SPECIAL_TRACKNAMES)

        if include_tracknames:
            indexed_tracknames = ((index, trackname)
                                  for index, trackname in enumerate(tracknames)
                                  if trackname in include_tracknames)

            # redefine tracknames:
            track_indexes, tracknames = zip(*indexed_tracknames)
            track_indexes = array(track_indexes)

            # check that there aren't any missing tracks
            assert len(tracknames) == len(include_tracknames)
        elif include_tracknames_all:
            # there are special tracknames only
            tracknames = []
            track_indexes = array([], intc)
            # XXX: this is too late to keep the file from being opened
            # all this junk should be refactored earlier, it doesn't
            # need to run every contig
            self.float_filelistpath = None
        else:
            track_indexes = arange(len(tracknames))
            tracknames_all = tracknames

        # replace illegal characters in tracknames only, not tracknames_all
        tracknames = [trackname.replace(".", "_") for trackname in tracknames]

        if self.tracknames is None:
            self.tracknames = tracknames
            self.tracknames_all = tracknames_all
            self.track_indexes = track_indexes
        elif (self.tracknames != tracknames
              or (self.track_indexes != track_indexes).any()):
            raise ValueError("all tracknames attributes must be identical")

        return track_indexes

    def set_params_filename(self, start_index=None, new=False):
        # if this is not run and params_filename is
        # unspecified, then it won't be passed to gmtkViterbiNew

        params_filename = self.params_filename
        if not new and params_filename:
            if (not self.delete_existing
                and path(params_filename).exists()):
                # it already exists and you don't want to force regen
                self.train = False
        else:
            self.params_filename = \
                self.make_filename(PREFIX_PARAMS, start_index, EXT_PARAMS)

    def set_log_likelihood_filename(self, start_index=None, new=False):
        if new or not self.log_likelihood_filename:
            self.log_likelihood_filename = \
                self.make_filename(PREFIX_LIKELIHOOD, start_index,
                                   EXT_LIKELIHOOD)

    def make_output_dirpath(self, dirname, start_index):
        res = self.dirpath / "output" / dirname / str(start_index)
        self.make_dir(res)

        return res

    def set_output_dirpaths(self, start_index):
        self.output_dirpath = self.make_output_dirpath("o", start_index)
        self.error_dirpath = self.make_output_dirpath("e", start_index)

    def make_dir(self, dirname):
        dirpath = path(dirname)

        if self.delete_existing:
            # just always try to delete it
            try:
                dirpath.rmtree()
            except OSError, err:
                if err.errno != ENOENT:
                    raise
        try:
            dirpath.makedirs()
        except OSError, err:
            # if the error is because directory exists, but it's
            # empty, then do nothing
            if (err.errno != EEXIST or not dirpath.isdir() or
                dirpath.listdir()):
                raise

    def make_obs_filelistpath(self, ext):
        return self.obs_dirpath / extjoin(ext, EXT_LIST)

    def make_obs_dir(self):
        obs_dirname = self.obs_dirname
        if not obs_dirname:
            self.obs_dirname = obs_dirname = self.dirname

        obs_dirpath = path(obs_dirname)

        try:
            self.make_dir(obs_dirname)
        except OSError, err:
            if not (err.errno == EEXIST and obs_dirpath.isdir()):
                raise

        self.obs_dirpath = obs_dirpath

        self.float_filelistpath = self.make_obs_filelistpath(EXT_FLOAT)
        self.int_filelistpath = self.make_obs_filelistpath(EXT_INT)

    def make_obs_filepath(self, prefix, suffix):
        return self.obs_dirpath / (prefix + suffix)

    def make_obs_filepaths(self, chrom, chunk_index):
        prefix_feature_tmpl = extjoin(chrom, make_prefix_fmt(MAX_CHUNKS))
        prefix = prefix_feature_tmpl % chunk_index

        make_obs_filepath_custom = partial(self.make_obs_filepath, prefix)

        return (make_obs_filepath_custom(EXT_FLOAT),
                make_obs_filepath_custom(EXT_INT))

    def print_obs_filepaths(self, float_filelist, int_filelist,
                            *args, **kwargs):
        float_filepath, int_filepath = self.make_obs_filepaths(*args, **kwargs)
        print >>float_filelist, float_filepath
        print >>int_filelist, int_filepath

        return float_filepath, int_filepath

    def save_resource(self, resname):
        orig_filename = data_filename(resname)

        if self.is_dirname_temp:
            return orig_filename
        else:
            orig_filepath = path(orig_filename)
            dirpath = self.dirpath

            orig_filepath.copy(dirpath)
            return dirpath / orig_filepath.name

    def save_include(self):
        self.gmtk_include_filename = self.save_resource(RES_INC)

    def save_structure(self):
        observation_sub = resource_substitute("observation.tmpl")

        tracknames = self.tracknames
        num_tracks = self.num_tracks

        observation_items = []
        for track_index, track in enumerate(tracknames):
            item = observation_sub(track=track, track_index=track_index,
                                   presence_index=num_tracks+track_index)
            observation_items.append(item)

        if self.use_dinucleotide:
            dinucleotide_sub = resource_substitute("dinucleotide.tmpl")

            item = dinucleotide_sub(dinucleotide_index=num_tracks*2,
                                    presence_index=num_tracks*2+1)
            observation_items.append(item)

        assert observation_items # must be at least one track
        observations = "\n".join(observation_items)

        mapping = dict(include_filename=self.gmtk_include_filename,
                       observations=observations)

        self.structure_filename, self.structure_filename_new = \
            save_template(self.structure_filename, RES_STR_TMPL, mapping,
                          self.dirname, self.delete_existing)

    def save_observations_chunk(self, float_filepath, int_filepath, float_data,
                                seq_data):
        # input function in GMTK_ObservationMatrix.cc:
        # ObservationMatrix::readBinSentence

        # input per frame is a series of float32s, followed by a series of
        # int32s it is better to optimize both sides here by sticking all
        # the floats in one file, and the ints in another one
        if float_data is None:
            int_data = None
        else:
            mask_missing = isnan(float_data)

            # output -> int_data
            # done in two steps so I can specify output type
            int_data = empty(mask_missing.shape, DTYPE_OBS_INT)
            invert(mask_missing, int_data)

            float_data[mask_missing] = SENTINEL

            float_data.tofile(float_filepath)

        if seq_data is not None:
            extra_int_data = make_dinucleotide_int_data(seq_data)

            # XXXopt: use the correctly sized matrix in the first place
            if int_data is None:
                int_data = extra_int_data
            else:
                int_data = column_stack([int_data, extra_int_data])

        int_data.tofile(int_filepath)

    def accum_metadata(self, mins, maxs, sums, sums_squares, num_datapoints):
        if self.mins is None:
            self.mins = mins
            self.maxs = maxs
            self.sums = sums
            self.sums_squares = sums_squares
            self.num_datapoints = num_datapoints
        else:
            self.mins = amin([mins, self.mins], 0)
            self.maxs = amax([maxs, self.maxs], 0)
            self.sums += sums
            self.sums_squares += sums_squares
            self.num_datapoints += num_datapoints

    def accum_metadata_chromosome(self, chromosome):
        """
        accumulate metadata for a chromsome to the Runner instance

        returns True if there is metadata
        returns False if there is not
        """

        chromosome_attrs = chromosome.root._v_attrs

        try:
            mins = chromosome_attrs.mins
            maxs = chromosome_attrs.maxs
            sums = chromosome_attrs.sums
            sums_squares = chromosome_attrs.sums_squares
            num_datapoints = chromosome_attrs.num_datapoints
        except AttributeError:
            # this means there is no data for that chromosome
            return False

        self.accum_metadata(mins, maxs, sums, sums_squares, num_datapoints)

        return True

    def write_observations(self, float_filelist, int_filelist):
        include_coords = self.include_coords

        # observations
        print_obs_filepaths_custom = partial(self.print_obs_filepaths,
                                             float_filelist, int_filelist)
        save_observations_chunk = self.save_observations_chunk
        delete_existing = self.delete_existing

        num_tracks = None # this is before any subsetting
        chunk_index = 0
        chunk_coords = []
        num_bases = 0

        use_dinucleotide = "dinucleotide" in self.include_tracknames

        chrom_iterator = iter_chroms_coords(self.h5filenames, include_coords)
        for chrom, filename, chromosome, chr_include_coords in chrom_iterator:
            assert not chromosome.root._v_attrs.dirty

            # if there is no metadata, then skip the chromosome
            if not self.accum_metadata_chromosome(chromosome):
                continue

            track_indexes = self.set_tracknames(chromosome)
            num_tracks = len(track_indexes)

            # observations
            if num_tracks:
                supercontig_walker = walk_continuous_supercontigs(chromosome)
            else:
                supercontig_walker = walk_all_supercontigs(chromosome)

            for supercontig, continuous in supercontig_walker:
                assert continuous is None or continuous.shape[1] >= num_tracks

                supercontig_attrs = supercontig._v_attrs
                supercontig_start = supercontig_attrs.start

                convert_chunks_custom = partial(convert_chunks,
                                                supercontig_attrs)

                if continuous is None:
                    starts = [supercontig_start]
                    ends = [supercontig_attrs.end]
                else:
                    starts = convert_chunks_custom("chunk_starts")
                    ends = convert_chunks_custom("chunk_ends")

                ## iterate through chunks and write
                ## izip so it can be modified in place
                for start, end in izip(starts, ends):
                    if include_coords:
                        overlaps = find_overlaps(start, end,
                                                 chr_include_coords)
                        len_overlaps = len(overlaps)

                        if len_overlaps == 0:
                            continue
                        elif len_overlaps == 1:
                            start, end = overlaps[0]
                        else:
                            for overlap in overlaps:
                                starts.append(overlap[0])
                                ends.append(overlap[1])
                            continue

                    num_frames = end - start
                    if not MIN_FRAMES <= num_frames <= MAX_FRAMES:
                        text = " skipping segment of length %d" % num_frames
                        print >>sys.stderr, text
                        continue

                    # start: relative to beginning of chromosome
                    # chunk_start: relative to the beginning of
                    # the supercontig
                    chunk_start = start - supercontig_start
                    chunk_end = end - supercontig_start
                    chunk_coords.append((chrom, start, end))

                    float_filepath, int_filepath = \
                        print_obs_filepaths_custom(chrom, chunk_index)

                    print >>float_filelist, float_filepath
                    print >>int_filelist, int_filepath
                    print >>sys.stderr, " %s (%d, %d)" % (float_filepath,
                                                          start, end)

                    num_bases += end - start

                    # if they don't both exist
                    if not (float_filepath.exists() and int_filepath.exists()):
                        # read rows first into a numpy.array because
                        # you can't do complex imports on a
                        # numpy.Array
                        if continuous is None:
                            cells = None
                        else:
                            min_col = track_indexes.min()
                            max_col = track_indexes.max() + 1
                            col_slice = s_[min_col:max_col]

                            rows = continuous[chunk_start:chunk_end, col_slice]

                            # correct for min_col offset
                            cells = rows[..., track_indexes - min_col]

                        if use_dinucleotide:
                            seq = supercontig.seq
                            len_seq = len(seq)

                            if chunk_end < len_seq:
                                seq_cells = seq[chunk_start:chunk_end+1]
                            elif chunk_end == len(seq):
                                seq_chunk = seq[chunk_start:chunk_end]
                                seq_cells = append(seq_chunk, ord("N"))
                            else:
                                raise ValueError("sequence too short for"
                                                 " supercontig")
                        else:
                            seq_cells = None

                        save_observations_chunk(float_filepath, int_filepath,
                                                cells, seq_cells)

                    chunk_index += 1

        self.num_tracks = num_tracks

        self.use_dinucleotide = use_dinucleotide
        if use_dinucleotide:
            self.num_int_cols = num_tracks + NUM_SEQ_COLS
        else:
            self.num_int_cols = num_tracks

        self.num_chunks = chunk_index
        self.num_bases = num_bases
        self.chunk_coords = chunk_coords

    def open_writable_or_dummy(self, filepath):
        if not filepath or (not self.delete_existing and filepath.exists()):
            return closing(StringIO()) # dummy output
        else:
            return open(filepath, "w")

    def save_observations(self):
        open_writable_or_dummy = self.open_writable_or_dummy

        with open_writable_or_dummy(self.float_filelistpath) as float_filelist:
            with open_writable_or_dummy(self.int_filelistpath) as int_filelist:
                self.write_observations(float_filelist, int_filelist)

    def calc_means_vars(self):
        num_datapoints = self.num_datapoints
        means = self.sums / num_datapoints

        # this is an unstable way of calculating the variance,
        # but it should be good enough
        # Numerical Recipes in C, Eqn 14.1.7
        # XXX: best would be to switch to the pairwise parallel method
        # (see Wikipedia)

        self.means = means
        self.vars = (self.sums_squares / num_datapoints) - square(means)

    def get_track_lt_min(self, track_index):
        """
        returns a value less than a minimum in a track
        """
        # XXX: refactor into a new function
        min_track = self.mins[track_index]

        # fudge the minimum by a very small amount. this is not
        # continuous, but hopefully we won't get values where it
        # matters
        # XXX: restore this after GMTK issues fixed
        # if min_track == 0.0:
        #     min_track_fudged = FUDGE_TINY
        # else:
        #     min_track_fudged = min_track - ldexp(abs(min_track), FUDGE_EP)

        # this happens for really big numbers or really small
        # numbers; you only have 7 orders of magnitude to play
        # with on a float32
        min_track_f32 = float32(min_track)

        assert min_track_f32 - float32(ABSOLUTE_FUDGE) != min_track_f32
        return min_track - ABSOLUTE_FUDGE

    def make_items_multiseg(self, tmpl, data=None, segnames=None):
        substitute = Template(tmpl).substitute

        res = []
        for mapping in self.generate_tmpl_mappings(segnames):
            track_index = mapping["track_index"]

            if self.distribution == DISTRIBUTION_GAMMA:
                mapping["min_track"] = self.get_track_lt_min(track_index)

            if data is not None:
                seg_index = mapping["seg_index"]
                mapping["rand"] = data[seg_index, track_index]

            res.append(substitute(mapping))

        return res

    def make_spec_multiseg(self, name, *args, **kwargs):
        return make_spec(name, self.make_items_multiseg(*args, **kwargs))

    def make_dirichlet_table(self):
        num_segs = self.num_segs

        prob_diag = prob_transition_from_expected_len(LEN_SEG_EXPECTED)
        prob_nondiag = (1.0 - prob_diag) / (num_segs - 1)

        probs = diag(fill_array(prob_diag, num_segs))
        probs[probs == 0.0] = prob_nondiag

        # astype(int) means flooring the floats
        total_pseudocounts = self.len_seg_strength * self.num_bases
        pseudocounts_per_row = total_pseudocounts / num_segs
        pseudocounts = (probs * pseudocounts_per_row).astype(int)

        return pseudocounts

    def make_dirichlet_spec(self):
        dirichlet_table = self.make_dirichlet_table()
        items = [make_table_spec(DIRICHLET_FRAG, dirichlet_table)]

        return make_spec("DIRICHLET_TAB", items)

    def make_dense_cpt_start_seg_spec(self):
        return make_random_spec(DENSE_CPT_START_SEG_FRAG, 1, self.num_segs)

    def make_dense_cpt_seg_seg_spec(self):
        num_segs = self.num_segs

        if self.len_seg_strength > 0:
            frag = "\n".join([DENSE_CPT_SEG_SEG_FRAG, DIRICHLET_SEG_SEG_FRAG])
        else:
            frag = DENSE_CPT_SEG_SEG_FRAG

        return make_random_spec(frag, num_segs, num_segs)

    def make_dinucleotide_table_row(self):
        # simple one-parameter model
        gc = uniform()
        at = 1 - gc

        a = at / 2
        c = gc / 2
        g = gc - c
        t = 1 - a - c - g

        acgt = array([a, c, g, t])

        # shape: (16,)
        return outer(acgt, acgt).ravel()

    def make_dense_cpt_seg_dinucleotide_spec(self):
        table = [self.make_dinucleotide_table_row()
                 for seg_index in xrange(self.num_segs)]

        return make_table_spec(DENSE_CPT_SEG_DINUCLEOTIDE_FRAG, table)

    def make_dense_cpt_spec(self):
        num_segs = self.num_segs

        items = [self.make_dense_cpt_start_seg_spec(),
                 self.make_dense_cpt_seg_seg_spec()]

        if self.use_dinucleotide:
            items.append(self.make_dense_cpt_seg_dinucleotide_spec())

        return make_spec("DENSE_CPT", items)

    def rand_means(self):
        low = self.mins
        high = self.maxs
        num_segs = self.num_segs

        assert len(low) == len(high)

        # size parameter is so that we always get an array, even if it
        # has shape = (1,)

        # iterator so that we regenerate uniform for every seg
        return array([uniform(low, high, len(low))
                      for seg_index in xrange(num_segs)])

    def make_means(self):
        if MEAN_METHOD == MEAN_METHOD_UNIFORM:
            return self.rand_means()
        elif MEAN_METHOD == MEAN_METHOD_ML_JITTER:
            return jitter(vstack_tile(self.means, self.num_segs))

        raise ValueError("unsupported MEAN_METHOD")

    def make_mean_spec(self):
        return self.make_spec_multiseg("MEAN", MEAN_TMPL, self.make_means())

    def make_covars(self):
        num_segs = self.num_segs

        if COVAR_METHOD == COVAR_METHOD_MAX_RANGE:
            ranges = self.maxs - self.mins
            return vstack_tile(ranges, num_segs)
        elif COVAR_METHOD == COVAR_METHOD_ML_JITTER:
            return jitter(vstack_tile(self.vars, num_segs))

        raise ValueError("unsupported COVAR_METHOD")

    def make_covar_spec(self, tied):
        if tied:
            segnames = ["any"]
            tmpl = COVAR_TMPL_TIED
        else:
            segnames = None
            tmpl = COVAR_TMPL_UNTIED

        vars = self.make_covars()

        return self.make_spec_multiseg("COVAR", tmpl, vars, segnames)

    def make_items_gamma(self):
        means = self.means
        vars = self.vars

        substitute_scale = Template(GAMMASCALE_TMPL).substitute
        substitute_shape = Template(GAMMASHAPE_TMPL).substitute

        # random start values are equivalent to the random start
        # values of a Gaussian:
        #
        # means = scales * shapes
        # vars = shapes * scales**2
        #
        # therefore:
        scales = vars / means
        shapes = means**2 / vars

        res = []
        for mapping in self.generate_tmpl_mappings():
            seg_index = mapping["seg_index"]
            track_index = mapping["track_index"]
            index = mapping["index"] * 2

            # factory for new dictionaries that start with mapping
            mapping_plus = partial(dict, **mapping)

            scale = jitter(scales[track_index])
            shape = jitter(shapes[track_index])

            mapping_scale = mapping_plus(rand=scale, index=index)
            res.append(substitute_scale(mapping_scale))

            mapping_shape = mapping_plus(rand=shape, index=index+1)
            res.append(substitute_shape(mapping_shape))

        return res

    def make_gamma_spec(self):
        return make_spec("REAL_MAT", self.make_items_gamma())

    def make_mc_spec(self):
        return self.make_spec_multiseg("MC", MC_TMPLS[self.distribution])

    def make_mx_spec(self):
        return self.make_spec_multiseg("MX", MX_TMPL)

    def save_input_master(self, start_index=None, new=False):
        tracknames = self.tracknames
        num_segs = self.num_segs

        include_filename = self.gmtk_include_filename

        if new:
            input_master_filename = None
        else:
            input_master_filename = self.input_master_filename

        if self.len_seg_strength > 0:
            dirichlet_spec = self.make_dirichlet_spec()
        else:
            dirichlet_spec = ""

        dense_cpt_spec = self.make_dense_cpt_spec()

        self.calc_means_vars()

        distribution = self.distribution
        if distribution == DISTRIBUTION_NORM:
            mean_spec = self.make_mean_spec()
            covar_spec = self.make_covar_spec(COVAR_TIED)
            gamma_spec = ""
        elif distribution == DISTRIBUTION_GAMMA:
            mean_spec = ""
            covar_spec = ""

            # XXX: another option is to calculate an ML estimate for
            # the gamma distribution rather than the ML estimate for the
            # mean and converting
            gamma_spec = self.make_gamma_spec()
        else:
            raise ValueError("distribution %s not supported" % distribution)

        mc_spec = self.make_mc_spec()
        mx_spec = self.make_mx_spec()
        name_collection_spec = make_name_collection_spec(num_segs, tracknames)

        self.input_master_filename, self.input_master_filename_new = \
            save_template(input_master_filename, RES_INPUT_MASTER_TMPL,
                          locals(), self.dirname, self.delete_existing,
                          start_index)

    def save_dont_train(self):
        self.dont_train_filename = self.save_resource(RES_DONT_TRAIN)

    def save_output_master(self):
        self.output_master_filename = self.save_resource(RES_OUTPUT_MASTER)

    def save_output_filelist(self):
        dirpath = self.dirpath
        num_chunks = self.num_chunks

        output_filename_fmt = "out" + make_prefix_fmt(num_chunks) + EXT_OUT
        output_filenames = [dirpath / output_filename_fmt % index
                            for index in xrange(num_chunks)]

        output_filelistname = dirpath / extjoin("output", EXT_LIST)
        self.output_filelistname = output_filelistname

        with open(output_filelistname, "w") as output_filelist:
            for output_filename in output_filenames:
                print >>output_filelist, output_filename

        self.output_filenames = output_filenames

    def save_dumpnames(self):
        dirpath = self.dirpath
        dumpnames_filename = dirpath / extjoin("dumpnames", EXT_LIST)
        self.dumpnames_filename = dumpnames_filename

        with open(dumpnames_filename, "w") as dumpnames_file:
            print >>dumpnames_file, "seg"

    def save_params(self):
        self.load_include_coords()

        self.make_obs_dir()

        # do first, because it sets self.num_tracks and self.tracknames
        self.save_observations()

        self.save_include()
        self.save_structure()

        train = self.train
        identify = self.identify

        if train or identify:
            self.make_chunk_mem_reqs()

        if train:
            self.save_dont_train()
            self.save_output_master()

            # might turn off self.train, if the params already exist
            self.set_params_filename()
            self.set_log_likelihood_filename()

        if identify:
            self.save_output_filelist()
            self.save_dumpnames()

    def move_results(self, name, src_filename, dst_filename):
        if dst_filename:
            move(src_filename, dst_filename)
        else:
            dst_filename = src_filename

        setattr(self, name, dst_filename)

    def gmtk_out2bed(self):
        bed_filename = self.bed_filename

        if bed_filename is None:
            bed_filename = self.dirpath / BED_FILEBASENAME

        tracknames = self.tracknames_all

        # chunk_coord = (chrom, chromStart, chromEnd)
        zipper = izip(count(), self.output_filenames, self.chunk_coords)
        with gzip_open(bed_filename, "w") as bed_file:
            # XXX: add in browser track line (see SVN revisions
            # previous to 195)
            print >>bed_file, WIG_HEADER % ", ".join(tracknames)

            for index, gmtk_outfilename, chunk_coord in zipper:
                load_gmtk_out_write_bed(chunk_coord, gmtk_outfilename,
                                        bed_file, tracknames)

    def prog_factory(self, prog):
        """
        allows dry_run
        """
        # XXX: this poisons a global variable
        prog.dry_run = self.dry_run

        return prog

    def make_acc_filename(self, start_index, chunk_index):
        filebasename = ACC_FILENAME_FMT % (start_index, chunk_index)
        return self.dirpath / filebasename

    def make_job_name_train(self, start_index, round_index, chunk_index):
        return "emt%d.%d.%s.%s.%s" % (start_index, round_index, chunk_index,
                                      self.dirpath.name, getpid())

    def make_job_name_identify(self, chunk_index):
        return "vit%d.%s.%s" % (chunk_index, self.dirpath.name, getpid())

    def make_gmtk_kwargs(self):
        res = dict(strFile=self.structure_filename,
                   triFile=self.triangulation_filename,
                   verbosity=self.verbosity)

        assert self.int_filelistpath
        if self.int_filelistpath:
            res.update(of1=self.int_filelistpath,
                       fmt1="binary",
                       nf1=0,
                       ni1=self.num_int_cols,
                       iswp1=SWAP_ENDIAN)

        if self.float_filelistpath:
            res.update(of2=self.float_filelistpath,
                       fmt2="binary",
                       nf2=self.num_tracks,
                       ni2=0,
                       iswp2=SWAP_ENDIAN)

        return res

    @staticmethod
    def make_mem_req(chunk_len, num_tracks):
        # will fail if it's not pre-defined
        slope, intercept = MEM_REQS[num_tracks]
        res = slope * chunk_len + intercept

        return "%dM" % ceil(res / 2**20)

    def make_chunk_lens(self):
        self.chunk_lens = [end - start
                           for chr, start, end in self.chunk_coords]

    def make_chunk_mem_reqs(self):
        # XXX: should probably have different mem reqs for train or viterbi
        num_tracks = self.num_tracks

        if self.use_dinucleotide:
            num_tracks += 1

        self.make_chunk_lens()

        self.chunk_mem_reqs = [self.make_mem_req(chunk_len, num_tracks)
                               for chunk_len in self.chunk_lens]

    def chunk_mem_reqs_decreasing(self):
        # sort chunks by decreasing size, so the most difficult chunks
        # are dropped in the queue first
        zipper = izip(self.chunk_lens, count(), self.chunk_mem_reqs)

        # XXX: use itertools instead of a generator
        for _, chunk_index, chunk_mem_req in sorted(zipper, reverse=True):
            yield chunk_index, chunk_mem_req

    def queue_gmtk(self, prog, kwargs, job_name, mem_req, native_specs={}):
        gmtk_cmdline = prog.build_cmdline(options=kwargs)

        # convoluted so I don't have to deal with a lot of escaping issues
        cmdline = BASH_CMDLINE + ['%s "$@"' % gmtk_cmdline[0]] + gmtk_cmdline

        if self.dry_run:
            print " ".join(gmtk_cmdline)
            return None

        session = self.session
        job_tmpl = session.createJobTemplate()

        # shouldn't this be jobName? not in the Python DRMAA implementation
        # XXX: report upstream
        job_tmpl.name = job_name

        job_tmpl.remoteCommand = ENV_CMD
        job_tmpl.args = cmdline

        job_tmpl.outputPath = ":" + (self.output_dirpath / job_name)
        job_tmpl.errorPath = ":" + (self.error_dirpath / job_name)

        set_cwd_job_tmpl(job_tmpl)

        res_req = make_res_req(mem_req)
        job_tmpl.nativeSpecification = make_native_spec(l=res_req,
                                                        **native_specs)

        return session.runJob(job_tmpl)

    def queue_train(self, start_index, round_index,
                    chunk_index, mem_req, hold_jid=None, **kwargs):
        kwargs["inputMasterFile"] = self.input_master_filename

        prog = self.train_prog
        name = self.make_job_name_train(start_index, round_index, chunk_index)
        native_specs = dict(hold_jid=hold_jid)

        return self.queue_gmtk(prog, kwargs, name, mem_req, native_specs)

    def queue_train_parallel(self, input_params_filename, start_index,
                             round_index, **kwargs):
        queue_train_custom = partial(self.queue_train, start_index,
                                     round_index)

        kwargs["cppCommandOptions"] = make_cpp_options(input_params_filename)

        res = [] # task ids

        chunk_mem_reqs = list(self.chunk_mem_reqs_decreasing())
        last_chunk_index = chunk_mem_reqs[-1][0]
        for chunk_index, chunk_mem_req in chunk_mem_reqs:
            acc_filename = self.make_acc_filename(start_index, chunk_index)
            kwargs_chunk = dict(trrng=chunk_index, storeAccFile=acc_filename,
                                **kwargs)

            # -dirichletPriors T only on the last (smallest) chunk
            kwargs_chunk["dirichletPriors"] = (chunk_index == last_chunk_index)

            jobid = queue_train_custom(chunk_index, chunk_mem_req,
                                       **kwargs_chunk)
            res.append(jobid)

        return res

    def queue_train_bundle(self, parallel_jobids,
                           input_params_filename, output_params_filename,
                           start_index, round_index, **kwargs):
        """bundle step: take parallel accumulators and combine them
        """
        acc_filename = self.make_acc_filename(start_index,
                                              GMTK_INDEX_PLACEHOLDER)

        cpp_options = make_cpp_options(input_params_filename,
                                       output_params_filename)

        kwargs = \
            dict(outputMasterFile=self.output_master_filename,
                 cppCommandOptions=cpp_options,
                 trrng="nil",
                 loadAccRange="0:%s" % (self.num_chunks-1),
                 loadAccFile=acc_filename,
                 **kwargs)

        if self.dry_run:
            hold_jid = None
        else:
            hold_jid = ",".join(parallel_jobids)

        return self.queue_train(start_index, round_index, NAME_PLACEHOLDER,
                                MEM_REQ_BUNDLE, hold_jid, **kwargs)

    def save_jt_triangulation(self):
        infilename = self.triangulation_filename

        # either strip ".trifile" off end, or just use the whole filename
        infilename_stem = (infilename.rpartition(SUFFIX_TRIFILE)[0]
                           or infilename)

        outfilename = extjoin(infilename_stem, EXT_JT, EXT_TRIFILE)

        # XXX: this is a fairly hacky way of doing it and will not
        # work if the triangulation file changes from what GMTK
        # generates. probably need to key on tokens rather than lines
        with open(infilename) as infile:
            with open(outfilename, "w") as outfile:
                rewriter = rewrite_strip_comments(infile, outfile)

                consume_until(rewriter, "@@@!!!TRIFILE_END_OF_ID_STRING!!!@@@")
                consume_until(rewriter, "CE_PARTITION")

                for frame in xrange(NUM_TRIANGULATION_FRAMES):
                    rewrite_cliques(rewriter, frame)

                while rewriter.next():
                    pass

    def run_triangulate(self):
        prog = self.prog_factory(TRIANGULATE_PROG)

        structure_filename = self.structure_filename
        triangulation_filename = self.triangulation_filename
        if not triangulation_filename:
            triangulation_filename = extjoin(structure_filename, EXT_TRIFILE)
            self.triangulation_filename = triangulation_filename

        # XXX: need exist/delete_existing logic here
        prog(strFile=structure_filename,
             outputTriangulatedFile=triangulation_filename,
             verbosity=self.verbosity)

        if not self.jt_triangulation_filename:
            self.save_jt_triangulation()

    def run_train_round(self, start_index, round_index, **kwargs):
        """
        returns None: normal
        returns not None: abort
        """
        last_params_filename = self.last_params_filename
        curr_params_filename = extjoin(self.params_filename, str(round_index))

        parallel_jobids = \
            self.queue_train_parallel(last_params_filename, start_index,
                                      round_index, **kwargs)

        bundle_jobid = \
            self.queue_train_bundle(parallel_jobids, last_params_filename,
                                    curr_params_filename, start_index,
                                    round_index,
                                    llStoreFile=self.log_likelihood_filename,
                                    **kwargs)

        self.last_params_filename = curr_params_filename

        if self.dry_run:
            return False

        return self.wait_bundle(parallel_jobids, bundle_jobid)

    def run_train_start(self):
        # make new files if you have more than one random start
        new = self.random_starts > 1

        start_index = self.start_index

        self.save_input_master(start_index, new)
        self.set_params_filename(start_index, new)
        self.set_log_likelihood_filename(start_index, new)
        self.set_output_dirpaths(start_index)

        last_log_likelihood = NINF
        log_likelihood = NINF
        round_index = 0

        self.last_params_filename = None

        kwargs = self.train_kwargs

        while (round_index < MAX_EM_ITERS and
               is_training_progressing(last_log_likelihood, log_likelihood)):
            round_res = self.run_train_round(start_index, round_index,
                                             **kwargs)
            if round_res is not None:
                return (None, None, None, None)

            last_log_likelihood = log_likelihood
            log_likelihood = self.load_log_likelihood()

            print >>sys.stderr, "log likelihood = %s" % log_likelihood

            round_index += 1

        # log_likelihood and a list of src_filenames to save
        return (log_likelihood, self.input_master_filename,
                self.last_params_filename, self.log_likelihood_filename)

    def wait_bundle(self, parallel_jobids, bundle_jobid):
        """
        wait for bundle to finish
        """
        # XXXopt: polling in each thread is a bad way to do this
        # it would be best to use session.synchronize() centrally
        # and communicate to each thread when its job is done

        # the very best thing would be to eliminate the GIL lock
        # in the DRMAA wrapper
        job_info = None
        session = self.session
        interrupt_event = self.interrupt_event

        control = session.control
        terminate = session.TERMINATE
        while not job_info:
            try:
                job_info = session.wait(bundle_jobid, session.TIMEOUT_NO_WAIT)
            except ExitTimeoutError:
                # ExitTimeoutError: not ready yet
                interrupt_event.wait(SESSION_WAIT_TIMEOUT)
            except ValueError:
                # ValueError: the job terminated abnormally
                # so interrupt everybody
                if self.keep_going:
                    return False
                else:
                    interrupt_event.set()
                    raise

            if interrupt_event.isSet():
                for jobid in parallel_jobids + [bundle_jobid]:
                    try:
                        print >>sys.stderr, "killing job %s" % jobid
                        control(jobid, terminate)
                    except BaseException, err:
                        print >>sys.stderr, ("ignoring exception: %r"
                                             % err)
                raise KeyboardInterrupt

    def run_train(self):
        self.train_prog = self.prog_factory(EM_TRAIN_PROG)

        self.train_kwargs = dict(objsNotToTrain=self.dont_train_filename,
                                 maxEmIters=1,
                                 island=ISLAND,
                                 componentCache=COMPONENT_CACHE,
                                 lldp=LOG_LIKELIHOOD_DIFF_FRAC*100.0,
                                 **self.make_gmtk_kwargs())

        # save the destination file for input_master as we will be
        # generating new input masters for each start
        #
        # len(dst_filenames) == len(TRAIN_ATTRNAMES) == len(return value
        # of Runner.run_train_start())-1. This is asserted below.

        random_starts = self.random_starts
        assert random_starts >= 1

        # XXX: why did I have "if random_starts == 1:" preceding this line?
        self.save_input_master()

        if self.input_master_filename_new:
            input_master_filename = self.input_master_filename
        else:
            input_master_filename = None

        dst_filenames = [input_master_filename,
                         self.params_filename,
                         self.log_likelihood_filename]

        interrupt_event = Event()

        threads = []
        with Session() as session:
            try:
                for start_index in xrange(random_starts):
                    thread = RandomStartThread(self, session, start_index,
                                               interrupt_event)
                    thread.start()
                    threads.append(thread)

                # list of tuples(log_likelihood, input_master_filename,
                #                params_filename)
                start_params = []
                for thread in threads:
                    while thread.isAlive():
                        # XXX: KeyboardInterrupts only occur if there is a
                        # timeout specified here. Is this a Python bug?
                        thread.join(JOIN_TIMEOUT)

                    # this will get AttributeError if the thread failed and
                    # therefore did not set thread.result
                    start_params.append(thread.result)
            except KeyboardInterrupt:
                interrupt_event.set()
                for thread in threads:
                    thread.join()

                raise

        self.proc_train_results(start_params, dst_filenames)

    def proc_train_results(self, start_params, dst_filenames):
        if self.dry_run:
            return

        # finds the max by log_likelihood
        src_filenames = max(start_params)[1:]

        if None in src_filenames:
            raise ValueError, "all training threads failed"

        assert LEN_TRAIN_ATTRNAMES == len(src_filenames) == len(dst_filenames)

        zipper = zip(TRAIN_ATTRNAMES, src_filenames, dst_filenames)
        for name, src_filename, dst_filename in zipper:
            self.move_results(name, src_filename, dst_filename)

    def run_identify(self):
        if not self.input_master_filename:
            self.save_input_master()

        params_filename = self.params_filename

        prog = self.prog_factory(VITERBI_PROG)

        identify_kwargs = \
            dict(inputMasterFile=self.input_master_filename,

                 ofilelist=self.output_filelistname,
                 dumpNames=self.dumpnames_filename,

                 cppCommandOptions=make_cpp_options(params_filename),
                 **self.make_gmtk_kwargs())

        self.set_output_dirpaths("identify")

        # XXX: kill submitted jobs on exception
        jobids = []
        with Session() as session:
            self.session = session
            queue_identify = partial(self.queue_gmtk, prog)

            for chunk_index, chunk_mem_req in self.chunk_mem_reqs_decreasing():
                identify_kwargs_chunk = dict(dcdrng=chunk_index,
                                             **identify_kwargs)
                job_name = self.make_job_name_identify(chunk_index)

                jobid = queue_identify(identify_kwargs_chunk, job_name,
                                       chunk_mem_req)
                jobids.append(jobid)

            # XXX: search ask on DRMAA mailing list--how to allow
            # KeyboardInterrupt here?
            session.synchronize(jobids, session.TIMEOUT_WAIT_FOREVER, True)

        if not self.dry_run:
            # XXXopt: could be done in parallel as well
            self.gmtk_out2bed()

    def run(self):
        """
        main run, after dirname is specified

        this is exposed so that it can be overriden in a subclass
        """
        # XXXopt: use binary I/O to gmtk rather than ascii

        self.dirpath = path(self.dirname)
        self.save_params()

        if self.triangulate:
            self.run_triangulate()

        # XXX: make tempfile to specify for -jtFile for both
        # em and viterbi
        if self.train:
            self.run_train()

        if self.identify:
            self.run_identify()

    def __call__(self, *args, **kwargs):
        # XXX: register atexit for cleanup_resources

        dirname = self.dirname
        if dirname:
            if self.delete_existing or not path(dirname).isdir():
                self.make_dir(dirname)

            self.run(*args, **kwargs)
        else:
            try:
                with NamedTemporaryDir(prefix=TEMPDIR_PREFIX) as tempdir:
                    self.dirname = tempdir.name
                    self.is_dirname_temp = True
                    self.run()
            finally:
                # the temporary directory has already been deleted (after
                # unwinding of the with block), so let's stop referring to
                # it
                self.dirname = None
                self.is_dirname_temp = False

def parse_options(args):
    from optparse import OptionParser
    from ._util import OptionGroup

    usage = "%prog [OPTION]... H5FILE..."
    version = "%%prog %s" % __version__
    parser = OptionParser(usage=usage, version=version)

    with OptionGroup(parser, "Data subset") as group:
        group.add_option("-t", "--track", action="append", default=[],
                         metavar="TRACK",
                         help="append TRACK to list of tracks to use"
                         " (default all)")

        # This is a 0-based file.
        # I know because ENm008 starts at position 0 in encodeRegions.txt.gz
        group.add_option("--include-coords", metavar="FILE",
                          help="limit to genomic coordinates in FILE")

    with OptionGroup(parser, "Model files") as group:
        group.add_option("-i", "--input-master", metavar="FILE",
                          help="use or create input master in FILE")

        group.add_option("-s", "--structure", metavar="FILE",
                          help="use or create structure in FILE")

        group.add_option("-p", "--trainable-params", metavar="FILE",
                          help="use or create trainable parameters in FILE")

    with OptionGroup(parser, "Output files") as group:
        group.add_option("-b", "--bed", metavar="FILE",
                          help="create bed track in FILE")

    with OptionGroup(parser, "Intermediate files") as group:
        # XXX: consider removing this option
        # this probably isn't necessary as observations are written
        # out pretty quickly now
        group.add_option("-o", "--observations", metavar="DIR",
                          help="use or create observations in DIR")

        group.add_option("-d", "--directory", metavar="DIR",
                          help="create all other files in DIR")


    with OptionGroup(parser, "Variables") as group:
        group.add_option("-D", "--distribution", choices=DISTRIBUTIONS,
                         metavar="DIST", default=DISTRIBUTION_DEFAULT,
                         help="use DIST distribution")

        group.add_option("-r", "--random-starts", type=int,
                         default=RANDOM_STARTS, metavar="NUM",
                         help="randomize start parameters NUM times"
                         " (default 1)")

        group.add_option("--prior-strength", type=float,
                         default=PRIOR_STRENGTH, metavar="RATIO",
                         help="use RATIO times the number of data counts as"
                         " the number of pseudocounts for the segment length"
                         " prior (default 0)")

        group.add_option("-v", "--verbosity", type=int, default=VERBOSITY,
                         metavar="NUM",
                         help="show messages with verbosity NUM")

    with OptionGroup(parser, "Flags") as group:
        group.add_option("-f", "--force", action="store_true",
                         help="delete any preexisting files")
        group.add_option("-I", "--no-identify", action="store_true",
                         help="do not identify segments")
        group.add_option("-T", "--no-train", action="store_true",
                         help="do not train model")
        group.add_option("-k", "--keep-going", action="store_true",
                         help="keep going in some threads even when you have"
                         " errors in another")
        group.add_option("-n", "--dry-run", action="store_true",
                         help="write all files, but do not run any"
                         " executables")

    options, args = parser.parse_args(args)

    if not len(args) >= 1:
        parser.print_usage()
        sys.exit(1)

    return options, args

def main(args=sys.argv[1:]):
    options, args = parse_options(args)

    runner = Runner()

    runner.h5filenames = args
    runner.dirname = options.directory
    runner.obs_dirname = options.observations
    runner.bed_filename = options.bed

    runner.input_master_filename = options.input_master
    runner.structure_filename = options.structure
    runner.params_filename = options.trainable_params
    runner.include_coords_filename = options.include_coords

    runner.distribution = options.distribution
    runner.random_starts = options.random_starts
    runner.len_seg_strength = options.prior_strength
    runner.include_tracknames = options.track
    runner.verbosity = options.verbosity

    runner.delete_existing = options.force
    runner.train = not options.no_train
    runner.identify = not options.no_identify
    runner.dry_run = options.dry_run
    runner.keep_going = options.keep_going

    return runner()

if __name__ == "__main__":
    sys.exit(main())
