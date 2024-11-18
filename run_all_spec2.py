# Import necessary libraries
import argparse
import concurrent.futures
import json
import os
import random
import subprocess
import sys
import threading
import time
from datetime import datetime
from itertools import product

"""This script handles running all spec benchmarks in parallel give any gem5 config."""

# Set up argument parser
parser = argparse.ArgumentParser()
parser.add_argument(
    "--dry-run", action="store_true", default=False, help="Dry run the command"
)
parser.add_argument(
    "-b",
    "--bench",
    "--benchmark",
    nargs="+",
    help="Benchmark to run[^1^][1]. Without this, program runs all by default",
)
parser.add_argument(
    "-r",
    "--redirect",
    action="store_false",
    default=True,
    help="Redirect outputs to terminal",
)
# parser.add_argument(
#     "--run_name",
#     type=str,
#     default="memory_ravens",
#     help="Name of the run to be used in the output directory",
# )
args = parser.parse_args()
spec_path = "spec_bin/train"

# Define SPEC benchmark commands
spec_cmds = [
    # Each dictionary in the list represents a SPEC benchmark command
    # 'name': Name of the benchmark
    # 'path': Path to the benchmark binary
    # 'bin': Benchmark binary name
    # 'opts': Options for the benchmark command
    # TODO: Add comments for each benchmark explaining its purpose
    {
        "name": "perlbench_r",
        "path": f"{spec_path}/500.perlbench_r/run/run_base_train_main-m64.0000/",
        "bin": "perlbench_r_base.main-m64",
        "opts": "-I./lib splitmail.pl 535 13 25 24 1091 1",
    },
    {
        "name": "gcc_r",
        "path": f"{spec_path}/502.gcc_r/run/run_base_train_main-m64.0000/",
        "bin": "cpugcc_r_base.main-m64",
        "opts": "train01.c -O3 -finline-limit=50000 -o train01.opts-O3_-finline-limit_50000.s",
    },
    # TODO: fix the handling of the input file for this benchmark
    # {
    #     "name": "bwaves_r",
    #     "path": f"{spec_path}/503.bwaves_r/run/run_base_train_main-m64.0000/",
    #     "bin": "bwaves_r_base.main-m64",
    #     "opts": "< bwaves_1.in",
    # },
    {
        "name": "mcf_r",
        "path": f"{spec_path}/505.mcf_r/run/run_base_train_main-m64.0000/",
        "bin": "mcf_r_base.main-m64",
        "opts": "inp.in",
    },
    {
        "name": "cactuBSSN_r",
        "path": f"{spec_path}/507.cactuBSSN_r/run/run_base_train_main-m64.0000/",
        "bin": "cactusBSSN_r_base.main-m64",
        "opts": "spec_train.par",
    },
    {
        "name": "namd_r",
        "path": f"{spec_path}/508.namd_r/run/run_base_train_main-m64.0000/",
        "bin": "namd_r_base.main-m64",
        "opts": "--input apoa1.input --iterations 7 --output apoa1.train.output",
    },
    {
        "name": "povray_r",
        "path": f"{spec_path}/511.povray_r/run/run_base_train_main-m64.0000/",
        "bin": "povray_r_base.main-m64",
        "opts": "SPEC-benchmark-train.ini",
    },
    {
        "name": "lbm_r",
        "path": f"{spec_path}/519.lbm_r/run/run_base_train_main-m64.0000/",
        "bin": "lbm_r_base.main-m64",
        "opts": "300 reference.dat 0 1",
    },
    {
        "name": "omnetpp_r",
        "path": f"{spec_path}/520.omnetpp_r/run/run_base_train_main-m64.0000/",
        "bin": "omnetpp_r_base.main-m64",
        "opts": "-c General -r 0",
    },
    {
        "name": "wrf_r",
        "path": f"{spec_path}/521.wrf_r/run/run_base_train_main-m64.0000/",
        "bin": "wrf_r_base.main-m64",
        "opts": "namelist.input",
    },
    {
        "name": "xalancbmk_r",
        "path": f"{spec_path}/523.xalancbmk_r/run/run_base_train_main-m64.0000/",
        "bin": "cpuxalan_r_base.main-m64",
        "opts": "allbooks.xml xalanc.xsl",
    },
    {
        "name": "x264_r",
        "path": f"{spec_path}/525.x264_r/run/run_base_train_main-m64.0000/",
        "bin": "x264_r_base.main-m64",
        "opts": "--dumpyuv 50 --frames 142 -o BuckBunny_New.264 BuckBunny.yuv 1280x720",
    },
    {
        "name": "blender_r",
        "path": f"{spec_path}/526.blender_r/run/run_base_train_main-m64.0000/",
        "bin": "blender_r_base.main-m64",
        "opts": "sh5_reduced.blend --render-output sh5_reduced_ --threads 1 -b -F RAWTGA -s 234 -e 234 -a",
    },
    {
        "name": "cam4_r",
        "path": f"{spec_path}/527.cam4_r/run/run_base_train_main-m64.0000/",
        "bin": "cam4_r_base.main-m64",
    },
    {
        "name": "deepsjeng_r",
        "path": f"{spec_path}/531.deepsjeng_r/run/run_base_train_main-m64.0000/",
        "bin": "deepsjeng_r_base.main-m64",
        "opts": "train.txt",
    },
    {
        "name": "imagick_r",
        "path": f"{spec_path}/538.imagick_r/run/run_base_train_main-m64.0000/",
        "bin": "imagick_r_base.main-m64",
        "opts": "-limit disk 0 train_input.tga -resize 320x240 -shear 31 -edge 140 -negate -flop -resize 900x900 -edge 10 train_output.tga",
    },
    {
        "name": "leela_r",
        "path": f"{spec_path}/541.leela_r/run/run_base_train_main-m64.0000/",
        "bin": "leela_r_base.main-m64",
        "opts": "train.sgf",
    },
    {
        "name": "nab_r",
        "path": f"{spec_path}/544.nab_r/run/run_base_train_main-m64.0000/",
        "bin": "nab_r_base.main-m64",
        "opts": "gcn4dna 1850041461 300",
    },
    {
        "name": "exchange2_r",
        "path": f"{spec_path}/548.exchange2_r/run/run_base_train_main-m64.0000/",
        "bin": "exchange2_r_base.main-m64",
        "opts": "1",
    },
    {
        "name": "fotonik3d_r",
        "path": f"{spec_path}/549.fotonik3d_r/run/run_base_train_main-m64.0000/",
        "bin": "fotonik3d_r_base.main-m64",
    },
    # TODO: fix input
    # {
    #     "name": "roms_r",
    #     "path": f"{spec_path}/554.roms_r/run/run_base_train_main-m64.0000/",
    #     "bin": "roms_r_base.main-m64",
    #     "opts": "ocean_benchmark1.in.x",
    # },
    {
        "name": "xz_r",
        "path": f"{spec_path}/557.xz_r/run/run_base_train_main-m64.0000/",
        "bin": "xz_r_base.main-m64",
        "opts": "IMG_2560.cr2.xz 40 ec03e53b02deae89b6650f1de4bed76a012366fb3d4bdc791e8633d1a5964e03004523752ab008eff0d9e693689c53056533a05fc4b277f0086544c6c3cbbbf6 40822692 40824404 4",
    },
]


# simulation parameters
cwd = os.getcwd() + "/"
# gem5_bin = cwd + "build/X86/gem5.debug"
gem5_bin = cwd + "build/X86/gem5.fast"
# gem5_bin = cwd + "build/X86/gem5.opt"
project_dir = "chipletization"
# project_dir = "malware_detection"
# project_dir = "rowhammer"
config_file = cwd + "configs/chipletization/se_deriv_o3.py"
# config_file = cwd + f"configs/malware_detection/se_deriv.py"

# debug_flags = ["SecureModuleCpp"]
debug_flags = []

# Create session and trace directories based on current date and time
session_dir = (
    cwd + f"runs/{project_dir}/" + datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
)
trace_dir = session_dir + "/traces/"
os.makedirs(session_dir, exist_ok=True)
os.makedirs(trace_dir, exist_ok=True)
# choose either fast or debug.
# gem5_bin = cwd + "build/X86/gem5.fast"

# static parameters
# these are the params you want to keep constant accross each run. For example, "cache size" may be one paramter you want to keep constant accross all benchmarks
fast_forward = 10000000
maxinsts = 250000000
# fast_forward = 200000 
# maxinsts = 5000000
redirect = args.redirect

# permutable paramters
# these are the params you want to change accross each run. For example, "cache miss latency" may be one paramter you want to see given multiple benchmarks
# set these as key value pairs
permutable_params = {
    "renameToFetchDelay": [4],
    "iewToFetchDelay": [4],
    "fetchToDecodeDelay": [4],
    "sys_clock": ["2GHz"],
    "forwardComSize": [10],
    "backComSize": [10],
}
# all_permutations = [
#     dict(zip(permutable_params.keys(), p))
#     for p in product(*permutable_params.values())
# ]

# Frick this im just gonna set it myself
all_permutations = [{'iewToCommitDelay': 1, 'sys_clock': '2GHz', 'forwardComSize': 10, 'backComSize': 10}, {'iewToCommitDelay': 2, 'sys_clock': '2GHz', 'forwardComSize': 10, 'backComSize': 10}, {'iewToCommitDelay': 4, 'sys_clock': '2GHz', 'forwardComSize': 10, 'backComSize': 10}]

print(all_permutations)

print(json.dumps(all_permutations, indent=4))
# permutable_params = []

# Build command strings

cmd_strs = []
for c in spec_cmds:
    if args.bench and c["name"] not in args.bench:
        continue
    benchmark = c["name"]
    cmd = c["bin"]
    path = cwd + c["path"]
    # our single command string now becomes a list of command strings for each permutation

    cs = []
    for i, b in enumerate(all_permutations):
        sim_params = ""
        for k, v in b.items():
            sim_params += f"--{k} {v} "
        # cs.append(c + ") ")
        # cmd_str = f"(cd {path} && {gem5_bin} --debug-flags SecureModuleCpp --outdir={session_dir}/{benchmark}/ {config_file} --cmd {cmd} "
        # cmd_str = f"(cd {path} && {gem5_bin} --outdir={session_dir}/{benchmark}/ {config_file} --cmd {cmd} --mem_issue_latency {mem_issue_latency} --read_issue_latency {read_issue_latency} --write_issue_latency {write_issue_latency} "
        cmd_str = f"(cd {path} && {gem5_bin} --outdir={session_dir}/stats/{benchmark}_{i}/ "
        for d in debug_flags:
            cmd_str += f" --debug-flags {d} "
        cmd_str += f" {config_file} --cmd {cmd} "
        cmd_str += sim_params
        cmd_str += ' --opts \\\\"{}\\\\"'.format(c.get("opts", ""))
        cmd_str += f" --fast-forward {fast_forward} --maxinsts {maxinsts}) "

        if redirect:
            cmd_str += f"1> {trace_dir}/{benchmark}_{i}.stdout 2> {trace_dir}/{benchmark}_{i}.stderr"

        cmd_strs.append((cmd_str, benchmark))

for i in cmd_strs:
    print(f"INFO: running benchmark {i[1]} with command: {i[0]}")
    print("=====================================")


print("=====================================")
print(
    """WARNING:
        bwaves_r and roms_r benchmarks are not supported yet.
        There is an issue with handling the input file."""
)
print(f"INFO: session directory is {session_dir}")
if redirect:
    print(f"INFO: redirecting stdout to {trace_dir}/<benchmark>.stdout")
print("=====================================")
print(f"INFO: fastforwarding {fast_forward} instructions")
print(f"INFO: stopping after {maxinsts} instructions")

# stall for 3 seconds
# time.sleep(1.5)


if args.dry_run:
    print("INFO: DRY RUN MODE")
    print(f"INFO: would execute {len(cmd_strs)} runs")
    for i in cmd_strs:
        print(f"INFO: running benchmark {i[1]} with command: {i[0]}")
    exit(0)


# Function to execute command strings
# returns exit code
def execute(cmd):
    # get the word after "--cmd" in the cmd_str
    result = subprocess.run(cmd[0], shell=True)
    return result.returncode


def do_sleep(start_time):
    sleep_time = random.randint(5, 10)
    time.sleep(sleep_time)
    return time.time() - start_time  # Return the elapsed time


# Execute all benchmarks using ThreadPoolExecutor
print(
    "INFO: launching all threads. check .stdout and .stderr files in the traces directory."
)
print("=====================================")
# with concurrent.futures.ThreadPoolExecutor() as executor:
#     executor.map(execute, cmd_strs)

num_threads = len(cmd_strs)
# Initialize the status display
print("\n" * num_threads)  # Create initial space for the status lines
with concurrent.futures.ThreadPoolExecutor(
    # max_workers=os.cpu_count()
    max_workers=12
) as executor:
    # Record the start time for each thread and submit the tasks
    start_times = [time.time() for _ in range(num_threads)]
    end_times = [0 for _ in range(num_threads)]
    futures = [
        executor.submit(
            execute,
            cmd_strs[i],
        )
        for i in range(num_threads)
    ]

    # update simulation status
    try:
        while True:
            # Move the cursor up by 'num_threads' lines to update the statuses in place
            print(f"\033[{num_threads}A", end="")

            for i, future in enumerate(futures):
                # elapsed_time = time.time() - start_times[i]
                if future.running():
                    end_times[i] = time.time()
                    elapsed_time = end_times[i] - start_times[i]
                    status = "Running ⏳"
                elif future.done():
                    elapsed_time = end_times[i] - start_times[i]
                    if future.result() == 0:
                        status = "Done ✅"
                    else:
                        status = f"Failed ❌"
                else:
                    status = "Waiting 🕑"
                    start_times[i] = time.time()
                    elapsed_time = 0
                print(
                    f"{cmd_strs[i][1]:<15} {i+1:<3} | {'Status':<10} {status:<10} | {'Elapsed Time':<15} {elapsed_time:0.0f}s | "
                )

            if all(future.done() for future in futures):
                break
            time.sleep(1)  # Wait for 1 second before the next status update

    except KeyboardInterrupt:
        print(
            "\n❌ Keyboard interrupt received, cancelling tasks...\nYou may need to run `pkill gem5` to make sure all threads are taken care of! 🚨"
        )
        for future in futures:
            future.cancel()  # Attempt to cancel each future

# Final messages and exit
print(f"INFO: Done running all benchmarks. Exiting.")
print(
    f"INFO: Trace files are stored in {session_dir}. It is highly recommended to move them to a different location or rename the folder."
)
exit(0)
