#!/usr/bin/env python

import os
import sys
import glob
import fnmatch


def TSatPyTeX():
    tsat_dir = os.path.realpath(os.path.join(os.path.dirname(__file__), '../TSatPy'))
    src_tex = os.path.join(os.path.dirname(__file__), 'sections/TSatPySource.tex')

    header = """
\chapter{TSatPy SOURCE CODE}
\label{chap:tsatpy_source}

\linespread{1}
"""

    with open(src_tex, 'w') as tex:
        tex.write(header)

        for f in sorted(glob.glob('%s/*.py' % tsat_dir)):
            fn = f[len(tsat_dir)+1:]
            tex.write('\n')
            tex.write('\pagebreak\n')
            tex.write('\section*{TSatPy/%s}\label{code:TSatPy/%s}' % (fn.replace('_', '\_'), fn))
            tex.write('\inputminted[linenos,fontsize=\scriptsize]{python}{%s}\n' % f)

        for f in sorted(glob.glob('%s/tests/*.py' % tsat_dir)):
            fn = f[len(tsat_dir)+1:]
            tex.write('\n')
            tex.write('\pagebreak\n')
            tex.write('\section*{TSatPy/%s}\label{code:TSatPy/%s}\n' % (fn.replace('_', '\_'), fn))
            tex.write('\inputminted[linenos,fontsize=\scriptsize]{python}{%s}\n' % f)


def TSatPySamples():
    sample_script_dir = os.path.realpath(os.path.join(os.path.dirname(__file__), '../tex/sample_scripts'))
    src_tex = os.path.join(os.path.dirname(__file__), 'sections/TSatPySamples.tex')

    header = """
\chapter{TSatPy SAMPLE SCRIPTS}
\label{chap:tsatpy_samples}

\linespread{1}
"""

    with open(src_tex, 'w') as tex:
        tex.write(header)

        for f in sorted(glob.glob('%s/*.py' % sample_script_dir)):
            fn = f[len(sample_script_dir)+1:]
            tex.write('\n')
            tex.write('\pagebreak\n')
            tex.write('\section*{%s}\label{code:TSatPySamples/%s}' % (fn.replace('_', '\_'), fn))
            tex.write('\inputminted[linenos,fontsize=\scriptsize]{python}{%s}\n' % f)


def MatlabOOTeX():
    src_tex = os.path.join(os.path.dirname(__file__), 'sections/NSSSource.tex')

    header = """
\chapter{NSS OBJECT ORIENTED SOURCE CODE}
\label{chap:NSSObjectOrientedSourceCode}

\linespread{1}
"""

    with open(src_tex, 'w') as tex:
        tex.write(header)

        code_dir = os.path.realpath(os.path.join(os.path.dirname(__file__), '../beta_versions/matlab_object_oriented/lib'))
        for f in sorted([os.path.join(dirpath, fname)
            for dirpath, dirnames, files in os.walk(code_dir)
            for fname in fnmatch.filter(files, '*.m')]):

            fn = f[len(code_dir)+1:]
            tex.write('\n')
            tex.write('\pagebreak\n')
            tex.write('\section*{NSS/%s}\label{code:NSS/%s}\n' % (fn.replace('_', '\_'), fn))
            tex.write('\inputminted[linenos,fontsize=\scriptsize]{matlab}{%s}\n' % f)

        code_dir = os.path.realpath(os.path.join(os.path.dirname(__file__), '../beta_versions/matlab_object_oriented/sims'))
        for f in sorted([os.path.join(dirpath, fname)
            for dirpath, dirnames, files in os.walk(code_dir)
            for fname in fnmatch.filter(files, '*.m')]):

            fn = f[len(code_dir)+1:]
            tex.write('\n')
            tex.write('\pagebreak\n')
            tex.write('\section*{NSS/%s}\label{code:NSS/%s}\n' % (fn.replace('_', '\_'), fn))
            tex.write('\inputminted[linenos,fontsize=\scriptsize]{matlab}{%s}\n' % f)



if __name__ == "__main__":
    TSatPyTeX()
    TSatPySamples()
    MatlabOOTeX()
