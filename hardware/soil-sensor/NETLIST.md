# Soil sensor netlist

Generated from `gen/netlist.py`. Do not edit by hand.

- `3V3`: U_LDO.5, C_LDOOUT.1, C_BULK.1, C_MCU1.1, C_MCU2.1, U_MCU.2, R_EN.2, R_BOOT.2, R_IO8.2, U_RH.1, R_SDA.2, R_SCL.2, C_RH.1
- `BAT_ADC`: U_MCU.26, R_BAT1.2, R_BAT2.1, C_BATADC.1
- `BOOT`: U_MCU.15, R_BOOT.1
- `CC1`: J_USB.A5, R_CC1.1
- `CC2`: J_USB.B5, R_CC2.1
- `CHRG_N`: U_CHG.7, LED_CHG.1
- `EN`: U_MCU.3, R_EN.1, C_EN.1
- `GND`: J_USB.A1, J_USB.A12, J_USB.B1, J_USB.B12, J_USB.SH, R_CC1.2, R_CC2.2, U_CHG.1, U_CHG.3, U_CHG.9, R_PROG.2, C_VBUS.2, C_VBAT.2, U_PROT.4, U_PROT.5, R_QG.2, U_LDO.2, C_LDOIN.2, C_LDOOUT.2, C_BULK.2, C_MCU1.2, C_MCU2.2, U_MCU.1, U_MCU.28, U_MCU.29, U_MCU.30, U_MCU.31, U_MCU.32, U_MCU.33, U_MCU.34, U_MCU.35, U_MCU.36, U_MCU.37, C_EN.2, U_RH.4, U_RH.5, C_RH.2, R_BAT2.2, C_BATADC.2, C_SOIL.2, R_SOIL.2
- `IO8`: U_MCU.10, R_IO8.1
- `LED_A`: LED_CHG.2, R_LED.1
- `PROBE_DRV`: U_MCU.17, R_DRV.1
- `PROBE_EL`: R_DRV.2, D_PROBE.2
- `PROG`: U_CHG.2, R_PROG.1
- `PROT_VDD`: U_PROT.3, R_PROT.2, C_PROT.1
- `QG`: Q_REV.1, R_QG.1
- `SCL`: U_MCU.21, U_RH.2, R_SCL.1
- `SDA`: U_MCU.20, U_RH.3, R_SDA.1
- `SOIL_ADC`: U_MCU.27, D_PROBE.1, C_SOIL.1, R_SOIL.1
- `USB_DN`: J_USB.A7, J_USB.B7, U_MCU.13
- `USB_DP`: J_USB.A6, J_USB.B6, U_MCU.14
- `VBAT`: U_CHG.5, C_VBAT.1, Q_REV.2, U_LDO.1, U_LDO.3, C_LDOIN.1, R_BAT1.1
- `VBUS`: J_USB.A4, J_USB.A9, J_USB.B4, J_USB.B9, U_CHG.4, U_CHG.8, R_LED.2, C_VBUS.1
- `VCELL_N`: BT1.1, U_PROT.2, C_PROT.2
- `VCELL_P`: BT1.2, R_PROT.1, Q_REV.3

## Not connected

- J_USB.A8
- J_USB.B8
- U_CHG.6
- U_LDO.4
- U_MCU.11
- U_MCU.12
- U_MCU.16
- U_MCU.18
- U_MCU.19
- U_MCU.22
- U_MCU.23
- U_MCU.24
- U_MCU.25
- U_MCU.4
- U_MCU.5
- U_MCU.6
- U_MCU.7
- U_MCU.8
- U_MCU.9
- U_PROT.1

## Parts

| Ref | Value | LCSC | JLC tier |
|---|---|---|---|
| U_MCU | ESP32-C6-WROOM-1-N8 | C5366877 | extended |
| U_LDO | XC6220B331MR | C3040644 | extended |
| J_USB | TYPE-C-31-M-12 | C165948 | extended |
| U_RH | SHTC3 | C194656 | extended |
| BT1 | BH-18650-B1BA002 | C2988620 | extended |
| U_PROT | XB5353A | C80628 | extended |
| U_CHG | TP4056 | C16581 | preferred |
| Q_REV | AO3401A | C15127 | basic |
| D_PROBE | 1N4148WS | C2128 | basic |
| LED_CHG | Red | C2286 | basic |
| R_CC1 | 5.1k | C25905 | basic |
| R_CC2 | 5.1k | C25905 | basic |
| R_PROG | 2.4k | C25882 | preferred |
| R_LED | 1k | C11702 | basic |
| C_VBUS | 10uF | C15850 | basic |
| C_VBAT | 10uF | C15850 | basic |
| R_PROT | 100R | C25076 | basic |
| C_PROT | 100nF | C1525 | basic |
| R_QG | 100k | C25741 | basic |
| C_LDOIN | 1uF | C52923 | basic |
| C_LDOOUT | 1uF | C52923 | basic |
| C_BULK | 22uF | C45783 | basic |
| C_MCU1 | 10uF | C15850 | basic |
| C_MCU2 | 100nF | C1525 | basic |
| R_EN | 10k | C25744 | basic |
| C_EN | 1uF | C52923 | basic |
| R_BOOT | 10k | C25744 | basic |
| R_IO8 | 10k | C25744 | basic |
| R_SDA | 10k | C25744 | basic |
| R_SCL | 10k | C25744 | basic |
| C_RH | 100nF | C1525 | basic |
| R_BAT1 | 1M | C26083 | basic |
| R_BAT2 | 1M | C26083 | basic |
| C_BATADC | 100nF | C1525 | basic |
| R_DRV | 1k | C11702 | basic |
| R_SOIL | 1M | C26083 | basic |
| C_SOIL | 100nF | C1525 | basic |
