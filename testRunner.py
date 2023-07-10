#!/usr/bin/env python3

from asyncio.subprocess import DEVNULL
from os import path
from re import S
import sys
import os.path
from pathlib import Path
import argparse
import subprocess
from subprocess import Popen, PIPE

CRED    = '\33[31m'
CGREEN  = '\33[32m'
RESET = "\033[0;0m"
CBOLD     = '\33[1m'

numOfTests=0
numOfFailedTests=0
verbose=False
ciRun=False


def xprint(str, color = ''):
    global ciRun
    if (not ciRun):
        print(color, end='')
    print(str, end='')
    if (not ciRun):
        print(RESET)
    else:
        print('') # endline


def computePath(path, *paths):
    return os.path.normpath(os.path.join(path, *paths))

def compareFilesLineByLine(marker, testFile, actualFile, expectedFile):
    global numOfFailedTests
    with open(expectedFile) as expected, open(actualFile) as actual:
        expt = expected.readlines()
        actl = actual.readlines()

        if len(expt) != len(actl):
            xprint(f"Test {testFile} -- FAIL", CBOLD + CRED)
            xprint(f" {marker}: actual output len ({len(actl)}) differs from expected len ({len(expt)})")
            numOfFailedTests = numOfFailedTests + 1
            return False
        else:
            i = 0

            while (i < len(expt)):
                e = expt[i].rstrip()
                a = actl[i].rstrip()
                if (e != a):
                    xprint(f"Test {testFile} -- FAIL", CBOLD + CRED)
                    xprint(f" {marker}: actual output differs from expected in line {i + 1}")
                    xprint(f"  ACTUAL:   {a}")
                    xprint(f"  EXPECTED: {e}")
                    numOfFailedTests = numOfFailedTests + 1
                    return False
                i = i + 1
    return True

def updateExpectedFromActualIfNeed(marker, actualFile, expectedFile):
    if (not path.exists(expectedFile)):
        xprint(f"  info: no {marker} expected file, create it")
        result = open(actualFile).read()
        open(expectedFile, 'w+').write(result)


def runTestGeneric(compiler, workingDir, dirname, name, kind, suffix, extraargs, stdoutFile):
    global numOfFailedTests
    global verbose
    global have_errors
    testFilePath = computePath(dirname, name + '.nut')
    expectedResultFilePath = computePath(dirname, name + suffix)
    outputDir = computePath(workingDir, dirname)

    if (not path.exists(outputDir)):
        os.makedirs(outputDir)

    actualResultFilePath = computePath(workingDir, expectedResultFilePath)

    if path.exists(actualResultFilePath):
        os.remove(actualResultFilePath)

    compialtionCommand = [compiler, "-ast", "-optCH"]
    compialtionCommand += extraargs

    if verbose:
        xprint(compialtionCommand)

    if stdoutFile:
        outredirect = open(actualResultFilePath, 'w+')
    else:
        outredirect = subprocess.PIPE
        compialtionCommand += [actualResultFilePath]

    compialtionCommand += [testFilePath]

    proc = Popen(compialtionCommand, stdout=outredirect, stderr=subprocess.PIPE)

    try:
      outs, errs = proc.communicate(timeout=10)
    except subprocess.TimeoutExpired:
      proc.kill()
      outs, errs = proc.communicate()
      xprint("\nTIMEOUT: sq freezed on test: {0}".format(testFilePath), CBOLD + CRED)
      numOfFailedTests = numOfFailedTests + 1
      return

    if proc.returncode != 0:
        xprint("TEST: {0} Crashed".format(testFilePath), CBOLD + CRED)
        xprint(f"STDERR: {0}".format(errs))
    else:
        testOk = True
        if (path.exists(expectedResultFilePath)):
            testOk = compareFilesLineByLine(kind, testFilePath, actualResultFilePath, expectedResultFilePath)

        if (testOk):
            xprint(f"TEST: {testFilePath} -- OK", CBOLD + CGREEN)

        updateExpectedFromActualIfNeed(kind, actualResultFilePath, expectedResultFilePath)

def runDiagTest(compiler, workingDir, dirname, name):
    runTestGeneric(compiler, workingDir, dirname, name, "Diagnostics", '.diag.txt', ["-diag-file"], False)

def runExecuteTest(compiler, workingDir, dirname, name):
    runTestGeneric(compiler, workingDir, dirname, name, "Exec", '.out', [], True)

def runASTTest(compiler, workingDir, dirname, name):
    runTestGeneric(compiler, workingDir, dirname, name, "AST", '.opt.txt', ["-ast-dump"], False)


def runTestForData(filePath, compiler, workingDir, testMode):
    global numOfFailedTests
    global numOfTests

    numOfTests = numOfTests + 1

    # print(f"processing {filePath}")
    basename = os.path.basename(filePath)
    dirname = os.path.dirname(filePath)
    index_of_dot = basename.index('.')
    suffix = basename[index_of_dot + 1:]
    # print(f"dirname: {dirname}, baseName: {basename}, suffix: {suffix}")
    name = basename[:index_of_dot]
    if suffix == "nut":
        if testMode == 'a':
            runASTTest(compiler, workingDir, dirname, name)
        elif testMode == 'd':
            runDiagTest(compiler, workingDir, dirname, name)
        elif testMode == 'e':
            runExecuteTest(compiler, workingDir, dirname, name)
        else:
            xprint(f"Unknown test mode {testMode}")



def walkDirectory(path, indent, block):
    for file in path.iterdir():
        # print('\t' * indent + f"Walk path {file}")
        if file.is_dir():
            walkDirectory(file, indent + 1, block)
        else:
            block(file)


def main():
    global numOfFailedTests
    global verbose, ciRun
    arguments = len(sys.argv) - 1
    position = 1
    compiler = ''
    workingDir = ''

    while (arguments >= position):
        arg = sys.argv[position]
        if arg == '-sq':
            compiler = sys.argv[position + 1]
            position = position + 1
        elif arg == '-workDir':
            workingDir = sys.argv[position + 1]
            position = position + 1
        elif arg == '-v':
            verbose = True
        elif arg == '-ci':
            ciRun = True
        else:
            xprint(f"Unknown option \'${arg}\' at position {position:>6}")
        position = position + 1

    if compiler == '':
        xprint(f"SQ is not specified")
        exit(-1)
    elif workingDir =='':
        xprint(f"working dir is not specified")
        exit(-1)

    walkDirectory(Path(computePath('testData', 'exec')), 0, lambda a: runTestForData(a, compiler, workingDir, 'e'))
    walkDirectory(Path(computePath('testData', 'diagnostics')), 0, lambda a: runTestForData(a, compiler, workingDir, 'd'))
    walkDirectory(Path(computePath('testData', 'ast')), 0, lambda a: runTestForData(a, compiler, workingDir, 'a'))

    if numOfFailedTests:
        xprint(f"Failed tests: {numOfFailedTests}", CBOLD + CRED)
    else:
        xprint(f"All tests passed", CBOLD + CGREEN)

    exit (numOfFailedTests)



if __name__ == "__main__":
   main()







