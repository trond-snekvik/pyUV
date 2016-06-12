import subprocess
from threading import Thread
import sys
import os



def nrfjprog(args):
    process = subprocess.Popen("nrfjprog "+args, stdout=subprocess.PIPE, stderr = subprocess.STDOUT)
    out, _ = process.communicate()
    if process == None or process.returncode != 0:
        print "Error calling nrfjprog with arguments " + args + "."
        print out
        exit(2)
    return out

def getDevices(beginsWith=None):
    devs = [dev for dev in nrfjprog("-i").splitlines() if not dev == ""]
    if not beginsWith is None:
        devs = [dev for dev in devs if dev.startswith(beginsWith)]
    return devs

def progDev(device, hexfile, erase=False, reset=True):
    if device is None:
        snrArg = ""
    else:
        snrArg = "-s " + device + " "
    #program
    if erase:
        out = nrfjprog(snrArg + "--program " + hexfile + " --chiperase")
    else:
        out = nrfjprog(snrArg + "--program " + hexfile + " --sectorerase")
    if "WARNING: A UICR write operation has been requested but UICR has not been" in out:
        sys.stdout.write("UICR->BOOTLOADERADDR: 0x" + nrfjprog(snrArg + "--memrd 0x10001014").split()[1].strip() + "\n")
    elif len(out) > 0:
        out = [device + ": " + line for line in out.splitlines()]
        sys.stdout.write(device + ": " + out)

    if reset:
        nrfjprog(snrArg + "-r")


def program(hexfile, devfilter=None, erase=False, reset=True):
    devices = getDevices(devfilter)
    threads = []
    for dev in devices:
        if not dev is None:
            print "Programming device " + dev
        thread = Thread(target = progDev, args = (dev, hexfile, erase, reset))
        thread.start()
        threads.append(thread)

    for thread in threads:
        thread.join()

if __name__ == "__main__":
    def printUsage():
        print "Usage: nrfmultiprog.py hexfile [-s <snr> | --select] [--sdapp][--erase|-e][--halt]"
        print "\t-s \"snr\"\tOnly program devices that fit the serial number snr. \n\t\t\tsnr may be any number of digits, and is matched from the beginning of the Serial number"
        print "\t--select\t\tSelect the device from the standard JLink prompt."
        print "\t--sdapp\t\tProgram relies on Softdevice, don't erase it. REDUNDANT."
        print "\t--erase, -e\tErase all firmware before programming."
        print "\t--halt\t\tDon't start execution."
    select = False
    snrFilter = None
    hasSD = False
    erase = False
    reset = True
    hexfile = sys.argv[1]
    for arg in sys.argv:
        arg = arg.lower()
    #check args
    if len(sys.argv) < 2:
        printUsage()
        exit(160) #bad arguments
    if "--help" in sys.argv or "-h" in sys.argv:
        printUsage()
        exit(0)
    if "-s" in sys.argv:
        snrIndex = sys.argv.index("-s") + 1
        if len(sys.argv) <= snrIndex:
            printUsage()
            exit(160) #bad arguments
        snrFilter = sys.argv[snrIndex]
    elif "--select" in sys.argv:
        select = True
    if "--erase" in sys.argv or "-e" in sys.argv:
        erase = True
    if "--halt" in sys.argv:
        reset = False

    program(hexfile, erase, reset)
    print "Done."




