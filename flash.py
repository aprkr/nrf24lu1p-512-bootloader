#!/bin/env python
import usb.core
import usb.util
import sys

USB_TIMEOUT = 1000

# USB Commands
CMD_VERSION        = 0x01
CMD_WRITE_INIT     = 0x02
CMD_READ_FLASH     = 0x03
CMD_ERASE_PAGE     = 0x04
CMD_READ_DISABLE   = 0x05
CMD_SELECT_FLASH_HALF   = 0x06
CMD_RESET          = 0x07

IN_ENDPOINT_ADDR = 0x81
OUT_ENDPOINT_ADDR = 0x01
BLOCKS_PER_16K = 256 # 16kb / 64 byte blocks
FLASH_BLOCK_SIZE = 64
PAGE_SIZE = 512

dev = usb.core.find(idVendor=0x1915, idProduct=0x0101)
if not dev:
    print("Bootloader device not found")
    quit()
intf_num = dev[0].interfaces()[0].iInterface
if dev.is_kernel_driver_active(intf_num):
    dev.detach_kernel_driver(intf_num)

def sendCommand(command, arg=None):
    cmd = bytes([command])
    if arg != None:
        cmd = bytes([command, arg])
    dev.write(CMD_VERSION, cmd)

def readResponse():
    return bytes(dev.read(IN_ENDPOINT_ADDR, 64, USB_TIMEOUT))

def getFirmwareVersion():
    sendCommand(CMD_VERSION)
    return readResponse()[0:2]

def readFlash(kb=16):
    flash = bytes()
    sendCommand(CMD_SELECT_FLASH_HALF, 0)
    readResponse()
    for x in range(BLOCKS_PER_16K):
        sendCommand(CMD_READ_FLASH, x)
        flash += readResponse()
    if kb == 32:
        sendCommand(CMD_SELECT_FLASH_HALF, 1)
        readResponse()
        for x in range(BLOCKS_PER_16K):
            sendCommand(CMD_READ_FLASH, x)
            flash += readResponse()
    return flash

def writeFlash(code, kb):
    numPages = int(kb * 1024 / PAGE_SIZE)
    for pageNum in range(numPages):
        page = code[pageNum*PAGE_SIZE:(pageNum+1)*PAGE_SIZE]
        if page.count(0xFF) == PAGE_SIZE:
            continue
        sendCommand(CMD_WRITE_INIT, pageNum)
        readResponse()
        for blockNum in range(int(PAGE_SIZE / FLASH_BLOCK_SIZE)):
            dev.write(OUT_ENDPOINT_ADDR, page[blockNum*FLASH_BLOCK_SIZE:(blockNum+1)*FLASH_BLOCK_SIZE])
            readResponse()
    flash = readFlash(kb)
    for pageNum in range(numPages):
        page = code[pageNum*PAGE_SIZE:(pageNum+1)*PAGE_SIZE]
        if page.count(0xFF) == PAGE_SIZE:
            continue
        if page != flash[pageNum*PAGE_SIZE:(pageNum+1)*PAGE_SIZE]:
            print("Data mismatch at page: " + str(pageNum))
            print(page.hex())
            print(flash[pageNum*PAGE_SIZE:(pageNum+1)*PAGE_SIZE].hex())
    print("Flash successful")
    try: dev.reset()
    except: pass

try:     
    version = getFirmwareVersion()
    print("Bootloader Version: " + str(version[0]) + "." + str(version[1]))
except:
    pass

# Verify that we received a command line argument
if len(sys.argv) < 3:
  print('Usage: ./flash.py path-to-firmware.bin kb')
  quit()

# # Read in the firmware
with open(sys.argv[1], 'rb') as f:
  data = f.read()
# Zero pad the data to a multiple of 512 bytes
if len(data) % PAGE_SIZE > 0: data += b'\xFF' * (PAGE_SIZE - len(data) % PAGE_SIZE)
kb = int(len(data) / 1024)
if (kb != 16 & kb != 32):
    print("Flash file isn't 16 or 32 kb")
    quit()
if (kb != int(sys.argv[2])):
    print("Flash file size does not match kb given on command line")
    quit()

writeFlash(data, kb)
