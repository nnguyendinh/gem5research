import argparse
import os
import pdb
import sys

import m5
from m5.defines import buildEnv
from m5.objects import *
from m5.params import NULL
from m5.util import (
    addToPath,
    fatal,
    warn,
)

from gem5.isas import ISA

addToPath("../")

from common import (
    CacheConfig,
    CpuConfig,
    MemConfig,
    ObjectList,
    Options,
    Simulation,
)
from common.Caches import *
from common.cpu2000 import *
from common.FileSystemConfig import config_filesystem
from ruby import Ruby


def _get_hwp(hwp_option):
    if hwp_option == None:
        return NULL

    hwpClass = ObjectList.hwp_list.get(hwp_option)
    return hwpClass()


def get_processes(args):
    """Interprets provided args and returns a list of processes"""

    multiprocesses = []
    inputs = []
    outputs = []
    errouts = []
    pargs = []

    workloads = args.cmd.split(";")
    if args.input != "":
        if '"' in args.input:
            print(
                "WARNING: removing quotes from options list. Make sure your command options don't need them."
            )
        inputs = args.input.replace('"', "").split(";")
    if args.output != "":
        outputs = args.output.split(";")
    if args.errout != "":
        errouts = args.errout.split(";")
    if args.options != "":
        if '"' in args.options:
            print(
                "WARNING: removing quotes from options list. Make sure your command options don't need them."
            )
        pargs = args.options.replace('"', "").split(";")

    idx = 0
    for wrkld in workloads:
        process = Process(pid=100 + idx)
        process.executable = wrkld
        if args.cwd:
            process.cwd = args.cwd
        else:
            process.cwd = os.getcwd()
        process.gid = os.getgid()

        if args.env:
            with open(args.env) as f:
                process.env = [line.rstrip() for line in f]

        if len(pargs) > idx:
            process.cmd = [wrkld] + pargs[idx].split()
        else:
            process.cmd = [wrkld]

        if len(inputs) > idx:
            process.input = inputs[idx]
        if len(outputs) > idx:
            process.output = outputs[idx]
        if len(errouts) > idx:
            process.errout = errouts[idx]

        multiprocesses.append(process)
        idx += 1

    if args.smt:
        cpu_type = ObjectList.cpu_list.get(args.cpu_type)
        assert ObjectList.is_o3_cpu(cpu_type), "SMT requires an O3CPU"
        return multiprocesses, idx
    else:
        return multiprocesses, 1


def _get_cache_opts(level, options):
    opts = {}

    size_attr = f"{level}_size"
    if hasattr(options, size_attr):
        opts["size"] = getattr(options, size_attr)

    assoc_attr = f"{level}_assoc"
    if hasattr(options, assoc_attr):
        opts["assoc"] = getattr(options, assoc_attr)

    prefetcher_attr = f"{level}_hwp_type"
    if hasattr(options, prefetcher_attr):
        opts["prefetcher"] = _get_hwp(getattr(options, prefetcher_attr))

    return opts


def getCPUClass(cpu_type):
    """Returns the required cpu class and the mode of operation."""
    cls = ObjectList.cpu_list.get(cpu_type)
    return cls, cls.memory_mode()


parser = argparse.ArgumentParser()
Options.addCommonOptions(parser)
Options.addSEOptions(parser)

parser.add_argument(
    "--cwd",
    help="change the relative dir for the binary",
)
# --cmd already derrived from other args
parser.add_argument(
    "--opts",
    help="options for the command",
)

parser.add_argument(
    "--decodeToFetchDelay",
    help="Decode to fetch delay",
    default=1,
)

parser.add_argument(
    "--renameToFetchDelay",
    help="Rename to fetch delay",
    default=1,
)

parser.add_argument(
    "--iewToFetchDelay",
    help="Issue/Execute/Writeback to fetch delay",
    default=1,
)

parser.add_argument(
    "--commitToFetchDelay",
    help="Commit to fetch delay",
    default=1,
)

parser.add_argument(
    "--renameToDecodeDelay",
    help="Rename to decode delay",
    default=1,
)

parser.add_argument(
    "--iewToDecodeDelay",
    help="Issue/Execute/Writeback to decode delay",
    default=1,
)

parser.add_argument(
    "--commitToDecodeDelay",
    help="Commit to decode delay",
    default=1,
)

parser.add_argument(
    "--fetchToDecodeDelay",
    help="Fetch to decode delay",
    default=1,
)

parser.add_argument(
    "--iewToRenameDelay",
    help="Issue/Execute/Writeback to rename delay",
    default=1,
)

parser.add_argument(
    "--commitToRenameDelay",
    help="Commit to rename delay",
    default=1,
)

parser.add_argument(
    "--decodeToRenameDelay",
    help="Decode to rename delay",
    default=1,
)

parser.add_argument(
    "--commitToIEWDelay",
    help="Commit to Issue/Execute/Writeback delay",
    default=1,
)

parser.add_argument(
    "--renameToIEWDelay",
    help="Rename to Issue/Execute/Writeback delay",
    default=2,
)

parser.add_argument(
    "--issueToExecuteDelay",
    help="Issue to execute delay (internal to the IEW stage)",
    default=1,
)

parser.add_argument(
    "--iewToCommitDelay",
    help="Issue/Execute/Writeback to commit delay",
    default=1,
)

parser.add_argument(
    "--renameToROBDelay",
    help="Rename to reorder buffer delay",
    default=1,
)

parser.add_argument(
    "--forwardComSize",
    help="Time buffer size for forwards communication",
    default=5,
)

parser.add_argument(
    "--backComSize",
    help="Time buffer size for backwards communication",
    default=5,
)

# Add argument for clock frequency
parser.add_argument(
    "--sys_clock",
    help="Clock frequency of the system",
    default="1GHz",
)

# Homogenous delays
parser.add_argument(
    "--homogenousIEWDelays",
    help="IEW Delays set to be homogenous",
)

parser.add_argument(
    "--homogenousRenameDelays",
    help="Rename Delays set to be homogenous",
)

parser.add_argument(
    "--homogenousFetchDelays",
    help="Fetch Delays set to be homogenous",
)

parser.add_argument(
    "--homogenousDecodeDelays",
    help="Decode Delays set to be homogenous",
)

parser.add_argument(
    "--homogenousMainStageDelays",
    help="Main Pipeline Stage Delays set to be homogenous",
)

if "--ruby" in sys.argv:
    Ruby.define_options(parser)

args = parser.parse_args()

multiprocesses = []
numThreads = 1

if args.cmd:
    # do this later if we need to do multi-workload shit.
    # multiprocesses, numThreads = get_processes(args)

    p = Process(pid=100)
    w = args.cmd.split(";")[0]
    pargs = args.opts.strip("\\").split()
    # inputs = args.input.replace('"','').split()
    p.executable = w
    p.cmd = [w] + pargs
    # p.inputs = [inputs]

    multiprocesses, numThreads = (p, 1)
else:
    print("No workload specified. Exiting!\n", file=sys.stderr)
    sys.exit(1)

# (CPUClass, test_mem_mode, FutureClass) = Simulation.setCPUClass(args)
"""Returns two cpu classes and the initial mode of operation.

Restoring from a checkpoint or fast forwarding through a benchmark
can be done using one type of cpu, and then the actual
simulation can be carried out using another type. This function
returns these two types of cpus and the initial mode of operation
depending on the options provided.
"""
warn('Override "args.cpu_type" command line argument')
warn("OTHER CLI ARGUMENTS ARE BEING OVERRIDDEN!")
# args.cpu_type = "X86MinorCPUChipletized"
args.cpu_type = "X86O3CPUChipletized"
# args.sys_clock = "3.2GHz"
args.caches = True
args.l1i_cache = "16KB"
args.l1d_cache = "16KB"
args.mem_size = "16GB"
args.l2cache = True
args.l2_size = "8MB"
args.mem_size = "16GB"
# --l1d_size L1D_SIZE] [--l1i_size L1I_SIZE

if args.homogenousIEWDelays:
    args.iewToFetchDelay = args.commitToIEWDelay
    args.iewToDecodeDelay = args.commitToIEWDelay
    args.iewToRenameDelay = args.commitToIEWDelay
    args.commitToIEWDelay = args.commitToIEWDelay
    args.renameToIEWDelay = args.commitToIEWDelay
    args.iewToCommitDelay = args.commitToIEWDelay
    print("Homogenous IEW Delays set to: ", args.homogenousIEWDelays)

if args.homogenousRenameDelays:
    args.renameToDecodeDelay = args.homogenousRenameDelays
    args.renameToDecodeDelay = args.homogenousRenameDelays
    args.iewToRenameDelay = args.homogenousRenameDelays
    args.commitToRenameDelay = args.homogenousRenameDelays
    args.decodeToRenameDelay = args.homogenousRenameDelays
    args.renameToIEWDelay = args.homogenousRenameDelays
    args.renameToROBDelay = args.homogenousRenameDelays
    print("Homogenous Rename Delays set to: ", args.homogenousRenameDelays)

if args.homogenousFetchDelays:
    args.decodeToFetchDelay = args.homogenousFetchDelays
    args.renameToFetchDelay = args.homogenousFetchDelays
    args.iewToFetchDelay = args.homogenousFetchDelays
    args.commitToFetchDelay = args.homogenousFetchDelays
    args.fetchToDecodeDelay = args.homogenousFetchDelays
    print("Homogenous Fetch Delays set to: ", args.homogenousFetchDelays)

if args.homogenousDecodeDelays:
    args.decodeToFetchDelay = args.homogenousDecodeDelays
    args.renameToDecodeDelay = args.homogenousDecodeDelays
    args.iewToDecodeDelay = args.homogenousDecodeDelays
    args.commitToDecodeDelay = args.homogenousDecodeDelays
    args.fetchToDecodeDelay = args.homogenousDecodeDelays
    print("Homogenous Decode Delays set to: ", args.homogenousDecodeDelays)

if args.homogenousMainStageDelays:
    args.fetchToDecodeDelay = args.homogenousMainStageDelays
    args.decodeToRenameDelay = args.homogenousMainStageDelays
    args.renameToIEWDelay = args.homogenousMainStageDelays
    print("Main Pipeline Stage Delays set to: ", args.homogenousMainStageDelays)

# Handle time buffer sizes not being big enough
if any(int(args.forwardComSize) < delay for delay in \
        [int(args.fetchToDecodeDelay), int(args.decodeToRenameDelay), int(args.renameToIEWDelay)]):
    args.forwardComSize = str(max([int(args.fetchToDecodeDelay), int(args.decodeToRenameDelay), int(args.renameToIEWDelay)]))
    args.backComSize = str(max([int(args.fetchToDecodeDelay), int(args.decodeToRenameDelay), int(args.renameToIEWDelay)]))

TmpClass, test_mem_mode = getCPUClass(args.cpu_type)
CPUClass = None

if TmpClass.require_caches() and not args.caches and not args.ruby:
    fatal(f"{args.cpu_type} must be used with caches")

if args.checkpoint_restore != None:
    if args.restore_with_cpu != args.cpu_type:
        CPUClass = TmpClass
        TmpClass, test_mem_mode = getCPUClass(args.restore_with_cpu)

elif args.fast_forward:
    CPUClass = TmpClass
    CPUISA = ObjectList.cpu_list.get_isa(args.cpu_type)
    TmpClass = getCPUClass(
        CpuConfig.isa_string_map[CPUISA] + "AtomicSimpleCPU"
    )
    test_mem_mode = "atomic"

# Ruby only supports atomic accesses in noncaching mode
if test_mem_mode == "atomic" and args.ruby:
    warn("Memory mode will be changed to atomic_noncaching")
    test_mem_mode = "atomic_noncaching"

(CPUClass, test_mem_mode, FutureClass) = (TmpClass, test_mem_mode, CPUClass)

if type(CPUClass) == tuple:
    CPUClass = CPUClass[0]
CPUClass.numThreads = numThreads

# Check -- do not allow SMT with multiple CPUs
if args.smt and args.num_cpus > 1:
    fatal("You cannot use SMT with multiple CPUs!")

np = args.num_cpus

mp0_path = multiprocesses[0].executable
system = System(
    cpu=[CPUClass(cpu_id=i) for i in range(np)],
    mem_mode=test_mem_mode,
    mem_ranges=[AddrRange(args.mem_size)],
    cache_line_size=args.cacheline_size,
)

if numThreads > 1:
    system.multi_thread = True

# Create a top-level voltage domain
system.voltage_domain = VoltageDomain(voltage=args.sys_voltage)

# Create a source clock for the system and set the clock period
system.clk_domain = SrcClockDomain(
    clock=args.sys_clock, voltage_domain=system.voltage_domain
)

# Create a CPU voltage domain
system.cpu_voltage_domain = VoltageDomain()

# Create a separate clock domain for the CPUs
system.cpu_clk_domain = SrcClockDomain(
    clock=args.cpu_clock, voltage_domain=system.cpu_voltage_domain
)

# All cpus belong to a common cpu_clk_domain, therefore running at a common
# frequency.
for cpu in system.cpu:
    cpu.clk_domain = system.cpu_clk_domain

for i in range(np):
    if len(multiprocesses) == 1:
        system.cpu[i].workload = multiprocesses[0]
    else:
        system.cpu[i].workload = multiprocesses[i]

    system.cpu[i].createThreads()

MemClass = Simulation.setMemClass(args)
system.membus = SystemXBar()
system.system_port = system.membus.cpu_side_ports

system.mem_ctrl = MemCtrl()
system.mem_ctrl.dram = DDR4_2400_16x4()
system.mem_ctrl.dram.range = system.mem_ranges[0]
system.mem_ctrl.port = system.membus.mem_side_ports

##### CACHE SETUP #####
# build the cache. instead of executing the config_cache(), we will
# just do our own version copied from there without the bloat
# CacheConfig.config_cache(args, system)
dcache_class, icache_class, l2_cache_class, walk_cache_class = (
    L1_DCache,
    L1_ICache,
    L2Cache,
    None,
)
if args.l2cache:
    system.l2 = l2_cache_class(
        clk_domain=system.cpu_clk_domain, **_get_cache_opts("l2", args)
    )
    system.tol2bus = L2XBar(clk_domain=system.cpu_clk_domain)
    system.l2.cpu_side = system.tol2bus.mem_side_ports
    system.l2.mem_side = system.membus.cpu_side_ports

# Set the cache line size of the system
system.cache_line_size = args.cacheline_size
for i in range(args.num_cpus):
    if args.caches:
        icache = icache_class(**_get_cache_opts("l1i", args))
        dcache = dcache_class(**_get_cache_opts("l1d", args))

        # If we are using ISA.X86 or ISA.RISCV, we set walker caches.
        if ObjectList.cpu_list.get_isa(args.cpu_type) in [
            ISA.RISCV,
            ISA.X86,
        ]:
            iwalkcache = PageTableWalkerCache()
            dwalkcache = PageTableWalkerCache()
        else:
            iwalkcache = None
            dwalkcache = None

        # When connecting the caches, the clock is also inherited
        # from the CPU in question
        system.cpu[i].addPrivateSplitL1Caches(
            icache, dcache, iwalkcache, dwalkcache
        )

    system.cpu[i].createInterruptController()
    if args.l2cache:
        system.cpu[i].connectAllPorts(
            system.tol2bus.cpu_side_ports,
            system.membus.cpu_side_ports,
            system.membus.mem_side_ports,
        )
    else:
        system.cpu[i].connectBus(system.membus)

# we don't need to copy this function, just leave it there.
config_filesystem(system, args)

system.workload = SEWorkload.init_compatible(mp0_path)

if args.wait_gdb:
    system.workload.wait_for_remote_gdb = True

root = Root(full_system=False, system=system)

Simulation.run(args, root, system, FutureClass)
