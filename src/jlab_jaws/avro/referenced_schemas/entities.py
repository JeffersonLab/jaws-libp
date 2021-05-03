from enum import Enum


class AlarmClass(Enum):
    Base_Class = 1
    BCM_Temperature = 2
    Trim_Temperature = 3
    Shunt_Temperature = 4
    CAMAC_Temperature = 5
    CAMAC_Voltage = 6
    MPS_Voltage_Mismatch = 7
    MPS_Voltage_Fault = 8
    MPS_Setpoint_Invalid = 9
    Magnet_Mismatch = 10
    Magnet_Communication_Error = 11
    Vacuum_Level = 12
    LCW_Supply_Pressure = 13


class AlarmLocation(Enum):
    S1D = 1
    S2D = 2
    S3D = 3
    S4D = 4
    S5D = 5
    L1 = 6
    L2 = 7
    L3 = 8
    L4 = 9
    L5 = 10
    L6 = 11
    L7 = 12
    L8 = 13
    L9 = 14
    LA = 15
    LB = 16
    A1 = 17
    A2 = 18
    A3 = 19
    A4 = 20
    A5 = 21
    A6 = 22
    A7 = 23
    A8 = 24
    A9 = 25
    AA = 26
    BSY2 = 27
    BSY4 = 28
    BSY6 = 29
    BSY8 = 30
    BSYA = 31
    BSYD = 32
    INJ = 33
    NL = 34
    SL = 35
    EA = 36
    WA = 37
    BSY = 38
    HA = 39
    HB = 40
    HC = 41
    HD = 42
    ACC = 43
    CHL = 44
    MCC = 45
    LERF = 46
    UITF = 47


class AlarmCategory(Enum):
    Aperture = 1
    BCM = 2
    Box = 3
    BPM = 4
    CAMAC = 5
    Crate = 6
    Dump = 7
    Gun = 8
    Harp = 9
    Helicity = 10
    IC = 11
    IOC = 12
    Laser = 13
    LCW = 14
    Misc = 15
    ODH = 16
    RADCON = 17
    RF = 18
    Vacuum = 19


class AlarmPriority(Enum):
    P1_CRITICAL = 1
    P2_MAJOR = 2
    P3_MINOR = 3
    P4_INCIDENTAL = 4
