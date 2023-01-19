# nrf24lu1p-512-bootloader

## Description

USB bootloader for nrf24lu1+.  Uses the same protocol given in the
NRF24LU1+ datasheet, except this version fits in 512 bytes.
Size of generated binary file can be adjusted via FLASH_SIZE_16 in main.S. flash.py can also be used to flash any other binary via USB.

To flash bootloader:

    make
    sudo ./flash.py ./bootloader.bin 16
16 will need to be changed to 32 if flashing the 32kb binary
## License

License under the MIT software license.
