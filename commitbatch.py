#!/usr/bin/env python3

import itertools
import locale
import os
import subprocess
import statistics 


commits = list()
segments = []
stddev = 0
mean = 0

def segmentCommits(num_stddev):
    boundary = mean + (num_stddev * stddev)  #trying just 1 stddev out for now
    working = []
    segments = []
    for c in commits:
        if len(c['files']) < boundary:
            working.append(c)
        else:
            if len(working):
                segments.append(working)
            segments.append([c])
            working = []
    return segments

def calculateDisjointSets(segment):
    # Kludgy - has to be a better way
    # Step 1 - iterate the segments and put them in the format of [[file_set, [commit]], ...]
    batches = []
    empty = [set(), []]
    for commit in segment:
        # We're going to special case the empty file set since it doesn't seem to work
        # TODO need to look into why...
        if commit['files']:
            batches.append([commit['files'], [commit]])
        else:
            empty[1].append(commit)
            # Step 2 - n: bubble through the array merging overlapping sets
    old_count = 0
    while old_count != len(batches):
        old_count = len(batches)
        batches = disjointSetScan(batches)
    return batches + [empty]


def disjointSetScan(set_array):
    batches = []
    for a_batch in set_array:
        res = []
        for b in batches:
            if not b[0].isdisjoint(a_batch[0]):
                res = b
                break
        if res:
            res[0] = res[0].union(a_batch[0])
            res[1] = res[1] + a_batch[1]
        else:
            batches.append(a_batch)
    return batches

def getGitLogs():
    cmd = ['/usr/local/bin/git log origin/REL8_3_STABLE..origin/REL8_4_STABLE --reverse --name-only']
    git = subprocess.Popen(cmd, stdout=subprocess.PIPE, shell=True, encoding=locale.getpreferredencoding())
#    git = subprocess.Popen(cmd, stdout=subprocess.PIPE, shell=True)
#    out, err = git.communicate()
#    print(out)
    commit = dict()
    s = 0
    for line in git.stdout.readlines():
        line = line.rstrip()
        if not line.strip():
                continue
        if line.startswith('commit'):
            # commit['files'] = tuple(sorted(commit['files']))
            # f = commit['files']
            # if not f:
            #     f = 'NONE'
            #     if f in commits_1:
            #         commits_1[f].append(commit)
            #     else:
            #         commits_1[f] = list([commit['hash']])
            if commit:
                commits.append(commit)
            s += 1
            commit = {
                'hash': line.split()[-1],
                'seq_no': s,
                'files': set(),
            }
        elif line[0] not in ['A', 'D', ' '] and line[-2:] in ['.c', '.h']:
                commit['files'].add(line)
    commits.append(commit)

def simpleStats():
    global stddev
    global mean
    vals = []
    for commit in commits:
        vals.append(len(commit['files']))
    stddev = statistics.pstdev(vals)
    mean = statistics.mean(vals)
    distrib = [0, 0, 0, 0]
    for v in vals:
        if v > (mean + (3 * stddev)):
            distrib[3] = distrib[3] + 1
        elif v > (mean + (2 * stddev)):
            distrib[2] = distrib[2] + 1
        elif v > (mean + (1 * stddev)):
            distrib[1] = distrib[1] + 1
        else:
            distrib[0] = distrib[0] + 1
    print("commit distribution:\n\t within 1 stddev: ", distrib[0])
    print("\t 2 stddev: ", distrib[1])
    print("\t 3 stddev: ", distrib[2])
    print("\t > 3 stddev: ", distrib[3])
    print("Mean: ",mean)
    print("Stddev: ", stddev)

def printBatch(batch):
    print("Seq No | Commit                                    | Files")
    print("-------|-------------------------------------------|--------------------")
    for b in batch:
        for pair in itertools.zip_longest(b[1], b[0]):
            line = ['', '', '']
            if pair[0]:
                line[0] = pair[0]['seq_no']
                line[1] = pair[0]['hash']
            if pair[1]:
                line[2] = pair[1]
                
            print('{:<7}| {:<41} | {}'.format(*line))
        print("-------|-------------------------------------------|--------------------")
        
          

def main():
    print(os.getcwd())
    getGitLogs()
    print(len(commits))
    simpleStats()
    for i in range(1, 4):
        print("Testing with grouping commits to {0} stddev.\nCommit threshold is {1} C files".format(i, mean+(i*stddev)))
        s = segmentCommits(i)
        print("Total # of segments: ", len(s))
        for idx, seg in enumerate(s):
            print("== Segment: ", idx)
            print("\tSegment size: ", len(seg))
            b = calculateDisjointSets(seg)
            print("\tNumber of distinct sets: ", len(b))
            printBatch(b)
        
if __name__=="__main__":
    main()

    
            
