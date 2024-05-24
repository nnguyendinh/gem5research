
""" This file creates a barebones system and executes 'hello', a simple Hello
World application. We add a configurable latency between the decode and execute
stages of the CPU. This is to simulate the latency of a chiplet link between the
CPU and the memory controller.

This config file assumes that the x86 ISA was built.

Author: Nathan Nguyendinh
"""

# import the m5 (gem5) library created when gem5 is built
import m5
import argparse

from m5.defines import buildEnv
from m5.objects import *
from m5.params import NULL
from m5.util import (
    addToPath,
    fatal,
    warn,
)

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

parser = argparse.ArgumentParser()

parser.add_argument(
    "--dtoe_delay", 
    help="How many cycles of delay between Decode and Execute stages", 
    default=1,
)

parser.add_argument(
    "--binary",
    help="binary to run",
    default="tests/test-progs/hello/bin/x86/linux/hello",
)

parser.add_argument(
    "--cmd",
    help="idk",
    # default="tests/test-progs/hello/bin/x86/linux/hello",
)

# --cmd already derrived from other args
parser.add_argument(
    "--opts",
    help="options for the command",
)



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

# create the system we are going to simulate
system = System()

# Set the clock frequency of the system (and all of its children)
system.clk_domain = SrcClockDomain()
system.clk_domain.clock = "1GHz"
system.clk_domain.voltage_domain = VoltageDomain()

# Set up the system
system.mem_mode = "timing"  # Use timing accesses
system.mem_ranges = [AddrRange("512MB")]  # Create an address range

# Create a simple CPU
# You can use ISA-specific CPU models for different workloads:
# `RiscvTimingSimpleCPU`, `ArmTimingSimpleCPU`.
system.cpu = X86MinorCPUChipletized(decode_to_execute_forward_delay=1)

# Create a memory bus, a system crossbar, in this case
system.membus = SystemXBar()

# Hook the CPU ports up to the membus
system.cpu.icache_port = system.membus.cpu_side_ports
system.cpu.dcache_port = system.membus.cpu_side_ports

# create the interrupt controller for the CPU and connect to the membus
system.cpu.createInterruptController()

# For X86 only we make sure the interrupts care connect to memory.
# Note: these are directly connected to the memory bus and are not cached.
# For other ISA you should remove the following three lines.
system.cpu.interrupts[0].pio = system.membus.mem_side_ports
system.cpu.interrupts[0].int_requestor = system.membus.cpu_side_ports
system.cpu.interrupts[0].int_responder = system.membus.mem_side_ports

# Create a DDR3 memory controller and connect it to the membus
system.mem_ctrl = MemCtrl()
system.mem_ctrl.dram = DDR3_1600_8x8()
system.mem_ctrl.dram.range = system.mem_ranges[0]
system.mem_ctrl.port = system.membus.mem_side_ports

# Connect the system up to the membus
system.system_port = system.membus.cpu_side_ports

# Here we set the X86 "hello world" binary. With other ISAs you must specify
# workloads compiled to those ISAs. Other "hello world" binaries for other ISAs
# can be found in "tests/test-progs/hello".
# thispath = os.path.dirname(os.path.realpath(__file__))
# binary = os.path.join(
#     thispath,
#     "../../",
#     "tests/test-progs/hello/bin/x86/linux/hello",
# )

binpath = args.binary

system.workload = SEWorkload.init_compatible(binary)

# Create a process for a simple "Hello World" application
process = Process()
# Set the command
# cmd is a list which begins with the executable (like argv)
process.cmd = [binpath]
# Set the cpu to use the process as its workload and create thread contexts
system.cpu.workload = process
system.cpu.createThreads()

# set up the root SimObject and start the simulation
root = Root(full_system=False, system=system)
# instantiate all of the objects we've created above
m5.instantiate()

print(f"Beginning simulation!")
exit_event = m5.simulate()
print(f"Exiting @ tick {m5.curTick()} because {exit_event.getCause()}")
