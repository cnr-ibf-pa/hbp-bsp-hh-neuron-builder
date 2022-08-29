#! /usr/bin/python3

from multiprocessing import cpu_count
import concurrent.futures
import subprocess
import argparse
import json
import time
import os


def disable_cypress_video():
    conf = 'cypress.json'
    if conf in os.listdir(args.project):
        with open(os.path.join(args.project, conf), 'r') as fd:
            jj = json.load(fd)
        jj.update({'video': False})
        with open(os.path.join(args.project, conf), 'w') as fd:
            json.dump(jj, fd, indent=4)
    

def run_cypress():
    cmd = f'{args.cypress} run -P "{args.project}"'
    if args.enable_browser:
        cmd += ' --headed'
    if args.browser:
        cmd += ' --browser ' + args.browser
    p = subprocess.run(cmd, shell='/bin/bash', capture_output=True, text=True)
    return p.returncode, p.stdout, p.stderr


def print_results(total_tests, passed_tests, failed_tests, execution_time):
    results = \
f"""
    Tests:\t{total_tests}
    Passed:\t{passed_tests}
    Failed:\t{failed_tests}

    Tests ended with success: {passed_tests}/{total_tests} ({passed_tests*100/total_tests}%)        
    
    Total execution time: {execution_time} seconds. 
"""
    print(results)


if __name__ == '__main__':

    parser = argparse.ArgumentParser(description='Run Cypress test in parallel session using the local machine.')
    parser.add_argument('-p', '--project', type=str, required=True, help='Set the path where the cypress project is placed.')
    parser.add_argument('-c', '--cypress', type=str, default='cypress', help='Explicity set the cypress executable if it is not found.')
    parser.add_argument('-t', '--test-number', default=1, type=int, help='Specify how many tests will launched. Default 1.')
    parser.add_argument('-b', '--browser', help='Run Cypress in the browser with the given name. If a filesystem path is supplied, Cypress will attempt to use the browser at that path.')
    parser.add_argument('-v', '--verbose', action='store_true', help='Print processes outputs.')
    parser.add_argument('--max-processes', type=int, default=cpu_count(), help='Set maximum processes that can run simultaneously. Default is %d.' % cpu_count())
    parser.add_argument('--enable-browser', action='store_true', help='Enable cypress browser view.')
    # parser.add_argument('--config', help='Load a custom "conf.json" file.')

    args = parser.parse_args()


    # try cypress
    if subprocess.run(args.cypress, shell='/bin/bash', capture_output=True).returncode > 0:
        # locate cypress otherwise exit
        args.cypress = os.path.join(os.getenv('HOME'), 'node_modules', 'cypress', 'bin', 'cypress')
        if subprocess.run(args.cypress, shell='/bin/bash', capture_output=True).returncode != 0:
            print('Cypress binary not found. Please set the Cypress binary using -c flag.')
            exit(1)

    args.project = os.path.abspath(args.project)

    disable_cypress_video()

    passed_tests = 0
    failed_tests = 0

    start_time = time.time()

    with concurrent.futures.ProcessPoolExecutor(max_workers=args.max_processes) as executor:
        processes = [executor.submit(run_cypress) for _ in range(args.test_number)]
        for process in concurrent.futures.as_completed(processes):
            print(process)
            result = process.result()
            if result[0] == 0:
                passed_tests += 1
            else:
                failed_tests += 1
                if args.verbose:
                    print('='*64)
                    print(result[1], result[2])
                    print('='*64)

    end_time = time.time()

    print_results(args.test_number, passed_tests, failed_tests, round(end_time - start_time, 1))
    exit(0)
