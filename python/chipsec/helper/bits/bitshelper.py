#!/usr/bin/python
##
## CHIPSEC: Platform Security Assessment Framework
##
## Copyright (C) 2018 3mdeb Embedded Systems Consulting
##
## This program is free software; you can redistribute it and/or modify
## it under the terms of the GNU General Public License as published by
## the Free Software Foundation; version 2 of the License.
##
## This program is distributed in the hope that it will be useful,
## but WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
## GNU General Public License for more details.
##


# -------------------------------------------------------------------------------
#
# CHIPSEC: Platform Hardware Security Assessment Framework
#
# -------------------------------------------------------------------------------

import struct
import sys
import bits

import chipsec.defines
from chipsec.logger import logger
from chipsec.helper.oshelper import Helper, get_tools_path, UnimplementedAPIError, UnimplementedNativeAPIError

class BitsHelperError (RuntimeError):
    pass

class BitsHelper(Helper):

    def __init__(self):
        super(BitsHelper, self).__init__()
        if sys.platform.startswith('EFI'):
            self.os_system = sys.platform
            self.os_release = "0.0"
            self.os_version = "0.0"
            self.os_machine = "i386"
        else:
            import platform
            self.os_system  = platform.system()
            self.os_release = platform.release()
            self.os_version = platform.version()
            self.os_machine = platform.machine()
            self.os_uname   = platform.uname()

    def __del__(self):
        try:
            destroy()
        except NameError:
            pass

###############################################################################################
# Driver/service management functions
###############################################################################################

    def create(self, start_driver):
        if logger().VERBOSE:
            logger().log("[helper] BITS Helper created")
        return True

    def start(self, start_driver, driver_exists=False):
        # The driver is not needed.
        # It is always considered as loaded.
        self.driver_loaded = True
        if logger().VERBOSE:
            logger().log("[helper] BITS Helper started/loaded")
        return True

    def stop(self, start_driver):
        if logger().VERBOSE:
            logger().log("[helper] BITS Helper stopped/unloaded")
        return True

    def delete(self, start_driver):
        if logger().VERBOSE:
            logger().log("[helper] BITS Helper deleted")
        return True


###############################################################################################
# Actual API functions to access HW resources
###############################################################################################

    #
    # Physical memory access
    #

    def read_phys_mem( self, phys_address_hi, phys_address_lo, length ):
        return bits.memory( (phys_address_hi << 32) | phys_address_lo, length )

    def write_phys_mem( self, phys_address_hi, phys_address_lo, length, buf ):
        logger().log( '[bits] write_phys_mem' )
        raise NotImplementedError()
        if (buf != None):
            mem = bits.memory( (phys_address_hi << 32) | phys_address_lo, length )
            mem = buf

    def _write_phys_mem( self, phys_address, length, buf ):
        raise NotImplementedError()
        # temp hack
        if 4 == length:
            dword_value = struct.unpack( 'I', buf )[0]
            edk2.writemem_dword( phys_address, dword_value )
        else:
            edk2.writemem( phys_address, buf, length )

    def alloc_phys_mem( self, length, max_pa ):
        raise NotImplementedError()
        # temporary WA using malloc
        va = edk2.allocphysmem(length, max_pa)[0]
        pa = self.va2pa(va)
        return (va, pa)

    def va2pa( self, va ):
        pa = va # UEFI shell has identity mapping
        if logger().VERBOSE: logger().log( "[helper] VA (0X%016x) -> PA (0X%016x)" % (va,pa) )
        return pa

    def pa2va(self, pa):
        va = pa # UEFI Shell has identity mapping
        if logger().VERBOSE:
            logger().log('[helper] PA (0X%016x) -> VA (0X%016x)' % (pa, va))
        return va


    #
    # Memory-mapped I/O (MMIO) access
    #

    def map_io_space(self, physical_address, length, cache_type):
        return self.pa2va(physical_address)

    def read_mmio_reg(self, phys_address, size):
        out_buf = self.read_phys_mem( 0, phys_address, size )
        if size == 4:
            value = struct.unpack( '=I', out_buf[:size] )[0]
        elif size == 2:
            value = struct.unpack( '=H', out_buf[:size] )[0]
        elif size == 1:
            value = struct.unpack( '=B', out_buf[:size] )[0]
        else: value = 0
        return value

    def write_mmio_reg(self, phys_address, size, value):
        logger().log( '[bits] write_mmio_reg' )
        buf = struct.pack(size*"B", value)
        self.write_phys_mem( 0, phys_address, size, buf )

    #
    # PCIe configuration access
    #

    def read_pci_reg( self, bus, device, function, address, size ):
        if   (1 == size):
            return ( bits.pci_read( bus, device, function, address, size ) & 0xFF )
        elif (2 == size):
            return ( bits.pci_read( bus, device, function, address, size ) & 0xFFFF )
        else:
            return bits.pci_read( bus, device, function, address, size )

    def write_pci_reg( self, bus, device, function, address, value, size ):
        return bits.pci_write( bus, device, function, address, value, size )

    #
    # CPU I/O port access
    #

    def read_io_port( self, io_port, size ):
        if   (1 == size):
            return ( bits.inb( io_port ) & 0xFF )
        elif (2 == size):
            return ( bits.inw( io_port ) & 0xFFFF )
        else:
            return bits.inl( io_port )

    def write_io_port( self, io_port, value, size ):
        if   (1 == size):
            return bits.outb( io_port, value )
        elif (2 == size):
            return bits.outw( io_port, value )
        else:
            return bits.outl( io_port, value )

    #
    # SMI events
    #

    def send_sw_smi( self, cpu_thread_id, SMI_code_data, _rax, _rbx, _rcx, _rdx, _rsi, _rdi ):
        raise NotImplementedError()
        return edk2.swsmi(SMI_code_data, _rax, _rbx, _rcx, _rdx, _rsi, _rdi)

    #
    # CPU related API
    #

    def read_msr( self, cpu_thread_id, msr_addr ):
        return bits.rdmsr( cpu_thread_id, msr_addr ) #TODO: check it
        #(eax, edx) = edk2.rdmsr( msr_addr )
        #eax = eax % 2**32
        #edx = edx % 2**32
        #return ( eax, edx )

    def write_msr( self, cpu_thread_id, msr_addr, eax, edx ):
        return bits.wrmsr( cpu_thread_id, msr_addr, ( edx << 32 ) | eax )
        #edk2.wrmsr( msr_addr, eax, edx )

    def read_cr(self, cpu_thread_id, cr_number):
        return 0

    def write_cr(self, cpu_thread_id, cr_number, value):
        return False

    def load_ucode_update( self, cpu_thread_id, ucode_update_buf ):
        logger().error( "[efi] load_ucode_update is not supported yet" )
        return 0

    def get_threads_count ( self ):
        logger().log_warning( "EFI helper hasn't implemented get_threads_count yet" )
        #print "OsHelper for %s does not support get_threads_count from OS API"%self.os_system.lower()
        return 0
        
    def cpuid(self, eax, ecx):
        (reax, rebx, recx, redx) = bits.cpuid(bits.bsp_apicid(), eax, ecx)
        return (reax, rebx, recx, redx)

    def get_descriptor_table( self, cpu_thread_id, desc_table_code ):
        logger().log_warning("EFI helper has not implemented get_descriptor_table yet")
        return 0

    #
    # File system
    #

    def getcwd( self ):
        return os.getcwd()


    #
    # EFI Variable API
    #

    def EFI_supported( self ):
        return False # Is this enough to not use the rest of EFI functions?

    def get_EFI_variable_full(self, name, guidstr):
        guid = uuid.UUID(guidstr)
        
        size = 100
        (Status, Attributes, newdata, DataSize) = edk2.GetVariable(unicode(name), guid.bytes, size)
        
        if Status == 5:
            size = DataSize+1
            (Status, Attributes, newdata, DataSize) = edk2.GetVariable(unicode(name), guid.bytes, size) 
        
        return (Status, newdata, Attributes)
        

    def get_EFI_variable(self, name, guidstr):
        (status, data, attrs) = self.get_EFI_variable_full(name, guidstr)
        return data
        
    def set_EFI_variable(self, name, guidstr, data, datasize=None, attrs=0x7):
        
        guid = uuid.UUID(guidstr)
        
        if data     is None: data = '\0'*4
        if datasize is None: datasize = len(data)

        (Status, datasize, guidbytes) = edk2.SetVariable(unicode(name), guid.bytes, int(attrs), data, datasize)
        
        return Status
        
    def delete_EFI_variable(self, name, guid):
        return self.set_EFI_variable(name, guid, None, 0)
    
    def list_EFI_variables(self):   
                
        off = 0
        buf = list()
        hdr = 0
        attr = 0
        variables = dict()

        status_dict = { 0:"EFI_SUCCESS", 1:"EFI_LOAD_ERROR", 2:"EFI_INVALID_PARAMETER", 3:"EFI_UNSUPPORTED", 4:"EFI_BAD_BUFFER_SIZE", 5:"EFI_BUFFER_TOO_SMALL", 6:"EFI_NOT_READY", 7:"EFI_DEVICE_ERROR", 8:"EFI_WRITE_PROTECTED", 9:"EFI_OUT_OF_RESOURCES", 14:"EFI_NOT_FOUND", 26:"EFI_SECURITY_VIOLATION" }
        
        name = '\0'*200
        
        randguid = uuid.uuid4()
        
        (status, name, size, guidbytes) = edk2.GetNextVariableName(200, unicode(name), randguid.bytes)     
        
        if status == 5:
            if logger().VERBOSE: logger().log("size was too small increasing to %d" % size)
            name = '\0'*size
            (status, name, size, guidbytes) = edk2.GetNextVariableName(size, unicode(name), randguid.bytes)

        
#        while status != 14:
        while status == 0:
            guid =  uuid.UUID(bytes=guidbytes)  
            name = name.encode('ascii','ignore')
            (status, data, attr) = self.get_EFI_variable_full(name, guid.hex)
            
            if logger().VERBOSE: logger().log("%d: Found variable %s" % (len(variables), name))

            var = (off, buf, hdr, data, guid, attr)
            if name in variables: 
                if logger().VERBOSE: logger().log("WARNING: found a second instance of name %s." % name)

            else: variables[name] = []
            if data != "" or guid != 0 or attr != 0:
                variables[name].append(var)

            (status, name, size, guidbytes) = edk2.GetNextVariableName(200, unicode(name), guid.bytes)
            if logger().VERBOSE: logger().log("returned %s. status is %s" % (name, status_dict[status]))

            if status == 5:
                if logger().VERBOSE: logger().log("size was too small increasing to %d" % size)
                (status, name, size, guidbytes) = edk2.GetNextVariableName(size, unicode(name), guid.bytes)
        return variables        
        
    #
    # ACPI tables access
    #

    def get_ACPI_SDT( self ):
        logger().error( "[efi] ACPI is not supported yet" )
        return 0        

    #
    # IOSF Message Bus access
    #

    def msgbus_send_read_message( self, mcr, mcrx ):
        logger().error( "[efi] Message Bus is not supported yet" )
        return None        

    def msgbus_send_write_message( self, mcr, mcrx, mdr ):
        logger().error( "[efi] Message Bus is not supported yet" )
        return None        

    def msgbus_send_message( self, mcr, mcrx, mdr=None ):
        logger().error( "[efi] Message Bus is not supported yet" )
        return None        
    
        
def get_helper():
    return EfiHelper( )
